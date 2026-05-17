import random
import time
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLineEdit, QLabel, QDialog, QTextBrowser)
from PyQt5.QtCore import Qt, QTimer
from weeks import sentences_en, sentences_fr


class SentenceAccessibleLabel(QLabel):
    def __init__(self, visual_text="", accessible_text="", parent=None):
        super().__init__(visual_text, parent)
        self.setFocusPolicy(Qt.TabFocus)
        self.setAccessibleName(accessible_text if accessible_text else visual_text)
        self.setStyleSheet(
            "padding: 12px;"
            "background-color: #1a1a2e;"
            "color: #f9d342;"
            "border: 2px solid #f9d342;"
            "border-radius: 10px;"
            "font-size: 22px;"
        )
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignCenter)

    def update_text(self, visual_text, accessible_text=None):
        self.setText(visual_text)
        self.setAccessibleName(
            accessible_text if accessible_text is not None else visual_text
        )


class SentenceAccessibleBrowser(QTextBrowser):
    def __init__(self, text="", accessible_text="", parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setOpenExternalLinks(False)
        self.setPlainText(text)
        self.setFocusPolicy(Qt.TabFocus)
        self.setAccessibleName(accessible_text if accessible_text else text)
        self.setStyleSheet(
            "padding: 14px;"
            "background-color: #1a1a2e;"
            "color: #f9d342;"
            "border: 2px solid #f9d342;"
            "border-radius: 10px;"
            "font-size: 20px;"
        )

    def update_text(self, text, accessible_text=None):
        self.setPlainText(text)
        self.setAccessibleName(accessible_text if accessible_text is not None else text)


class SentenceTypingInput(QLineEdit):
    def __init__(self, mode, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = mode

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.mode.repeat_current_word()
            return

        if event.modifiers() & Qt.ControlModifier:
            text = event.text()
            if text.isdigit():
                index = int(text) - 1
                self.mode.repeat_word_index(index)
                return

        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.mode.submit_sentence()
            return

        if event.key() == Qt.Key_Space:
            super().keyPressEvent(event)
            self.mode.advance_word()
            return

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
        self._setup_ui()

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
        self.btn_quit = QPushButton(
            "Quit" if self.is_english else "Quitter"
        )
        self.btn_quit.clicked.connect(self.leave_session)
        button_layout.addWidget(self.btn_quit)

        self.btn_hear_again = QPushButton(
            "Repeat Current Word" if self.is_english else "Répéter le mot actuel"
        )
        self.btn_hear_again.clicked.connect(self.repeat_current_word)
        button_layout.addWidget(self.btn_hear_again)
        layout.addLayout(button_layout)

        help_text = (
            "Ctrl repeats the current word. Ctrl + number repeats that word index."
            if self.is_english else
            "Ctrl répète le mot actuel. Ctrl + chiffre répète le mot correspondant."
        )
        self.help_display = SentenceAccessibleBrowser(
            text=help_text,
            accessible_text=help_text,
        )
        self.help_display.setMinimumHeight(90)
        layout.addWidget(self.help_display)

        self.setLayout(layout)

    def start_session(self):
        self._prepare_sentence_pool()
        self.current_sentence_index = 0
        self.sentence_results = []
        self.total_xp_earned = 0
        self.total_boss_damage = 0
        self.passed = False
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
                "Type the sentence word by word. Press Ctrl to repeat the current word, or Ctrl + number to repeat a different word.\n"
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
                "Tapez la phrase mot par mot. Appuyez sur Ctrl pour répéter le mot actuel, ou Ctrl + chiffre pour répéter un autre mot.\n"
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
        btn_start = QPushButton(start_text)
        btn_start.clicked.connect(lambda: self._start_typing_session(intro))
        buttons.addWidget(btn_start)

        btn_cancel = QPushButton(cancel_text)
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
        for letter in word:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda l=letter: self._announce_text(l))
            timer.start(delay)
            self.pending_timers.append(timer)
            delay += 280

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
        for index in range(max_count):
            tgt = target_words[index] if index < len(target_words) else "??"
            typ = typed_words[index] if index < len(typed_words) else "??"
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

    def _finish_session(self):
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
            btn_back = QPushButton(
                "Go Back to Challenge Battle" if self.is_english else
                "Retour au Combat de Défi"
            )
            btn_back.clicked.connect(lambda: self._complete_and_close(dlg))
            button_layout.addWidget(btn_back)
        else:
            btn_retry = QPushButton(
                "Retry" if self.is_english else "Recommencer"
            )
            btn_retry.clicked.connect(lambda: self._retry_from_results(dlg))
            button_layout.addWidget(btn_retry)

            btn_back = QPushButton(
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
        self.close()
        if self.parent_challenge:
            self.parent_challenge.pages.setCurrentIndex(1)
            self.parent_challenge.update_display()

    def leave_session(self):
        self.close()
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
        if self.parent_challenge:
            self.parent_challenge.pages.setCurrentIndex(1)

    def closeEvent(self, event):
        self._cancel_pending_timers()
        event.accept()
