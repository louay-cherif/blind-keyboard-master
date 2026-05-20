# Blind Keyboard Master - keyboard learning app accessible for visually impaired people
# Copyright (C) 2026 Louay Cherif
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import random
import time
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QLabel, QDialog, QTextBrowser)
from PyQt5.QtCore import Qt, QTimer
from weeks import sentences_en, sentences_fr
from static.accessible_widgets import AccessiblePushButton, AccessibleLabel, AccessibleBrowser


# Create aliases for backward compatibility
SentenceAccessibleLabel = AccessibleLabel
SentenceAccessibleBrowser = AccessibleBrowser


class SentenceTypingInput(QLineEdit):
    def __init__(self, mode, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = mode
        self._last_was_space = False  # optional, not strictly needed

    def keyPressEvent(self, event):
        # Ctrl alone: repeat current word
        if event.key() == Qt.Key_Control and event.modifiers() == Qt.ControlModifier:
            self.mode.repeat_current_word()
            return

        # Shift+Ctrl: announce status
        if (event.key() == Qt.Key_Control and event.modifiers() & Qt.ShiftModifier):
            self.mode._announce_status()
            return

        # Shift+Enter: exit confirmation
        if (event.key() in (Qt.Key_Return, Qt.Key_Enter) and event.modifiers() & Qt.ShiftModifier):
            self.mode._on_shift_enter()
            return

        # Ctrl+number: repeat specific word
        if event.modifiers() & Qt.ControlModifier:
            text = event.text()
            if text.isdigit():
                index = int(text) - 1
                self.mode.repeat_word_index(index)
                return

        # Enter: submit sentence
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.mode.submit_sentence()
            return

        # Space: only advance if not at last word, and prevent double spaces
        if event.key() == Qt.Key_Space:
            # Prevent double spaces
            if self.text().endswith(' '):
                # ignore second space
                return
            # If at last word, announce and do NOT insert space
            if self.mode.current_word_index >= len(self.mode.words) - 1:
                if self.mode.base_logic.speaker:
                    msg = ("No more words, please press enter."
                           if self.mode.is_english else
                           "Plus de mots, veuillez appuyer sur Entrée.")
                    self.mode.base_logic.speaker.output(msg)
                return  # do not insert space
            # Normal case: advance word and insert space
            self.mode.advance_word()
            super().keyPressEvent(event)
            return

        # Backspace: handle spaces carefully
        if event.key() == Qt.Key_Backspace:
            text = self.text()
            cursor = self.cursorPosition()
            # If there is a character to delete
            if cursor > 0:
                char_to_delete = text[cursor-1]
                if char_to_delete == ' ':
                    # Deleting a space: only move back if there is a word before the current one
                    # and the space is not trailing after the last word? Actually we need to know if there is a next word.
                    # Condition: move back only if the current word index is not zero AND the space is not after the last word?
                    # Simpler: if the current word index is not the last word (i.e., there is a next word), then moving back means
                    # we want to go to the previous word. But if we are at the last word and deleting a trailing space,
                    # we should not move back.
                    # However, note that when we are at the last word, the word index is len(words)-1.
                    # The only time we have a space after the last word is when user typed a space after the last word,
                    # but that is prevented by the space handling above. So if we are here, the space must be between words.
                    # Therefore, we can always move back when deleting a space? Wait, the user reported moving back at the end.
                    # Let's refine: We only move back if the space is not the last character and there is a word after.
                    # Actually, easier: if after deleting the space, the cursor position would be at the end of the previous word,
                    # then we should move back. But our current implementation uses a separate move_word_back().
                    # To avoid confusion, we only move back if the current word index is greater than 0 AND the space is not at the very end of the text (meaning it is between words).
                    # But the user might delete a space that is between words, then we should move back.
                    # I'll implement: if the current word index is not 0, then moving back is allowed. But what about trailing spaces? They are prevented by space handler.
                    # So safe: always move back when deleting a space? No, because the user could have pressed space after last word before we fixed it? But we fixed it.
                    # Given the user wants: "when the user presses space in the end of the phrase where no words are left it's announced then space removed"
                    # Since we already prevent inserting that space, there will be no trailing space. So backspace on space only occurs between words.
                    # Therefore, we can unconditionally move back on space deletion.
                    if self.mode.current_word_index > 0:
                        self.mode.move_word_back()
            super().keyPressEvent(event)
            return

        # Any other key: interrupt pending announcements
        if self.mode.has_pending_announcements():
            self.mode.stop_pending_announcements()

        super().keyPressEvent(event)

class SentenceMode(QWidget):
    def __init__(self, base_logic, is_english=True, parent=None):
        super().__init__(None)
        self.setWindowFlag(Qt.Window, True)
        self.base_logic = base_logic
        self.is_english = is_english
        self.parent_challenge = parent
        self.sentence_count_required = 12
        self.session_sentences = []
        self.current_sentence_index = 0
        self.current_sentence = ""
        self.words = []
        self.current_word_index = 0
        self.sentence_results = []
        self.pending_timers = []
        self.total_xp_earned = 0
        self.total_boss_damage = 0
        self.passed = False
        self.session_finished = False          # new flag to prevent exit dialog on normal close
        self._announcement_paused = False
        self._closing = False

        self._setup_ui()

    # ----------------------------------------------------------------------
    # UI setup
    # ----------------------------------------------------------------------

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(18)

        title_text = "Sentence Mode" if self.is_english else "Mode Phrase"
        self.title_label = SentenceAccessibleLabel(
            visual_text=title_text,
            accessible_text=title_text,
        )
        self.title_label.setStyleSheet(
            "padding: 16px; background-color: #13131f; color: #0fecb0;"
            "border: 2px solid #0fecb0; border-radius: 10px;"
            "font-size: 26px; font-weight: bold;"
        )
        layout.addWidget(self.title_label)

        self.sentence_display = SentenceAccessibleLabel(
            visual_text="",
            accessible_text="",
        )
        self.sentence_display.setStyleSheet(
            "padding: 18px; background-color: #1a1a2e; color: #f9d342;"
            "border: 2px solid #f9d342; border-radius: 10px;"
            "font-size: 24px; min-height: 140px;"
        )
        layout.addWidget(self.sentence_display)

        self.current_word_label = SentenceAccessibleLabel(
            visual_text="",
            accessible_text="",
        )
        self.current_word_label.setStyleSheet(
            "padding: 14px; background-color: #0f172a; color: #f9d342;"
            "border: 2px solid #f9d342; border-radius: 10px;"
            "font-size: 22px;"
        )
        layout.addWidget(self.current_word_label)

        status_layout = QHBoxLayout()
        self.sentences_left_label = SentenceAccessibleLabel(
            visual_text="Sentences Left: 12",
            accessible_text="Sentences left: 12",
        )
        self.sentences_left_label.setStyleSheet(
            "padding: 12px; background-color: #1a1a2e; color: #f9d342;"
            "border: 2px solid #f9d342; border-radius: 10px; font-size: 20px;"
        )
        status_layout.addWidget(self.sentences_left_label)

        self.average_accuracy_label = SentenceAccessibleLabel(
            visual_text="Average Accuracy: ?",
            accessible_text="Average accuracy is not available yet.",
        )
        self.average_accuracy_label.setStyleSheet(
            "padding: 12px; background-color: #1a1a2e; color: #f9d342;"
            "border: 2px solid #f9d342; border-radius: 10px; font-size: 20px;"
        )
        status_layout.addWidget(self.average_accuracy_label)
        layout.addLayout(status_layout)

        self.input_field = SentenceTypingInput(self)
        self.input_field.setAccessibleName(
            "Type the current sentence here"
            if self.is_english else
            "Tapez la phrase actuelle ici"
        )
        self.input_field.setStyleSheet(
            "padding: 14px; background-color: black; color: #f9d342;"
            "border: 2px solid #f9d342; border-radius: 10px; font-size: 22px;"
        )
        self.input_field.setPlaceholderText(
            "Type the full sentence, then press Enter." if self.is_english else
            "Tapez la phrase complète, puis appuyez sur Entrée."
        )
        layout.addWidget(self.input_field)

        button_layout = QHBoxLayout()
        self.btn_quit = AccessiblePushButton(
            "Quit" if self.is_english else "Quitter"
        )
        self.btn_quit.clicked.connect(self._on_shift_enter)
        button_layout.addWidget(self.btn_quit)

        self.btn_hear_again = AccessiblePushButton(
            "Repeat Current Word" if self.is_english else "Répéter le mot actuel"
        )
        self.btn_hear_again.clicked.connect(self.repeat_current_word)
        button_layout.addWidget(self.btn_hear_again)
        layout.addLayout(button_layout)

        help_text = (
            "Ctrl repeats the current word. Ctrl+number repeats that word index.\n"
            "Shift+Ctrl: status | Shift+Enter: exit"
            if self.is_english else
            "Ctrl répète le mot actuel. Ctrl+chiffre répète le mot correspondant.\n"
            "Maj+Ctrl: statut | Maj+Entrée: quitter"
        )
        self.help_display = SentenceAccessibleBrowser(
            text=help_text,
            accessible_text=help_text,
        )
        self.help_display.setMinimumHeight(90)
        layout.addWidget(self.help_display)

        self.setLayout(layout)

    # ----------------------------------------------------------------------
    # Session lifecycle
    # ----------------------------------------------------------------------

    def start_session(self):
        self._prepare_sentence_pool()
        self.current_sentence_index = 0
        self.sentence_results = []
        self.total_xp_earned = 0
        self.total_boss_damage = 0
        self.passed = False
        self.session_finished = False
        self._show_welcome_dialog()

    def _prepare_sentence_pool(self):
        pool = sentences_en if self.is_english else sentences_fr
        if not pool or len(pool) < self.sentence_count_required:
            pool = [
                "This is a sample sentence for sentence mode.",
                "The quick brown fox jumps over the lazy dog.",
                "Typing full sentences improves accuracy and rhythm.",
                "Please press Enter once the entire sentence is complete.",
                "Use control and number keys to repeat words while typing."
            ]
        sample = pool.copy()
        random.shuffle(sample)
        self.session_sentences = sample[: self.sentence_count_required]

    def _show_welcome_dialog(self):
        intro = QDialog(self)
        intro.setWindowTitle(
            "Sentence Mode" if self.is_english else "Mode Phrase"
        )
        intro.setMinimumWidth(560)
        intro.setStyleSheet(self.styleSheet())

        layout = QVBoxLayout()
        if self.is_english:
            title = "Sentence Mode"
            explanation = (
                "Sentence Mode is calm and realistic. You will type full sentences instead of letters or combos.\n"
                "Finish 12 sentences with 80% or higher average accuracy to pass.\n"
                "This mode is designed for natural typing flow rather than punishment.\n\n"
                "Interaction model: the sentence is spoken first, then each word is spoken and spelled.\n"
                "Type the sentence word by word. Press Ctrl to repeat the current word, or Ctrl+number to repeat a different word.\n"
                "Shift+Ctrl announces status. Shift+Enter exits with penalty.\n"
                "When you reach the end, press Enter to submit the whole sentence."
            )
            start_text = "I'm ready for it!"
            cancel_text = "Not yet"
        else:
            title = "Mode Phrase"
            explanation = (
                "Le mode Phrase est calme et réaliste. Vous taperez des phrases complètes plutôt que des lettres ou des combos.\n"
                "Terminez 12 phrases avec une précision moyenne d'au moins 80% pour réussir.\n"
                "Ce mode est conçu pour un flux de frappe naturel plutôt que pour une punition.\n\n"
                "Modèle d'interaction : la phrase est d'abord prononcée, puis chaque mot est prononcé et épelé.\n"
                "Tapez la phrase mot par mot. Appuyez sur Ctrl pour répéter le mot actuel, ou Ctrl+chiffre pour répéter un autre mot.\n"
                "Maj+Ctrl annonce le statut. Maj+Entrée quitte avec pénalité.\n"
                "Lorsque vous avez atteint la fin, appuyez sur Entrée pour soumettre la phrase entière."
            )
            start_text = "Je suis prêt !"
            cancel_text = "Pas encore"

        title_label = SentenceAccessibleLabel(visual_text=title, accessible_text=title)
        title_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #0fecb0;"
            "background-color: transparent; border: none; padding: 8px;"
        )
        layout.addWidget(title_label)

        instructions = SentenceAccessibleBrowser(text=explanation, accessible_text=explanation)
        instructions.setMinimumHeight(180)
        layout.addWidget(instructions)

        buttons = QHBoxLayout()
        btn_start = AccessiblePushButton(start_text)
        btn_start.clicked.connect(lambda: self._start_typing_session(intro))
        buttons.addWidget(btn_start)

        btn_cancel = AccessiblePushButton(cancel_text)
        btn_cancel.clicked.connect(intro.reject)
        buttons.addWidget(btn_cancel)

        layout.addLayout(buttons)
        intro.setLayout(layout)
        intro.exec_()

    def _start_typing_session(self, dialog):
        dialog.accept()
        self._load_current_sentence()
        self.show()
        self.raise_()
        self.activateWindow()
        self.input_field.setFocus()

    def _load_current_sentence(self):
        if self.current_sentence_index >= len(self.session_sentences):
            return
        self.current_sentence = self.session_sentences[self.current_sentence_index]
        self.words = self.current_sentence.split()
        self.current_word_index = 0
        self.input_field.clear()
        self._update_display_labels()
        self._announce_sentence()

    # ----------------------------------------------------------------------
    # Display and speech helpers
    # ----------------------------------------------------------------------

    def _update_display_labels(self):
        sentence_text = self.current_sentence if self.current_sentence else ""
        sentence_access = (
            f"Current sentence: {self.current_sentence}"
            if self.is_english else
            f"Phrase actuelle : {self.current_sentence}"
        )
        self.sentence_display.update_text(sentence_text, sentence_access)

        current_word = self.words[self.current_word_index] if self.words else ""
        current_access = (
            f"Current word: {current_word}"
            if self.is_english else
            f"Mot actuel : {current_word}"
        )
        self.current_word_label.update_text(current_word, current_access)

        left = self.sentence_count_required - len(self.sentence_results)
        left_text = (
            f"Sentences Left: {left}"
            if self.is_english else
            f"Phrases restantes : {left}"
        )
        left_access = (
            f"{left} sentences left"
            if self.is_english else
            f"{left} phrases restantes"
        )
        self.sentences_left_label.update_text(left_text, left_access)

        if not self.sentence_results:
            avg_text = "Average Accuracy: ?"
            avg_access = ("Average accuracy is not available yet."
                          if self.is_english else
                          "La précision moyenne n'est pas encore disponible.")
        else:
            average = sum(self.sentence_results) / len(self.sentence_results)
            avg_text = f"Average Accuracy: {average:.1f}%"
            avg_access = f"Average accuracy is {average:.1f} percent"
        self.average_accuracy_label.update_text(avg_text, avg_access)

    def _get_char_pronunciation(self, char):
        from weeks import symbol_pronounciation
        if char in symbol_pronounciation:
            return symbol_pronounciation[char]
        if char.isupper() and char.isalpha():
            return f"{char.lower()} majuscule" if not self.is_english else f"{char.lower()} capital"
        return char

    def _announce_text(self, text):
        if self.base_logic.speaker:
            self.base_logic.speaker.output(text)

    def _cancel_pending_timers(self):
        for timer in self.pending_timers:
            timer.stop()
        self.pending_timers = []

    def has_pending_announcements(self):
        return any(timer.isActive() for timer in self.pending_timers)

    def stop_pending_announcements(self):
        self._cancel_pending_timers()

    def _pause_announcement(self):
        if not self._announcement_paused:
            self._announcement_paused = True
            self._cancel_pending_timers()

    def _resume_announcement(self):
        if self._announcement_paused:
            self._announcement_paused = False

    # ----------------------------------------------------------------------
    # Sentence announcement and word spelling
    # ----------------------------------------------------------------------

    def _announce_sentence(self):
        self._cancel_pending_timers()
        self._announce_text(self.current_sentence)
        QTimer.singleShot(1200, self._speak_current_word)

    def _speak_current_word(self):
        if not self.words:
            return
        self._cancel_pending_timers()
        word = self.words[self.current_word_index]
        self._announce_text(word)
        delay = 500
        for char in word:
            pron = self._get_char_pronunciation(char)
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda p=pron: self._announce_text(p))
            timer.start(delay)
            self.pending_timers.append(timer)
            delay += len(pron) * 65 + 200

    # ----------------------------------------------------------------------
    # Word navigation
    # ----------------------------------------------------------------------

    def advance_word(self):
        if self.current_word_index < len(self.words) - 1:
            self.current_word_index += 1
            self._update_display_labels()
            self._speak_current_word()
        else:
            if self.base_logic.speaker:
                msg = (
                    "No more words, please press enter."
                    if self.is_english else
                    "Plus de mots, veuillez appuyer sur Entrée."
                )
                self.base_logic.speaker.output(msg)

    def move_word_back(self):
        if self.current_word_index > 0:
            self.current_word_index -= 1
            self._update_display_labels()
            self._speak_current_word()

    # ----------------------------------------------------------------------
    # Repeat commands
    # ----------------------------------------------------------------------

    def repeat_current_word(self):
        if not self.words:
            return
        self._speak_current_word()

    def repeat_word_index(self, index):
        if index < 0 or index >= len(self.words):
            if self.base_logic.speaker:
                msg = (
                    "Word number is out of range." if self.is_english else
                    "Le numéro de mot est hors de portée."
                )
                self.base_logic.speaker.output(msg)
            return
        self.current_word_index = index
        self._update_display_labels()
        self._speak_current_word()

    # ----------------------------------------------------------------------
    # Sentence submission and accuracy
    # ----------------------------------------------------------------------

    def submit_sentence(self):
        typed = self.input_field.text().strip()
        accuracy = self._calculate_accuracy(self.current_sentence, typed)
        self.sentence_results.append(accuracy)
        xp = self._sentence_xp(accuracy)
        self.total_xp_earned += xp
        self._update_display_labels()

        self.current_sentence_index += 1
        if self.current_sentence_index >= self.sentence_count_required:
            self._finish_session()
        else:
            self._load_current_sentence()

    def _calculate_accuracy(self, target, typed):
        target_words = target.strip().split()
        typed_words = typed.strip().split()
        max_count = max(len(target_words), len(typed_words))
        matched = 0
        total = 0
        for idx in range(max_count):
            tgt = target_words[idx] if idx < len(target_words) else "??"
            typ = typed_words[idx] if idx < len(typed_words) else "??"
            word_len = max(len(tgt), len(typ))
            for pos in range(word_len):
                tc = tgt[pos] if pos < len(tgt) else "?"
                pc = typ[pos] if pos < len(typ) else "?"
                if tc == pc:
                    matched += 1
                total += 1
        return (matched / total * 100) if total > 0 else 0.0

    def _sentence_xp(self, accuracy):
        if accuracy >= 90.0:
            return 15
        if accuracy >= 80.0:
            return 10
        return 0

    # ----------------------------------------------------------------------
    # Session completion
    # ----------------------------------------------------------------------

    def _finish_session(self):
        self.session_finished = True
        average = sum(self.sentence_results) / len(self.sentence_results)
        self.passed = average >= 80.0 and len(self.sentence_results) >= self.sentence_count_required
        self.total_boss_damage = 15 if self.passed else 0
        if self.passed and average > 95.0:
            self.total_xp_earned += 20
            self.total_boss_damage += 5
        self._show_results_dialog(average)

    def _show_results_dialog(self, average):
        dlg = QDialog(self)
        dlg.setWindowTitle(
            "Sentence Mode Results" if self.is_english else "Résultats Mode Phrase"
        )
        dlg.setMinimumWidth(560)
        dlg.setStyleSheet(self.styleSheet())

        layout = QVBoxLayout()
        title = (
            "Sentence Mode Complete" if self.is_english else "Mode Phrase Terminé"
        )
        title_label = SentenceAccessibleLabel(visual_text=title, accessible_text=title)
        title_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #0fecb0;"
            "background-color: transparent; border: none; padding: 8px;"
        )
        layout.addWidget(title_label)

        result_text = []
        if self.passed:
            summary = (
                "You passed Sentence Mode!" if self.is_english else
                "Vous avez réussi le Mode Phrase !"
            )
            result_text.append(summary)
        else:
            summary = (
                "You failed Sentence Mode." if self.is_english else
                "Vous avez échoué au Mode Phrase."
            )
            result_text.append(summary)

        accuracy_text = (
            f"Average Accuracy: {average:.1f}%"
            if self.is_english else
            f"Précision Moyenne : {average:.1f}%"
        )
        result_text.append(accuracy_text)

        xp_text = (
            f"XP Earned: {self.total_xp_earned}"
            if self.is_english else
            f"XP Gagnés : {self.total_xp_earned}"
        )
        result_text.append(xp_text)

        boss_text = (
            f"Boss Health Reduction: -{self.total_boss_damage}%"
            if self.is_english else
            f"Réduction Santé Boss : -{self.total_boss_damage}%"
        )
        result_text.append(boss_text)

        if self.passed and average > 95.0:
            bonus_text = (
                "Bonus reward earned for 95%+ average accuracy!"
                if self.is_english else
                "Bonus gagné pour une précision moyenne supérieure à 95% !"
            )
            result_text.append(bonus_text)

        summary_display = SentenceAccessibleBrowser(
            text="\n".join(result_text),
            accessible_text="\n".join(result_text),
        )
        summary_display.setMinimumHeight(180)
        layout.addWidget(summary_display)

        breakdown_lines = []
        for idx, accuracy in enumerate(self.sentence_results, start=1):
            line = (
                f"{idx}. {self.session_sentences[idx-1]} - {accuracy:.1f}%"
                if self.is_english else
                f"{idx}. {self.session_sentences[idx-1]} - {accuracy:.1f}%"
            )
            breakdown_lines.append(line)

        breakdown_display = SentenceAccessibleBrowser(
            text="\n".join(breakdown_lines),
            accessible_text="\n".join(breakdown_lines),
        )
        breakdown_display.setMinimumHeight(260)
        layout.addWidget(breakdown_display)

        button_layout = QHBoxLayout()
        if self.passed:
            btn_back = AccessiblePushButton(
                "Go Back to Challenge Battle" if self.is_english else
                "Retour au Combat de Défi"
            )
            btn_back.clicked.connect(lambda: self._complete_and_close(dlg))
            button_layout.addWidget(btn_back)
        else:
            btn_retry = AccessiblePushButton(
                "Retry" if self.is_english else "Recommencer"
            )
            btn_retry.clicked.connect(lambda: self._retry_from_results(dlg))
            button_layout.addWidget(btn_retry)

            btn_back = AccessiblePushButton(
                "Go Back to Challenge Battle" if self.is_english else
                "Retour au Combat de Défi"
            )
            btn_back.clicked.connect(lambda: self._close_without_reward(dlg))
            button_layout.addWidget(btn_back)

        layout.addLayout(button_layout)
        dlg.setLayout(layout)
        dlg.exec_()

    def _complete_and_close(self, dialog):
        dialog.accept()
        self._apply_sentence_rewards()
        self._close_to_challenge()

    def _retry_from_results(self, dialog):
        dialog.accept()
        self.start_session()

    def _close_without_reward(self, dialog):
        dialog.accept()
        self._close_to_challenge()

    def _apply_sentence_rewards(self):
        if not self.parent_challenge or not hasattr(self.parent_challenge, 'logic'):
            return
        logic = self.parent_challenge.logic
        logic.add_xp(int(self.total_xp_earned))
        logic.boss_health = max(0, logic.boss_health - self.total_boss_damage)
        logic.modes["sentence"]["status"] = "done"
        logic.modes["sentence"]["completed"] = True
        logic.completed_modes_count = sum(
            1 for v in logic.modes.values() if v["completed"]
        )
        for mk, data in logic.modes.items():
            if mk != "crazy_party" and not data["completed"]:
                data["status"] = "unlocked"
        logic.save_progress()
        self.parent_challenge.update_display()

    def _close_to_challenge(self):
        self.session_finished = True   # ensure closeEvent doesn't show exit dialog
        self.close()
        if self.parent_challenge:
            self.parent_challenge.pages.setCurrentIndex(1)
            self.parent_challenge.update_display()

    # ----------------------------------------------------------------------
    # Status announcement (Shift+Ctrl)
    # ----------------------------------------------------------------------

    def _announce_status(self):
        self._pause_announcement()
        left = self.sentence_count_required - len(self.sentence_results)
        if not self.sentence_results:
            avg_text = "?" if self.is_english else "?"
        else:
            avg = sum(self.sentence_results) / len(self.sentence_results)
            avg_text = f"{avg:.1f}%"
        if self.is_english:
            msg = f"Average accuracy: {avg_text}. Sentences left: {left}."
        else:
            msg = f"Précision moyenne : {avg_text}. Phrases restantes : {left}."
        if self.base_logic.speaker:
            self.base_logic.speaker.output(msg)
        delay = len(msg) * 100 + 500
        QTimer.singleShot(delay, self._resume_announcement)

    # ----------------------------------------------------------------------
    # Exit handling
    # ----------------------------------------------------------------------

    def _on_shift_enter(self):
        if self.session_finished:
            return
        self._pause_announcement()
        dlg = QDialog(self)
        dlg.setWindowTitle("Exit?" if self.is_english else "Quitter ?")
        dlg.setMinimumWidth(480)
        dlg.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout()
        msg_text = (
            "Exit Sentence Mode?\n\nA 50 XP penalty will be applied."
            if self.is_english else
            "Quitter le Mode Phrase ?\n\nUne penalite de 50 XP sera appliquee."
        )
        msg = SentenceAccessibleBrowser(text=msg_text, accessible_text=msg_text)
        layout.addWidget(msg)
        btn_row = QHBoxLayout()
        btn_yes = AccessiblePushButton("Yes, exit" if self.is_english else "Oui, quitter")
        btn_no = AccessiblePushButton("No, continue" if self.is_english else "Non, continuer")
        btn_yes.clicked.connect(lambda: self._confirm_exit(dlg))
        btn_no.clicked.connect(lambda: self._cancel_exit(dlg))
        btn_row.addWidget(btn_yes)
        btn_row.addWidget(btn_no)
        layout.addLayout(btn_row)
        dlg.setLayout(layout)
        dlg.exec_()

    def _confirm_exit(self, dialog):
        dialog.accept()
        self._apply_exit_penalty()
        self._close_to_challenge()

    def _cancel_exit(self, dialog):
        dialog.reject()
        self._resume_announcement()

    def _apply_exit_penalty(self):
        if self.parent_challenge and hasattr(self.parent_challenge, 'logic'):
            logic = self.parent_challenge.logic
            logic.xp_balance = max(0, logic.xp_balance - 50)
            logic.save_progress()
            self.parent_challenge.update_display()
        if self.base_logic.speaker:
            msg = (
                "Sentence Mode exited. 50 XP penalty applied."
                if self.is_english else
                "Mode Phrase quitté. Pénalité de 50 XP appliquée."
            )
            self.base_logic.speaker.output(msg)

    def leave_session(self):
        self._on_shift_enter()

    # ----------------------------------------------------------------------
    # Window close event
    # ----------------------------------------------------------------------

    def closeEvent(self, event):
        if self._closing:
            event.accept()
            return
        if self.session_finished or not self.current_sentence:
            event.accept()
            return
        self._closing = True
        self._on_shift_enter()
        event.ignore()