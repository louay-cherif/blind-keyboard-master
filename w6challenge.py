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

"""
Week 6: Ultimate Challenge - Final comprehensive keyboard mastery mode
"""

import time
import os
import csv
import random
import winsound
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QLabel, QStackedWidget, QDialog, QApplication, QMessageBox,
                             QTextBrowser)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from weeks import symbol_pronounciation, w6words
from survival_mode import SurvivalMode
from sentence_mode import SentenceMode
from static.accessible_widgets import AccessiblePushButton, AccessibleLabel, AccessibleBrowser


def _format_uppercase_announcement(char, is_english):
    """Return a screen-reader pronunciation for uppercase letters, with a special Y case."""
    if char == "Y":
        return "ay capital" if is_english else "i grec majuscule"
    return f"{char.lower()} capital" if is_english else f"{char.lower()} majuscule"


# ============= SHARED TYPING INPUT WITH KEYBOARD SHORTCUTS =============

class ChallengeTypingInput(QLineEdit):
    """
    Typing input used across all Week 6 modes.
    - Ctrl alone: repeat current target.
    - Shift+Enter: exit confirmation dialog (penalty).
    - Shift+Ctrl: announce status.
    - Any other key: interrupt TTS / resume timers.
    """

    def __init__(self, mode, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = mode

    def keyPressEvent(self, event):
        # Ctrl alone: repeat target
        if event.key() == Qt.Key_Control and event.modifiers() == Qt.ControlModifier:
            if hasattr(self.mode, 'repeat_current_target'):
                self.mode.repeat_current_target()
            return

        # Shift+Enter: exit confirmation
        if (event.key() in (Qt.Key_Return, Qt.Key_Enter)
                and event.modifiers() & Qt.ShiftModifier):
            if hasattr(self.mode, '_on_shift_enter'):
                self.mode._on_shift_enter()
            return

        # Shift+Ctrl: announce status
        if (event.key() == Qt.Key_Control
                and event.modifiers() & Qt.ShiftModifier):
            if hasattr(self.mode, '_announce_status'):
                self.mode._announce_status()
            return

        # Any other key: interrupt TTS / resume timers
        if hasattr(self.mode, 'on_typing_key_pressed'):
            self.mode.on_typing_key_pressed()

        super().keyPressEvent(event)


# ============= WARMUP WELCOME PAGE =============

class WarmupWelcomePage(QWidget):
    def __init__(self, parent, is_english=True):
        super().__init__()
        self.parent_challenge = parent
        self.is_english = is_english
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        if self.is_english:
            title_text   = "WARMUP GATE - Training Phase 1"
            welcome_text = "Welcome to Warmup Training"
            instructions = (
                "You are entering the first training phase of Boss Mode.\n"
                "Your objective is to survive 8 minutes of continuous typing practice.\n"
                "This will prepare you for future battles.\n\n"
                "Type the characters as they appear. Stay focused and keep typing.\n"
                "Ready? Let's begin!"
            )
            ready_text   = "I Am Ready"
            notyet_text  = "Not Yet"
        else:
            title_text   = "PORTE RECHauffEMENT - Phase d'Entraînement 1"
            welcome_text = "Bienvenue à l'Entraînement"
            instructions = (
                "Vous entrez dans la première phase d'entraînement du Mode Boss.\n"
                "Votre objectif est de survivre 8 minutes de pratique dactylographique continue.\n"
                "Cela vous préparera pour les batailles futures.\n\n"
                "Tapez les caractères au fur et à mesure qu'ils apparaissent. Restez concentré.\n"
                "Prêt ? Commençons !"
            )
            ready_text   = "Je Suis Prêt"
            notyet_text  = "Pas encore"

        title = AccessibleLabel(visual_text=title_text, accessible_text=title_text)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #0fecb0; background-color: transparent; border: none; padding: 8px;")
        layout.addWidget(title)

        welcome = AccessibleLabel(visual_text=welcome_text, accessible_text=welcome_text)
        welcome.setStyleSheet("font-size: 20px; font-weight: bold; color: #e94560; background-color: transparent; border: none; padding: 4px;")
        layout.addWidget(welcome)

        inst_field = AccessibleBrowser(text=instructions, accessible_text=instructions)
        inst_field.setMinimumHeight(180)
        layout.addWidget(inst_field)

        btn_layout = QHBoxLayout()
        btn_ready = AccessiblePushButton(ready_text)
        btn_ready.clicked.connect(self._launch)
        btn_layout.addWidget(btn_ready)

        btn_notyet = AccessiblePushButton(notyet_text)
        btn_notyet.clicked.connect(self.close)
        btn_layout.addWidget(btn_notyet)

        layout.addLayout(btn_layout)
        layout.addStretch()
        self.setLayout(layout)

    def _launch(self):
        if hasattr(self.parent_challenge, 'launch_warmup_session'):
            self.parent_challenge.launch_warmup_session()
        self.close()


# ============= GENERIC TYPING MODE (Warmup) =============

class GenericTypingMode(QWidget):
    """
    Reusable 8-minute typing session.
    Override get_random_target() in subclasses.
    """

    def __init__(self, base_logic, mode_name="Warmup Gate", is_english=True, parent=None):
        super().__init__()
        self.base_logic       = base_logic
        self.mode_name        = mode_name
        self.is_english       = is_english
        self.parent_challenge = parent

        self.session_start_time = None
        self.session_duration   = 480
        self.current_target     = ""
        self.target_start_time  = None
        self.target_timeout     = 2.0
        self._original_target   = ""

        self.correct_count   = 0
        self.incorrect_count = 0
        self.timeout_count   = 0
        self.xp_earned       = 0.0
        self.session_xp      = 0.0
        self.accuracy        = 0.0

        self.warmup_csv_path = None
        self._announcement_paused = False

        self._setup_ui()
        self._setup_timers()

    def _setup_ui(self):
        layout = QVBoxLayout()
        if self.is_english:
            mode_label_text   = "WARMUP GATE - Continuous Practice"
            instructions_text = (
                "Type each character that appears.\n"
                "Incorrect entries and timeouts do not stop the session - keep typing!"
            )
            xp_text           = "XP Earned: 0"
            timer_text        = "Time: 8:00"
            button_text       = "Leave and Go Back to Challenge Battle"
        else:
            mode_label_text   = "PORTE RECHauffEMENT - Pratique Continue"
            instructions_text = (
                "Tapez chaque caractère qui apparaît.\n"
                "Les erreurs et dépassements ne stoppent pas la session - continuez !"
            )
            xp_text           = "XP Gagné : 0"
            timer_text        = "Temps : 8:00"
            button_text       = "Quitter et Retourner au Combat de Défi"

        mode_title = AccessibleLabel(visual_text=mode_label_text, accessible_text=mode_label_text)
        mode_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #0fecb0; background-color: transparent; border: none; padding: 6px;")
        layout.addWidget(mode_title)

        self.instructions_display = AccessibleBrowser(text=instructions_text, accessible_text=instructions_text)
        self.instructions_display.setMinimumHeight(70)
        layout.addWidget(self.instructions_display)

        stats_layout = QHBoxLayout()
        self.xp_label = AccessibleLabel(visual_text=xp_text, accessible_text=xp_text)
        stats_layout.addWidget(self.xp_label)
        self.timer_label = AccessibleLabel(visual_text=timer_text, accessible_text=timer_text)
        stats_layout.addWidget(self.timer_label)
        layout.addLayout(stats_layout)

        self.target_display = AccessibleLabel(visual_text="", accessible_text="Waiting for session to start")
        self.target_display.setStyleSheet("font-size: 120px; color: #f9d342; border: 3px solid #f9d342; border-radius: 10px; background-color: #1a1a2e; padding: 8px; min-height: 160px;")
        layout.addWidget(self.target_display)

        self.input_field = ChallengeTypingInput(self)
        self.input_field.textChanged.connect(self._on_input_changed)
        layout.addWidget(self.input_field)

        btn_leave = AccessiblePushButton(button_text)
        btn_leave.clicked.connect(self.leave_session)
        layout.addWidget(btn_leave)

        self.setLayout(layout)

    def _setup_timers(self):
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self._update_session_timer)
        self.target_timer = QTimer()
        self.target_timer.setSingleShot(True)
        self.target_timer.timeout.connect(self._on_target_timeout)
        self.message_timer = QTimer()
        self.message_timer.setSingleShot(True)
        self.message_timer.timeout.connect(self._clear_message_display)

    def start_session(self):
        self.session_start_time = time.time()
        self.correct_count = 0
        self.incorrect_count = 0
        self.timeout_count = 0
        self.session_xp = 0.0
        self.xp_earned = 0.0
        self._init_warmup_csv()
        self.session_timer.start(1000)
        self._next_target()
        if self.base_logic.speaker:
            msg = ("Warmup session started. Begin typing!" if self.is_english
                   else "Session de réchauffement démarrée. Commencez à taper !")
            self.base_logic.speaker.output(msg)

    def _init_warmup_csv(self):
        clean_name = self.base_logic.get_clean_username()
        user_dir = os.path.join(self.base_logic.data_dir, clean_name)
        os.makedirs(user_dir, exist_ok=True)
        self.warmup_csv_path = os.path.join(user_dir, f"{clean_name}_Warmup_Session.csv")
        try:
            with open(self.warmup_csv_path, 'w', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow(["Timestamp", "Target", "Status", "Typing Time (s)"])
        except Exception:
            pass

    def _log_attempt(self, target, status, typing_time=None):
        if not self.warmup_csv_path:
            return
        try:
            with open(self.warmup_csv_path, 'a', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow([
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    target,
                    status,
                    round(typing_time, 3) if status == "correct" and typing_time is not None else "!",
                ])
        except Exception:
            pass

    def get_random_target(self):
        lowercase = "abcdefghijklmnopqrstuvwxyz"
        uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        symbols = "".join(symbol_pronounciation.keys())
        pool = lowercase * 15 + uppercase * 5 + symbols * 3
        return random.choice(pool)

    def _next_target(self):
        self.target_timer.stop()
        self.current_target = self.get_random_target()
        self.target_start_time = time.time()

        if self.current_target in symbol_pronounciation or self.current_target.isupper():
            self.target_timeout = 3.0
        else:
            self.target_timeout = 2.0

        if self.current_target in symbol_pronounciation:
            announcement = symbol_pronounciation[self.current_target]
        elif self.current_target.isupper():
            announcement = _format_uppercase_announcement(self.current_target, self.is_english)
        else:
            announcement = self.current_target

        self.target_display.update_text(self.current_target, announcement)
        if self.base_logic.speaker:
            self.base_logic.speaker.output(announcement)

        self.input_field.textChanged.disconnect(self._on_input_changed)
        self.input_field.clear()
        self.input_field.textChanged.connect(self._on_input_changed)
        self.input_field.setFocus()
        self.target_timer.start(int(self.target_timeout * 1000))

    def _on_input_changed(self, text):
        if not text:
            return
        typed = text[-1]
        if typed == self.current_target:
            self.target_timer.stop()
            typing_time = time.time() - self.target_start_time
            winsound.Beep(1500, 100)
            self.correct_count += 1
            self.session_xp += 0.25
            self.xp_earned += 0.25
            self._update_xp_display()
            self._log_attempt(self.current_target, "correct", typing_time)
            self._next_target()
        else:
            # Single character mismatch: treat as incorrect immediately
            self.target_timer.stop()
            winsound.Beep(400, 200)
            self.incorrect_count += 1
            self.session_xp -= 0.5
            self.xp_earned -= 0.5
            self._update_xp_display()
            self._log_attempt(self.current_target, "incorrect")
            self.input_field.textChanged.disconnect(self._on_input_changed)
            self.input_field.clear()
            self.input_field.textChanged.connect(self._on_input_changed)
            self._next_target()

    def _on_target_timeout(self):
        winsound.Beep(600, 300)
        self.timeout_count += 1
        self.session_xp -= 1.0
        self.xp_earned -= 1.0
        self._update_xp_display()
        self._log_attempt(self.current_target, "timeout")
        self._next_target()

    def _update_xp_display(self):
        v = (f"XP Earned: {self.xp_earned:.2f}" if self.is_english else f"XP Gagné : {self.xp_earned:.2f}")
        a = (f"{self.xp_earned:.2f} XP earned this session" if self.is_english else f"{self.xp_earned:.2f} XP gagnés cette session")
        self.xp_label.update_text(v, a)

    def _update_session_timer(self):
        elapsed = time.time() - self.session_start_time
        remaining = self.session_duration - elapsed
        if remaining <= 0:
            self._end_session()
            return
        m = int(remaining) // 60
        s = int(remaining) % 60
        v = f"Time: {m}:{s:02d}" if self.is_english else f"Temps : {m}:{s:02d}"
        a = (f"{m} minutes {s} seconds remaining" if self.is_english else f"{m} minutes {s} secondes restantes")
        self.timer_label.update_text(v, a)

    def show_temporary_message(self, message, duration=2000):
        self._original_target = self.current_target
        self.target_display.update_text(message, message)
        self.target_display.setStyleSheet("font-size: 60px; color: #0fecb0; border: 3px solid #0fecb0; border-radius: 10px; background-color: #1a1a2e; padding: 8px; min-height: 160px;")
        self.message_timer.start(duration)

    def _clear_message_display(self):
        t = self._original_target
        if t:
            ann = symbol_pronounciation.get(
                t,
                _format_uppercase_announcement(t, self.is_english) if t.isupper() else t
            )
            self.target_display.update_text(t, ann)
        self.target_display.setStyleSheet("font-size: 120px; color: #f9d342; border: 3px solid #f9d342; border-radius: 10px; background-color: #1a1a2e; padding: 8px; min-height: 160px;")

    def _end_session(self):
        self.session_timer.stop()
        self.target_timer.stop()
        self.message_timer.stop()
        total = self.correct_count + self.incorrect_count
        self.accuracy = (self.correct_count / total * 100) if total > 0 else 0.0
        self.session_xp += 30
        self.xp_earned += 30
        accuracy_bonus = boss_damage_bonus = 0
        if self.accuracy >= 90:
            accuracy_bonus = 20
            boss_damage_bonus = 5
            self.session_xp += 20
            self.xp_earned += 20
        self._update_challenge_state(accuracy_bonus, boss_damage_bonus)
        self._show_results_page()

    def _update_challenge_state(self, accuracy_bonus, boss_damage_bonus):
        if not (self.parent_challenge and hasattr(self.parent_challenge, 'logic')):
            return
        logic = self.parent_challenge.logic
        logic.add_xp(int(self.session_xp))
        if boss_damage_bonus > 0:
            logic.boss_health = max(0, logic.boss_health - boss_damage_bonus)
        logic.modes["warmup"]["status"] = "done"
        logic.modes["warmup"]["completed"] = True
        logic.completed_modes_count = sum(1 for v in logic.modes.values() if v["completed"])
        for mk, data in logic.modes.items():
            if mk != "crazy_party" and not data["completed"]:
                data["status"] = "unlocked"
        logic.save_progress()
        self.parent_challenge.update_display()

    def _show_results_page(self):
        if self.is_english:
            title = "WARMUP COMPLETE"
            correct_text = f"Correct Answers: {self.correct_count}"
            incorrect_text = f"Incorrect Answers: {self.incorrect_count}"
            timeout_text = f"Timeouts: {self.timeout_count}"
            accuracy_text = f"Accuracy: {self.accuracy:.1f}%"
            xp_text = f"Total XP Earned: {int(self.xp_earned)}"
            bonus_text = ("Accuracy Bonus: +20 XP  |  Boss Damage: -5%" if self.accuracy >= 90 else "Tip: reach 90%+ accuracy for a bonus!")
            button_text = "Return to Challenge Battle"
        else:
            title = "ECHauffEMENT COMPLET"
            correct_text = f"Bonnes Réponses : {self.correct_count}"
            incorrect_text = f"Mauvaises Réponses : {self.incorrect_count}"
            timeout_text = f"Dépassements : {self.timeout_count}"
            accuracy_text = f"Précision : {self.accuracy:.1f}%"
            xp_text = f"XP Total Gagné : {int(self.xp_earned)}"
            bonus_text = ("Bonus Précision : +20 XP  |  Dommage Boss : -5%" if self.accuracy >= 90 else "Conseil : atteignez 90%+ de précision pour un bonus !")
            button_text = "Retour au Combat de Défi"

        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setMinimumWidth(520)
        dlg.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout()
        title_label = AccessibleLabel(visual_text=title, accessible_text=title)
        title_label.setStyleSheet("font-size: 26px; font-weight: bold; color: #0fecb0; background-color: transparent; border: none; padding: 6px;")
        layout.addWidget(title_label)
        stats_text = f"{correct_text}\n{incorrect_text}\n{timeout_text}\n{accuracy_text}\n\n{xp_text}\n{bonus_text}"
        stats_browser = AccessibleBrowser(text=stats_text, accessible_text=stats_text)
        stats_browser.setMinimumHeight(220)
        layout.addWidget(stats_browser)
        btn_return = AccessiblePushButton(button_text)
        btn_return.clicked.connect(lambda: self._return_to_challenge(dlg))
        layout.addWidget(btn_return)
        dlg.setLayout(layout)
        dlg.exec_()

    def _return_to_challenge(self, dialog):
        dialog.accept()
        if self.parent_challenge:
            self.parent_challenge.pages.setCurrentIndex(1)
            self.parent_challenge.update_display()
        self.close()

    def _pause_timers(self):
        if not self._announcement_paused:
            self._announcement_paused = True
            self.session_timer.stop()
            self.target_timer.stop()

    def _resume_timers(self):
        if self._announcement_paused:
            self._announcement_paused = False
            if not self.session_timer.isActive() and self.session_start_time:
                self.session_timer.start(1000)
            if self.current_target and not self.target_timer.isActive():
                self.target_timer.start(int(self.target_timeout * 1000))

    def on_typing_key_pressed(self):
        if self._announcement_paused:
            self._resume_timers()

    def repeat_current_target(self):
        if not self.current_target:
            return
        if self.current_target in symbol_pronounciation:
            ann = symbol_pronounciation[self.current_target]
        elif self.current_target.isupper():
            ann = _format_uppercase_announcement(self.current_target, self.is_english)
        else:
            ann = self.current_target
        if self.base_logic.speaker:
            self.base_logic.speaker.output(ann)

    def _on_shift_enter(self):
        # Announce status and show exit dialog
        self._pause_timers()
        elapsed = time.time() - self.session_start_time
        remaining = self.session_duration - elapsed
        if remaining < 0:
            remaining = 0
        m = int(remaining) // 60
        s = int(remaining) % 60
        if self.is_english:
            msg = f"XP earned: {self.xp_earned:.1f}. Time remaining: {m} minutes {s} seconds."
        else:
            msg = f"XP gagnés : {self.xp_earned:.1f}. Temps restant : {m} minutes {s} secondes."
        if self.base_logic.speaker:
            self.base_logic.speaker.output(msg)
        # Show exit dialog after announcing
        self._show_exit_dialog()

    def _announce_status(self):
        self._pause_timers()
        elapsed = time.time() - self.session_start_time
        remaining = self.session_duration - elapsed
        if remaining < 0:
            remaining = 0
        m = int(remaining) // 60
        s = int(remaining) % 60
        if self.is_english:
            msg = f"XP earned: {self.xp_earned:.1f}. Time remaining: {m} minutes {s} seconds."
        else:
            msg = f"XP gagnés : {self.xp_earned:.1f}. Temps restant : {m} minutes {s} secondes."
        if self.base_logic.speaker:
            self.base_logic.speaker.output(msg)
        delay = len(msg) * 100 + 500
        QTimer.singleShot(delay, self._resume_timers)

    def _show_exit_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Exit?" if self.is_english else "Quitter ?")
        dlg.setMinimumWidth(480)
        dlg.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout()
        msg_text = ("Exit this session?\n\nA 50 XP penalty will be applied." if self.is_english
                    else "Quitter cette session ?\n\nUne penalite de 50 XP sera appliquee.")
        msg = AccessibleBrowser(text=msg_text, accessible_text=msg_text)
        layout.addWidget(msg)
        btn_row = QHBoxLayout()
        btn_yes = AccessiblePushButton("Yes, exit" if self.is_english else "Oui, quitter")
        btn_no = AccessiblePushButton("No, continue" if self.is_english else "Non, continuer")
        btn_yes.clicked.connect(dlg.accept)
        btn_no.clicked.connect(dlg.reject)
        btn_row.addWidget(btn_yes)
        btn_row.addWidget(btn_no)
        layout.addLayout(btn_row)
        dlg.setLayout(layout)
        if dlg.exec_() == QDialog.Accepted:
            self.leave_session()
        else:
            self._resume_timers()

    def leave_session(self):
        self.session_timer.stop()
        self.target_timer.stop()
        self.message_timer.stop()
        if self.warmup_csv_path and os.path.exists(self.warmup_csv_path):
            try:
                os.remove(self.warmup_csv_path)
            except Exception:
                pass
        if self.parent_challenge and hasattr(self.parent_challenge, 'logic'):
            logic = self.parent_challenge.logic
            logic.xp_balance = max(0, logic.xp_balance - 50)
            logic.save_progress()
            self.parent_challenge.update_display()
        if self.base_logic.speaker:
            msg = ("Session exited. 50 XP penalty applied." if self.is_english else "Session quittée. Pénalité de 50 XP appliquée.")
            self.base_logic.speaker.output(msg)
        if self.parent_challenge:
            self.parent_challenge.pages.setCurrentIndex(1)
        self.close()

    def closeEvent(self, event):
        if not self.session_start_time or not self.session_timer.isActive():
            event.accept()
            return
        self.session_timer.stop()
        self.target_timer.stop()
        self.message_timer.stop()
        self._show_exit_dialog()
        event.ignore()


# ============= COMBO MODE =============

class ComboTypingInput(QLineEdit):
    def __init__(self, mode, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = mode

    def keyPressEvent(self, event):
        # Ctrl alone: repeat target
        if event.key() == Qt.Key_Control and event.modifiers() == Qt.ControlModifier:
            if hasattr(self.mode, 'repeat_current_target'):
                self.mode.repeat_current_target()
            return

        # Shift+Enter: exit confirmation
        if (event.key() in (Qt.Key_Return, Qt.Key_Enter)
                and event.modifiers() & Qt.ShiftModifier):
            if hasattr(self.mode, '_on_shift_enter'):
                self.mode._on_shift_enter()
            return

        # Shift+Ctrl: announce status
        if (event.key() == Qt.Key_Control
                and event.modifiers() & Qt.ShiftModifier):
            if hasattr(self.mode, '_announce_status'):
                self.mode._announce_status()
            return

        # Any other key: interrupt TTS
        if hasattr(self.mode, 'on_typing_key_pressed'):
            self.mode.on_typing_key_pressed()

        super().keyPressEvent(event)


class ComboWelcomePage(QWidget):
    def __init__(self, parent, is_english=True):
        super().__init__()
        self.parent_challenge = parent
        self.is_english = is_english
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        if self.is_english:
            title_text = "COMBO RUSH - Stage-Based Multiplier Challenge"
            welcome_text = "Welcome to Combo Mode"
            instructions = (
                "Build your combo score through precision and survive increasing complexity!\n\n"
                "SCORING MECHANICS:\n"
                "- Correct answer: Doubles your current combo score\n"
                "- Incorrect answer: Divides your score by 3\n"
                "- Timeout: Resets score back to 0.1\n"
                "- Cap at 128: When your score reaches 128, it auto-converts to XP and resets to 0.1\n\n"
                "STAGE PROGRESSION:\n"
                "• Stage 1 (5 min): Single characters\n"
                "• Stage 2 (5 min): Two-character combos\n"
                "• Stage 3 (5 min): Three-character combos\n"
                "• Optional: Continue infinitely with longer combos for bonus rewards\n\n"
                "XP CONVERSION:\n"
                "After each correct answer, your combo score is converted to XP based on stage difficulty. "
                "Each stage increases conversion by 0.05 XP per point.\n"
                "Stage 1: 0.05 XP per point | Stage 2: 0.1 XP per point | Stage 3: 0.15 XP per point\n\n"
                "KEYBOARD SHORTCUTS:\n"
                "Ctrl: Repeat target | Shift+Ctrl: Status | Shift+Enter: Exit\n\n"
                "COMPLETION:\n"
                "Complete Stage 3 with ≥70% accuracy to succeed and damage the boss.\n"
                "Below 70%: Retry later. At or above 70%: +40 XP and -15% boss health!"
            )
            ready_text = "I Am Ready"
            notyet_text = "Not Yet"
        else:
            title_text = "COMBO RUSH - Défi de Multiplicateur par Étape"
            welcome_text = "Bienvenue au Mode Combo"
            instructions = (
                "Construisez votre score de combo par la précision et survivez à la complexité croissante !\n\n"
                "MÉCANIQUE DE NOTATION :\n"
                "- Bonne réponse : Double votre score de combo actuel\n"
                "- Mauvaise réponse : Divise votre score par 3\n"
                "- Dépassement : Réinitialise le score à 0,1\n"
                "- Plafond à 128 : Quand votre score atteint 128, il est automatiquement converti en XP et réinitialisé à 0,1\n\n"
                "PROGRESSION PAR ÉTAPE :\n"
                "• Étape 1 (5 min) : Caractères uniques\n"
                "• Étape 2 (5 min) : Combos de deux caractères\n"
                "• Étape 3 (5 min) : Combos de trois caractères\n"
                "• Optionnel : Continuer indéfiniment avec des combos plus longs pour des récompenses bonus\n\n"
                "CONVERSION XP :\n"
                "Après chaque bonne réponse, votre score de combo est converti en XP selon la difficulté de l'étape. "
                "Chaque étape augmente la conversion de 0,05 XP par point.\n"
                "Étape 1 : 0,05 XP par point | Étape 2 : 0,1 XP par point | Étape 3 : 0,15 XP par point\n\n"
                "RACCOURCIS CLAVIER :\n"
                "Ctrl : Répéter la cible | Maj+Ctrl : Statut | Maj+Entrée : Quitter\n\n"
                "ACHÈVEMENT :\n"
                "Terminez l'étape 3 avec ≥70 % de précision pour réussir et endommager le boss.\n"
                "Moins de 70 % : Réessayez plus tard. 70 % ou plus : +40 XP et -15 % de santé du boss !"
            )
            ready_text = "Je Suis Prêt"
            notyet_text = "Pas encore"

        title = AccessibleLabel(visual_text=title_text, accessible_text=title_text)
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #0fecb0; background-color: transparent; border: none; padding: 8px;")
        layout.addWidget(title)
        welcome = AccessibleLabel(visual_text=welcome_text, accessible_text=welcome_text)
        welcome.setStyleSheet("font-size: 18px; font-weight: bold; color: #e94560; background-color: transparent; border: none; padding: 4px;")
        layout.addWidget(welcome)
        inst_field = AccessibleBrowser(text=instructions, accessible_text=instructions)
        inst_field.setMinimumHeight(300)
        layout.addWidget(inst_field)
        btn_layout = QHBoxLayout()
        btn_ready = AccessiblePushButton(ready_text)
        btn_ready.clicked.connect(self._launch)
        btn_layout.addWidget(btn_ready)
        btn_notyet = AccessiblePushButton(notyet_text)
        btn_notyet.clicked.connect(self.close)
        btn_layout.addWidget(btn_notyet)
        layout.addLayout(btn_layout)
        layout.addStretch()
        self.setLayout(layout)

    def _launch(self):
        if hasattr(self.parent_challenge, 'launch_combo_session'):
            self.parent_challenge.launch_combo_session()
        self.close()


class ComboTypingMode(GenericTypingMode):
    def __init__(self, base_logic, is_english=True, parent=None):
        super().__init__(base_logic, mode_name="Combo Rush", is_english=is_english, parent=parent)
        self.session_duration = 999999
        self.current_stage = 1
        self.stage_start_time = None
        self.stage_duration = 300
        self.combo_score = 0.1
        self.highest_combo = 0.1
        self.total_session_xp = 0.0
        self.session_complete = False
        self.continue_challenge = False
        self.combo_csv_path = None
        self.session_accuracy = 0.0
        self.failed_mode = False
        self._tts_waiting = False

    def _setup_ui(self):
        layout = QVBoxLayout()
        if self.is_english:
            mode_label_text = "COMBO RUSH - Stage-Based Progression"
            instructions_text = "Type the combo as it appears. Build your streak and maximize score!\nCorrect: 2x score | Incorrect: ÷3 | Timeout: Reset to 0.1"
            xp_text = "XP Balance: 0"
            stage_text = "Stage: 1 - Single Character"
            score_text = "Combo Score: 0.1"
            timer_text = "Stage Time: 5:00"
            button_text = "Leave and Go Back to Challenge Battle"
        else:
            mode_label_text = "COMBO RUSH - Progression par Étape"
            instructions_text = "Tapez le combo au fur et à mesure. Construisez votre série et maximisez le score !\nCorrect : 2x score | Incorrect : ÷3 | Dépassement : Réinitialiser à 0,1"
            xp_text = "Solde XP : 0"
            stage_text = "Etape : 1 - Caractere Unique"
            score_text = "Score Combo : 0.1"
            timer_text = "Temps d'Étape : 5:00"
            button_text = "Quitter et Retourner au Combat de Défi"

        mode_title = AccessibleLabel(visual_text=mode_label_text, accessible_text=mode_label_text)
        mode_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #0fecb0; background-color: transparent; border: none; padding: 6px;")
        layout.addWidget(mode_title)
        self.instructions_display = AccessibleBrowser(text=instructions_text, accessible_text=instructions_text)
        self.instructions_display.setMinimumHeight(70)
        layout.addWidget(self.instructions_display)

        stats_layout1 = QHBoxLayout()
        self.xp_label = AccessibleLabel(visual_text=xp_text, accessible_text=xp_text)
        stats_layout1.addWidget(self.xp_label)
        self.stage_label = AccessibleLabel(visual_text=stage_text, accessible_text=stage_text)
        stats_layout1.addWidget(self.stage_label)
        layout.addLayout(stats_layout1)

        stats_layout2 = QHBoxLayout()
        self.combo_score_label = AccessibleLabel(visual_text=score_text, accessible_text=score_text)
        stats_layout2.addWidget(self.combo_score_label)
        self.timer_label = AccessibleLabel(visual_text=timer_text, accessible_text=timer_text)
        stats_layout2.addWidget(self.timer_label)
        layout.addLayout(stats_layout2)

        self.target_display = AccessibleLabel(visual_text="", accessible_text="Waiting for stage to start")
        self.target_display.setStyleSheet("font-size: 100px; color: #f9d342; border: 3px solid #f9d342; border-radius: 10px; background-color: #1a1a2e; padding: 8px; min-height: 160px;")
        layout.addWidget(self.target_display)

        self.input_field = ComboTypingInput(self)
        self.input_field.textChanged.connect(self._on_input_changed)
        layout.addWidget(self.input_field)

        btn_leave = AccessiblePushButton(button_text)
        btn_leave.clicked.connect(self.leave_session)
        layout.addWidget(btn_leave)
        self.setLayout(layout)

    def start_session(self):
        self.session_start_time = time.time()
        self.stage_start_time = time.time()
        self.current_stage = 1
        self.combo_score = 0.1
        self.highest_combo = 0.1
        self.total_session_xp = 0.0
        self.correct_count = 0
        self.incorrect_count = 0
        self.timeout_count = 0
        self.session_accuracy = 0.0
        self._init_combo_csv()
        self.session_timer.start(1000)
        self._next_target()
        if self.base_logic.speaker:
            msg = (f"Combo Mode started. Stage 1 begins. Type the character as it appears!" if self.is_english
                   else f"Mode Combo lancé. L'étape 1 commence. Tapez le caractère au fur et à mesure !")
            self.base_logic.speaker.output(msg)

    def _init_combo_csv(self):
        clean_name = self.base_logic.get_clean_username()
        user_dir = os.path.join(self.base_logic.data_dir, clean_name)
        os.makedirs(user_dir, exist_ok=True)
        self.combo_csv_path = os.path.join(user_dir, f"{clean_name}_Combo_Session_{int(time.time())}.csv")
        try:
            with open(self.combo_csv_path, 'w', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow(["Timestamp", "Generated Combo", "Result Status", "Response Time (s)", "Stage", "Current Combo Score"])
        except Exception:
            pass

    def _log_combo_attempt(self, combo, status, response_time, score_after_action):
        if not self.combo_csv_path:
            return
        try:
            with open(self.combo_csv_path, 'a', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow([
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    combo,
                    status,
                    round(response_time, 3) if status == "correct" else "!",
                    self.current_stage,
                    round(score_after_action, 2),
                ])
        except Exception:
            pass

    def get_random_target(self):
        lowercase = "abcdefghijklmnopqrstuvwxyz"
        uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        symbols = "".join(symbol_pronounciation.keys())
        char_pool = lowercase + uppercase + symbols
        combo_length = min(self.current_stage, 10)
        return "".join(random.choice(char_pool) for _ in range(combo_length))

    def _next_target(self):
        self.target_timer.stop()
        self._tts_waiting = False
        self.current_target = self.get_random_target()
        self.target_start_time = time.time()
        self.target_timeout = 3.0
        announcement = self._get_combo_announcement(self.current_target)
        self.target_display.update_text(self.current_target, announcement)
        self.input_field.textChanged.disconnect(self._on_input_changed)
        self.input_field.clear()
        self.input_field.textChanged.connect(self._on_input_changed)
        if self.current_stage == 1:
            if self.base_logic.speaker:
                self.base_logic.speaker.output(announcement)
            self.input_field.setEnabled(True)
            self.input_field.setFocus()
            self.target_timer.start(int(self.target_timeout * 1000))
        else:
            self.input_field.setEnabled(False)
            if self.base_logic.speaker:
                self.base_logic.speaker.output(announcement)
            delay = len(announcement) * 60 + 400
            QTimer.singleShot(delay, self._enable_combo_input)

    def _enable_combo_input(self):
        winsound.Beep(1000, 150)
        self.input_field.setEnabled(True)
        self.input_field.setFocus()
        self.target_start_time = time.time()
        self.target_timer.start(int(self.target_timeout * 1000))

    def _get_combo_announcement(self, combo):
        parts = []
        for char in combo:
            if char in symbol_pronounciation:
                parts.append(symbol_pronounciation[char])
            elif char.isupper():
                parts.append(_format_uppercase_announcement(char, self.is_english))
            else:
                parts.append(char)
        return ", ".join(parts)

    def _on_input_changed(self, text):
        if not text:
            return
        typed = text.strip()
        # Exactly matched
        if typed == self.current_target:
            self.target_timer.stop()
            typing_time = time.time() - self.target_start_time
            winsound.Beep(1500, 100)
            self.correct_count += 1
            self.combo_score = round(self.combo_score * 2, 2)
            if self.combo_score >= 128:
                multiplier = self.get_xp_multiplier(self.current_stage)
                xp_gained = round(int(self.combo_score) * multiplier, 1)
                self.total_session_xp += xp_gained
                self.xp_earned = self.total_session_xp
                self.combo_score = 0.1
                if self.base_logic.speaker:
                    msg = (f"Combo cap! {xp_gained} XP converted." if self.is_english else f"Plafond combo ! {xp_gained} XP convertis.")
                    self.base_logic.speaker.output(msg)
            if self.combo_score > self.highest_combo:
                self.highest_combo = self.combo_score
            self._log_combo_attempt(self.current_target, "correct", typing_time, self.combo_score)
            self._update_displays()
            self._next_target()
        # Mismatch when length equals target length (single char or full combo)
        elif len(text) == len(self.current_target) and typed != self.current_target:
            self.target_timer.stop()
            winsound.Beep(400, 200)
            self.incorrect_count += 1
            self.combo_score = max(0.1, round(self.combo_score / 3.0, 2))
            self._log_combo_attempt(self.current_target, "incorrect", None, self.combo_score)
            self._update_displays()
            self.input_field.textChanged.disconnect(self._on_input_changed)
            self.input_field.clear()
            self.input_field.textChanged.connect(self._on_input_changed)
            self._next_target()
        # Too many characters typed (only relevant for multi-char, but also catches over-typing)
        elif len(text) > len(self.current_target):
            self.target_timer.stop()
            winsound.Beep(400, 200)
            self.incorrect_count += 1
            self.combo_score = max(0.1, round(self.combo_score / 3.0, 2))
            self._log_combo_attempt(self.current_target, "incorrect", None, self.combo_score)
            self._update_displays()
            self.input_field.textChanged.disconnect(self._on_input_changed)
            self.input_field.clear()
            self.input_field.textChanged.connect(self._on_input_changed)
            self._next_target()
        # Else (prefix match) do nothing, allow typing

    def _on_target_timeout(self):
        winsound.Beep(600, 300)
        self.timeout_count += 1
        self.combo_score = 0.1
        self._log_combo_attempt(self.current_target, "timeout", None, self.combo_score)
        self._update_displays()
        self._next_target()

    def _update_session_timer(self):
        stage_elapsed = time.time() - self.stage_start_time
        stage_remaining = self.stage_duration - stage_elapsed
        if stage_remaining <= 0:
            self._convert_stage_xp()
            self._transition_stage()
            return
        m = int(stage_remaining) // 60
        s = int(stage_remaining) % 60
        v = f"Stage Time: {m}:{s:02d}" if self.is_english else f"Temps d'Étape : {m}:{s:02d}"
        a = (f"{m} minutes {s} seconds remaining in this stage" if self.is_english
             else f"{m} minutes {s} secondes restantes dans cette étape")
        self.timer_label.update_text(v, a)

    def _convert_stage_xp(self):
        multiplier = self.get_xp_multiplier(self.current_stage)
        xp_gained = round(int(self.combo_score) * multiplier, 1)
        self.total_session_xp += xp_gained
        self.xp_earned = self.total_session_xp
        self._update_displays()

    def _transition_stage(self):
        if self.current_stage < 3:
            self.current_stage += 1
            self.stage_start_time = time.time()
            self.combo_score = 0.1
            stage_names = {
                1: ("Stage 1 - Single Character", "Etape 1 - Caractere Unique"),
                2: ("Stage 2 - Two Character Combos", "Etape 2 - Combos de Deux Caracteres"),
                3: ("Stage 3 - Three Character Combos", "Etape 3 - Combos de Trois Caracteres"),
            }
            eng_name, fr_name = stage_names[self.current_stage]
            display_text = eng_name if self.is_english else fr_name
            self.stage_label.update_text(display_text, display_text)
            if self.base_logic.speaker:
                self.base_logic.speaker.output(f"Stage {self.current_stage} started!" if self.is_english else f"L'étape {self.current_stage} a commencé !")
            self._next_target()
        elif self.current_stage == 3:
            self._complete_mandatory_stages()
        else:
            self._complete_bonus_stage()

    def _complete_mandatory_stages(self):
        self.session_timer.stop()
        self.target_timer.stop()
        self.message_timer.stop()
        total = self.correct_count + self.incorrect_count
        self.session_accuracy = (self.correct_count / total * 100) if total > 0 else 0.0
        if self.session_accuracy < 70:
            self.failed_mode = True
            self._show_failure_page()
        else:
            self._show_stage3_complete_page()

    def _complete_bonus_stage(self):
        self.session_timer.stop()
        self.target_timer.stop()
        self.message_timer.stop()
        total = self.correct_count + self.incorrect_count
        self.session_accuracy = (self.correct_count / total * 100) if total > 0 else 0.0
        if self.is_english:
            title = f"STAGE {self.current_stage} COMPLETE"
            stats_text = (
                f"Stage Accuracy: {self.session_accuracy:.1f}%\n"
                f"Highest Combo This Stage: {self.highest_combo:.1f}\n"
                f"Total Session Accuracy: {self.session_accuracy:.1f}%\n\n"
                f"Bonus Stage Reward: +20 XP and -5% Boss Health earned.\n"
                f"Continue to Stage {self.current_stage + 1} for more rewards?"
            )
            btn_continue_text = f"Continue to Stage {self.current_stage + 1}"
            btn_return_text = "Exit and Return to Challenge Battle"
        else:
            title = f"ÉTAPE {self.current_stage} COMPLÈTE"
            stats_text = (
                f"Précision de l'Étape : {self.session_accuracy:.1f} %\n"
                f"Combo le Plus Élevé de cette Étape : {self.highest_combo:.1f}\n"
                f"Précision Totale de la Session : {self.session_accuracy:.1f} %\n\n"
                f"Récompense Étape Bonus : +20 XP et -5 % santé du Boss gagnés.\n"
                f"Continuer à l'étape {self.current_stage + 1} pour plus de récompenses ?"
            )
            btn_continue_text = f"Continuer à l'étape {self.current_stage + 1}"
            btn_return_text = "Quitter et Retourner au Combat de Défi"

        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setMinimumWidth(520)
        dlg.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout()
        title_label = AccessibleLabel(visual_text=title, accessible_text=title)
        title_label.setStyleSheet("font-size: 26px; font-weight: bold; color: #0fecb0; background-color: transparent; border: none; padding: 6px;")
        layout.addWidget(title_label)
        stats_browser = AccessibleBrowser(text=stats_text, accessible_text=stats_text)
        stats_browser.setMinimumHeight(220)
        layout.addWidget(stats_browser)
        btn_layout = QHBoxLayout()
        btn_continue = AccessiblePushButton(btn_continue_text)
        btn_continue.clicked.connect(self._continue_to_next_bonus_stage)
        btn_layout.addWidget(btn_continue)
        btn_return = AccessiblePushButton(btn_return_text)
        btn_return.clicked.connect(lambda: self._exit_bonus_stages(dlg))
        btn_layout.addWidget(btn_return)
        layout.addLayout(btn_layout)
        dlg.setLayout(layout)
        dlg.exec_()

    def _continue_to_next_bonus_stage(self):
        if self.parent_challenge and hasattr(self.parent_challenge, 'logic'):
            logic = self.parent_challenge.logic
            logic.add_xp(20)
            logic.boss_health = max(0, logic.boss_health - 5)
        self.combo_score = 0.1
        self.current_stage += 1
        self.highest_combo = 0.1
        self.stage_start_time = time.time()
        stage_names = {
            4: ("Stage 4 - Four Character Combos", "Etape 4 - Combos de Quatre Caracteres"),
            5: ("Stage 5 - Five Character Combos", "Etape 5 - Combos de Cinq Caracteres"),
        }
        eng_name, fr_name = stage_names.get(self.current_stage, (f"Stage {self.current_stage} - Bonus Challenge", f"Etape {self.current_stage} - Defi Bonus"))
        display_text = eng_name if self.is_english else fr_name
        self.stage_label.update_text(display_text, display_text)
        if self.base_logic.speaker:
            self.base_logic.speaker.output(f"Bonus Stage {self.current_stage} started!" if self.is_english else f"L'étape bonus {self.current_stage} a commencé !")
        self.session_timer.start(1000)
        self._next_target()

    def _exit_bonus_stages(self, dialog):
        dialog.accept()
        if self.parent_challenge and hasattr(self.parent_challenge, 'logic'):
            logic = self.parent_challenge.logic
            logic.add_xp(20)
            logic.boss_health = max(0, logic.boss_health - 5)
            logic.save_progress()
            self.parent_challenge.update_display()
        self._show_final_results_page()

    def _show_failure_page(self):
        if self.is_english:
            title = "ACCURACY TOO LOW"
            message = f"Final Accuracy: {self.session_accuracy:.1f}%\n\nYou need at least 70% accuracy to complete Combo Mode.\nPlease try again later!"
            button_text = "Return to Challenge Battle"
        else:
            title = "PRÉCISION INSUFFISANTE"
            message = f"Précision Finale : {self.session_accuracy:.1f} %\n\nVous avez besoin d'au moins 70 % de précision pour terminer le Mode Combo.\nVeuillez réessayer plus tard !"
            button_text = "Retour au Combat de Défi"

        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setMinimumWidth(520)
        dlg.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout()
        title_label = AccessibleLabel(visual_text=title, accessible_text=title)
        title_label.setStyleSheet("font-size: 26px; font-weight: bold; color: #e94560; background-color: transparent; border: none; padding: 6px;")
        layout.addWidget(title_label)
        msg_browser = AccessibleBrowser(text=message, accessible_text=message)
        msg_browser.setMinimumHeight(180)
        layout.addWidget(msg_browser)
        btn_return = AccessiblePushButton(button_text)
        btn_return.clicked.connect(lambda: self._return_to_challenge(dlg))
        layout.addWidget(btn_return)
        dlg.setLayout(layout)
        dlg.exec_()

    def _show_stage3_complete_page(self):
        if self.is_english:
            title = "STAGE 3 COMPLETE"
            stats_text = (
                f"Correct Answers: {self.correct_count}\n"
                f"Incorrect Answers: {self.incorrect_count}\n"
                f"Timeouts: {self.timeout_count}\n"
                f"Final Accuracy: {self.session_accuracy:.1f}%\n"
                f"Highest Combo Score: {self.highest_combo:.1f}\n"
                f"Total XP Earned: {int(self.total_session_xp)}\n\n"
                f"You passed! +40 XP and -15% Boss Health awarded.\n"
                f"Continue for bonus stages with longer combos and more XP?"
            )
            btn_continue_text = "Continue Combo Challenge (Bonus)"
            btn_return_text = "Return to Challenge Battle"
        else:
            title = "ÉTAPE 3 COMPLÈTE"
            stats_text = (
                f"Bonnes Réponses : {self.correct_count}\n"
                f"Mauvaises Réponses : {self.incorrect_count}\n"
                f"Dépassements : {self.timeout_count}\n"
                f"Précision Finale : {self.session_accuracy:.1f} %\n"
                f"Score Combo le Plus Élevé : {self.highest_combo:.1f}\n"
                f"XP Total Gagné : {int(self.total_session_xp)}\n\n"
                f"Vous avez réussi ! +40 XP et -15 % santé du Boss accordés.\n"
                f"Continuer pour les étapes bonus avec des combos plus longs et plus de XP ?"
            )
            btn_continue_text = "Continuer Défi Combo (Bonus)"
            btn_return_text = "Retour au Combat de Défi"

        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setMinimumWidth(520)
        dlg.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout()
        title_label = AccessibleLabel(visual_text=title, accessible_text=title)
        title_label.setStyleSheet("font-size: 26px; font-weight: bold; color: #0fecb0; background-color: transparent; border: none; padding: 6px;")
        layout.addWidget(title_label)
        stats_browser = AccessibleBrowser(text=stats_text, accessible_text=stats_text)
        stats_browser.setMinimumHeight(260)
        layout.addWidget(stats_browser)
        btn_layout = QHBoxLayout()
        btn_continue = AccessiblePushButton(btn_continue_text)
        btn_continue.clicked.connect(self._continue_to_next_bonus_stage)
        btn_layout.addWidget(btn_continue)
        btn_return = AccessiblePushButton(btn_return_text)
        btn_return.clicked.connect(lambda: self._end_session_and_return(dlg))
        btn_layout.addWidget(btn_return)
        layout.addLayout(btn_layout)
        dlg.setLayout(layout)
        dlg.exec_()

    def _end_session_and_return(self, dialog):
        dialog.accept()
        self._convert_stage_xp()
        self._update_challenge_state_success()
        self._show_final_results_page()

    def _update_displays(self):
        v = f"XP Balance: {int(self.xp_earned)}" if self.is_english else f"Solde XP : {int(self.xp_earned)}"
        a = f"{int(self.xp_earned)} XP earned" if self.is_english else f"{int(self.xp_earned)} XP gagnés"
        self.xp_label.update_text(v, a)
        v = f"Combo Score: {self.combo_score:.2f}" if self.is_english else f"Score Combo : {self.combo_score:.2f}"
        a = f"Current combo score is {self.combo_score:.2f}" if self.is_english else f"Le score de combo actuel est {self.combo_score:.2f}"
        self.combo_score_label.update_text(v, a)

    def get_xp_multiplier(self, stage):
        return 0.05 * stage

    def _update_challenge_state_success(self):
        if not (self.parent_challenge and hasattr(self.parent_challenge, 'logic')):
            return
        logic = self.parent_challenge.logic
        logic.add_xp(int(self.total_session_xp))
        logic.add_xp(40)
        logic.boss_health = max(0, logic.boss_health - 15)
        logic.modes["combo"]["status"] = "done"
        logic.modes["combo"]["completed"] = True
        logic.completed_modes_count = sum(1 for v in logic.modes.values() if v["completed"])
        for mk, data in logic.modes.items():
            if mk != "crazy_party" and not data["completed"]:
                data["status"] = "unlocked"
        logic.save_progress()
        self.parent_challenge.update_display()

    def _show_final_results_page(self):
        if self.is_english:
            title = "COMBO MODE COMPLETE"
            message = (
                f"Accuracy: {self.session_accuracy:.1f}%\n"
                f"Correct Answers: {self.correct_count}\n"
                f"Incorrect Answers: {self.incorrect_count}\n"
                f"Timeouts: {self.timeout_count}\n"
                f"Highest Combo: {self.highest_combo:.2f}\n"
                f"XP Earned: {int(self.xp_earned)}\n"
                f"Stages Completed: {self.current_stage}\n\n"
                f"Completion Bonus: +40 XP | Boss Damage: -15%"
            )
            button_text = "Return to Challenge Battle"
        else:
            title = "MODE COMBO COMPLET"
            message = (
                f"Précision : {self.session_accuracy:.1f} %\n"
                f"Bonnes Réponses : {self.correct_count}\n"
                f"Mauvaises Réponses : {self.incorrect_count}\n"
                f"Dépassements : {self.timeout_count}\n"
                f"Combo le Plus Élevé : {self.highest_combo:.2f}\n"
                f"XP Gagné : {int(self.xp_earned)}\n"
                f"Étapes Complétées : {self.current_stage}\n\n"
                f"Bonus d'Achèvement : +40 XP | Dommage Boss : -15 %"
            )
            button_text = "Retour au Combat de Défi"

        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setMinimumWidth(520)
        dlg.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout()
        title_label = AccessibleLabel(visual_text=title, accessible_text=title)
        title_label.setStyleSheet("font-size: 26px; font-weight: bold; color: #0fecb0; background-color: transparent; border: none; padding: 6px;")
        layout.addWidget(title_label)
        msg_browser = AccessibleBrowser(text=message, accessible_text=message)
        msg_browser.setMinimumHeight(240)
        layout.addWidget(msg_browser)
        btn_return = AccessiblePushButton(button_text)
        btn_return.clicked.connect(lambda: self._return_to_challenge(dlg))
        layout.addWidget(btn_return)
        dlg.setLayout(layout)
        dlg.exec_()

    def repeat_current_target(self):
        if not self.current_target:
            return
        is_multi = self.current_stage > 1 and len(self.current_target) > 1
        if is_multi:
            self._pause_timers()
            spelled = self._get_combo_announcement(self.current_target)
            if self.base_logic.speaker:
                self.base_logic.speaker.output(spelled)
            delay = len(spelled) * 65 + 400
            QTimer.singleShot(delay, self._resume_timers)
        else:
            ann = self._get_combo_announcement(self.current_target)
            if self.base_logic.speaker:
                self.base_logic.speaker.output(ann)

    def _pause_timers(self):
        self._tts_waiting = True
        self.session_timer.stop()
        self.target_timer.stop()

    def _resume_timers(self):
        if not self._tts_waiting:
            return
        self._tts_waiting = False
        if not self.session_timer.isActive():
            self.session_timer.start()
        self.target_timer.start(int(self.target_timeout * 1000))
        self.input_field.setFocus()

    def on_typing_key_pressed(self):
        if self._tts_waiting:
            self._resume_timers()

    def _on_shift_enter(self):
        self._pause_timers()
        self._show_exit_dialog()

    def _announce_status(self):
        self._pause_timers()
        stage_elapsed = time.time() - self.stage_start_time
        stage_remaining = self.stage_duration - stage_elapsed
        if stage_remaining < 0:
            stage_remaining = 0
        m = int(stage_remaining) // 60
        s = int(stage_remaining) % 60
        if self.is_english:
            msg = f"Combo score: {self.combo_score:.1f}. XP earned: {self.xp_earned:.1f}. Stage time remaining: {m} minutes {s} seconds."
        else:
            msg = f"Score combo : {self.combo_score:.1f}. XP gagnés : {self.xp_earned:.1f}. Temps restant dans l'étape : {m} minutes {s} secondes."
        if self.base_logic.speaker:
            self.base_logic.speaker.output(msg)
        delay = len(msg) * 100 + 500
        QTimer.singleShot(delay, self._resume_timers)

    def _show_exit_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Exit?" if self.is_english else "Quitter ?")
        dlg.setMinimumWidth(480)
        dlg.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout()
        msg_text = ("Exit Combo Rush?\n\nA 50 XP penalty will be applied and your session CSV will be deleted." if self.is_english
                    else "Quitter Combo Rush ?\n\nUne penalite de 50 XP sera appliquee et votre CSV de session sera supprime.")
        msg = AccessibleBrowser(text=msg_text, accessible_text=msg_text)
        layout.addWidget(msg)
        btn_row = QHBoxLayout()
        btn_yes = AccessiblePushButton("Yes, exit" if self.is_english else "Oui, quitter")
        btn_no = AccessiblePushButton("No, continue" if self.is_english else "Non, continuer")
        btn_yes.clicked.connect(dlg.accept)
        btn_no.clicked.connect(dlg.reject)
        btn_row.addWidget(btn_yes)
        btn_row.addWidget(btn_no)
        layout.addLayout(btn_row)
        dlg.setLayout(layout)
        if dlg.exec_() == QDialog.Accepted:
            self.leave_session()
        else:
            self._resume_timers()

    def leave_session(self):
        self.session_timer.stop()
        self.target_timer.stop()
        self.message_timer.stop()
        if self.combo_csv_path and os.path.exists(self.combo_csv_path):
            try:
                os.remove(self.combo_csv_path)
            except Exception:
                pass
        if self.parent_challenge and hasattr(self.parent_challenge, 'logic'):
            logic = self.parent_challenge.logic
            logic.xp_balance = max(0, logic.xp_balance - 50)
            logic.save_progress()
            self.parent_challenge.update_display()
        if self.base_logic.speaker:
            msg = ("Combo session exited. 50 XP penalty applied." if self.is_english else "Session Combo quittée. Pénalité de 50 XP appliquée.")
            self.base_logic.speaker.output(msg)
        if self.parent_challenge:
            self.parent_challenge.pages.setCurrentIndex(1)
        self.close()

    def _return_to_challenge(self, dialog):
        dialog.accept()
        if self.parent_challenge:
            self.parent_challenge.pages.setCurrentIndex(1)
            self.parent_challenge.update_display()
        self.close()

    def closeEvent(self, event):
        if not self.session_start_time or not self.session_timer.isActive():
            event.accept()
            return
        self.session_timer.stop()
        self.target_timer.stop()
        self.message_timer.stop()
        self._show_exit_dialog()
        event.ignore()


# ============= PRECISION ARENA =============

class PrecisionWelcomePage(QWidget):
    def __init__(self, parent, is_english=True):
        super().__init__()
        self.parent_challenge = parent
        self.is_english = is_english
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        if self.is_english:
            title_text   = "PRECISION ARENA - Accuracy Marathon"
            instructions = (
                "7 minutes of nonstop typing. No timeouts.\n\n"
                "HOW IT WORKS:\n"
                "Type each target exactly as shown. It validates automatically once you "
                "have typed enough characters. Wrong answer? You move on immediately. "
                "This is an arena, not a classroom.\n\n"
                "TWO PHASES:\n"
                "First 4 minutes: random characters.\n"
                "Final 3 minutes: adapts to your weakest letters based on your history.\n\n"
                "MEDALS (accuracy required):\n"
                "Bronze: 91% | Silver: 93% | Gold: 95% | Diamond: 97% | Master: 99%\n\n"
                "SPEED REQUIREMENT:\n"
                "You also need at least 20 CPM. Medal still shows if accuracy qualifies, "
                "but is only officially granted if speed qualifies too.\n\n"
                "REWARDS on success: +50 XP, -15% boss health, plus medal bonus XP.\n"
                "Failed run: retry anytime. Progress is always saved."
            )
            ready_text  = "I'm ready for it!"
            notyet_text = "Not Yet"
        else:
            title_text   = "PRECISION ARENA - Marathon de Precision"
            instructions = (
                "7 minutes de frappe continue. Pas de delai.\n\n"
                "COMMENT CA MARCHE :\n"
                "Tapez chaque cible exactement. La validation est automatique des que vous "
                "avez assez de caracteres. Mauvaise reponse ? On passe immediatement. "
                "C'est une arene, pas une salle de classe.\n\n"
                "DEUX PHASES :\n"
                "4 premieres minutes : caracteres aleatoires.\n"
                "3 dernieres minutes : s'adapte a vos lettres les plus faibles.\n\n"
                "MEDAILLES (precision requise) :\n"
                "Bronze : 91% | Argent : 93% | Or : 95% | Diamant : 97% | Maitre : 99%\n\n"
                "EXIGENCE DE VITESSE :\n"
                "Vous avez aussi besoin d'au moins 20 CPM. La medaille s'affiche si la "
                "precision qualifie, mais ne compte que si la vitesse aussi.\n\n"
                "Reussite : +50 XP, -15% sante boss, plus XP bonus de medaille.\n"
                "Echec : recommencez quand vous voulez."
            )
            ready_text  = "Je suis pret !"
            notyet_text = "Pas encore"

        title = AccessibleLabel(visual_text=title_text, accessible_text=title_text)
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #0fecb0; background-color: transparent; border: none; padding: 8px;")
        layout.addWidget(title)
        inst_field = AccessibleBrowser(text=instructions, accessible_text=instructions)
        inst_field.setMinimumHeight(380)
        layout.addWidget(inst_field)
        btn_layout = QHBoxLayout()
        btn_ready = AccessiblePushButton(ready_text)
        btn_ready.clicked.connect(self._launch)
        btn_layout.addWidget(btn_ready)
        btn_notyet = AccessiblePushButton(notyet_text)
        btn_notyet.clicked.connect(self.close)
        btn_layout.addWidget(btn_notyet)
        layout.addLayout(btn_layout)
        layout.addStretch()
        self.setLayout(layout)

    def _launch(self):
        if hasattr(self.parent_challenge, 'launch_precision_session'):
            self.parent_challenge.launch_precision_session()
        self.close()


class PrecisionArenaMode(QWidget):
    SESSION_DURATION = 420
    ADAPTIVE_START   = 240
    MEDALS = [
        ("master",  99, "static/mtr.png", 150),
        ("diamond", 97, "static/dmd.png", 100),
        ("gold",    95, "static/gld.png",  50),
        ("silver",  93, "static/slv.png",  50),
        ("bronze",  91, "static/bnz.png",  25),
    ]
    FOUR_CHAR_WORDS = [
        "chat", "main", "pied", "nuit", "jour", "lune", "rose", "bleu",
        "vert", "noir", "gris", "beau", "fort", "vrai", "faux", "bois",
        "parc", "port", "pont", "tour", "dame", "vent", "sage", "seul",
        "fond", "aide", "chef", "ciel", "clef", "coup", "dent", "doux",
        "drap", "feux", "fils", "flot", "four", "gare", "gout", "gros",
        "lait", "lame", "lien", "lieu", "lion", "lire", "loup", "luxe",
        "miel", "mois", "mort", "naif", "nain", "neuf", "noix", "note",
        "once", "ours", "page", "pain", "paon", "part", "peur", "pile",
        "plan", "plat", "pois", "polo", "pore", "pose", "prix", "prof",
        "puce", "race", "rage", "raid", "rail", "rang", "rime", "ring",
        "rire", "rive", "robe", "rock", "role", "rond", "roue", "roux",
        "rude", "ruse", "sain", "sale", "sang", "saut", "sein", "sens",
        "sire", "site", "soie", "soir", "sole", "sort", "sous", "surf",
        "tact", "taux", "taxi", "toit", "tome", "tort", "trek", "trio",
        "trop", "tube", "type", "vain", "veau", "velo", "vers", "vice",
        "vide", "viol", "vite", "voie", "vote", "yoga", "zinc", "zone",
    ]

    def __init__(self, base_logic, is_english=True, parent=None):
        super().__init__()
        self.base_logic = base_logic
        self.is_english = is_english
        self.parent_challenge = parent
        self.session_elapsed = 0
        self.current_target = ""
        self.current_phase = "random"
        self.correct_chars = 0
        self.incorrect_chars = 0
        self.four_char_pool = []
        self.phase_weights_built = False
        self.session_letter_stats = {}
        self.adaptive_weights = {}
        self.precision_csv_path = None
        self.precision_history_path = None
        self.warmup_history_path = None
        self._announcement_paused = False
        self._setup_ui()
        self._setup_timer()

    def _setup_ui(self):
        layout = QVBoxLayout()
        if self.is_english:
            title_text = "PRECISION ARENA - Accuracy Marathon"
            instructions = "7 minutes nonstop. No timeouts. Type the target - validates automatically.\nFirst 4 min: random. Final 3 min: adapts to your weak letters."
            correct_v = "Correct Chars: 0"
            incorrect_v = "Incorrect Chars: 0"
            accuracy_v = "Accuracy: ?"
            timer_v = "Remaining: 7:00"
            button_text = "Leave and Go Back to Challenge Battle"
        else:
            title_text = "PRECISION ARENA - Marathon de Precision"
            instructions = "7 minutes sans arret. Pas de delai. Tapez la cible - validation automatique.\n4 min aleatoires. 3 dernieres min : s'adapte a vos lettres faibles."
            correct_v = "Caracteres Corrects : 0"
            incorrect_v = "Caracteres Incorrects : 0"
            accuracy_v = "Precision : ?"
            timer_v = "Restant : 7:00"
            button_text = "Quitter et Retourner au Combat de Defi"

        mode_title = AccessibleLabel(visual_text=title_text, accessible_text=title_text)
        mode_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #0fecb0; background-color: transparent; border: none; padding: 6px;")
        layout.addWidget(mode_title)
        self.instructions_display = AccessibleBrowser(text=instructions, accessible_text=instructions)
        self.instructions_display.setMinimumHeight(70)
        layout.addWidget(self.instructions_display)

        stats1 = QHBoxLayout()
        self.correct_label = AccessibleLabel(visual_text=correct_v, accessible_text=correct_v)
        stats1.addWidget(self.correct_label)
        self.incorrect_label = AccessibleLabel(visual_text=incorrect_v, accessible_text=incorrect_v)
        stats1.addWidget(self.incorrect_label)
        layout.addLayout(stats1)

        stats2 = QHBoxLayout()
        acc_accessible = ("Accuracy hidden until adaptive phase." if self.is_english else "Precision masquee jusqu'a la phase adaptative.")
        self.accuracy_label = AccessibleLabel(visual_text=accuracy_v, accessible_text=acc_accessible)
        stats2.addWidget(self.accuracy_label)
        self.timer_label = AccessibleLabel(visual_text=timer_v, accessible_text=timer_v)
        stats2.addWidget(self.timer_label)
        layout.addLayout(stats2)

        self.target_display = AccessibleLabel(visual_text="", accessible_text="Waiting for session to start")
        self.target_display.setStyleSheet("font-size: 110px; color: #f9d342; border: 3px solid #f9d342; border-radius: 10px; background-color: #1a1a2e; padding: 8px; min-height: 160px;")
        layout.addWidget(self.target_display)

        self.input_field = ChallengeTypingInput(self)
        self.input_field.textChanged.connect(self._on_input_changed)
        layout.addWidget(self.input_field)

        btn_leave = AccessiblePushButton(button_text)
        btn_leave.clicked.connect(self.leave_session)
        layout.addWidget(btn_leave)
        self.setLayout(layout)

    def _setup_timer(self):
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self._tick)

    def start_session(self):
        self.session_elapsed = 0
        self.correct_chars = 0
        self.incorrect_chars = 0
        self.current_phase = "random"
        self.phase_weights_built = False
        self.session_letter_stats = {}
        self.four_char_pool = list(self.FOUR_CHAR_WORDS)
        random.shuffle(self.four_char_pool)
        self._init_paths()
        self._init_precision_csv()
        self._refresh_stats_display()
        self.session_timer.start(1000)
        self._next_target()
        if self.base_logic.speaker:
            msg = ("Precision Arena started. Focus on accuracy!" if self.is_english else "Precision Arena demarree. Concentrez-vous sur la precision !")
            self.base_logic.speaker.output(msg)

    def _init_paths(self):
        clean_name = self.base_logic.get_clean_username()
        user_dir = os.path.join(self.base_logic.data_dir, clean_name)
        os.makedirs(user_dir, exist_ok=True)
        self.precision_csv_path = os.path.join(user_dir, f"{clean_name}_Precision_Arena_Session.csv")
        self.precision_history_path = os.path.join(user_dir, f"{clean_name}_Precision_Arena_History.csv")
        self.warmup_history_path = os.path.join(user_dir, f"{clean_name}_Warmup_Session.csv")

    def _init_precision_csv(self):
        if not self.precision_csv_path:
            return
        try:
            with open(self.precision_csv_path, 'w', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow([
                    "Timestamp", "Target", "Typed Input", "Correct",
                    "Target Length", "Running Accuracy", "Phase",
                    "Session Minute", "Cumulative Correct Chars", "Cumulative Incorrect Chars",
                ])
        except Exception:
            pass

    def _log_attempt(self, target, typed_input, correct):
        total = self.correct_chars + self.incorrect_chars
        running_acc = (self.correct_chars / total * 100) if total > 0 else 0.0
        minute = min(7, self.session_elapsed // 60 + 1)
        row = [
            time.strftime("%Y-%m-%d %H:%M:%S"),
            target, typed_input, str(correct),
            len(target), f"{running_acc:.1f}",
            self.current_phase, minute,
            self.correct_chars, self.incorrect_chars,
        ]
        for path in (self.precision_csv_path, self.precision_history_path):
            if not path:
                continue
            try:
                file_exists = os.path.exists(path)
                with open(path, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow([
                            "Timestamp", "Target", "Typed Input", "Correct",
                            "Target Length", "Running Accuracy", "Phase",
                            "Session Minute", "Cumulative Correct Chars", "Cumulative Incorrect Chars",
                        ])
                    writer.writerow(row)
            except Exception:
                pass

    def _generate_target(self):
        lengths = [1, 2, 3, 4]
        length = random.choices(lengths, weights=[33, 43, 17, 7], k=1)[0]
        if length == 4:
            if self.four_char_pool:
                return self.four_char_pool.pop()
            else:
                length = 3
        return "".join(self._pick_char() for _ in range(length))

    def _pick_char(self):
        if random.random() < 0.05 and symbol_pronounciation:
            return random.choice(list(symbol_pronounciation.keys()))
        letters = [chr(c) for c in range(ord('a'), ord('z') + 1)]
        if self.current_phase == "adaptive" and self.adaptive_weights:
            weights = [self.adaptive_weights.get(l, 4) for l in letters]
            base_letter = random.choices(letters, weights=weights, k=1)[0]
        else:
            base_letter = random.choice(letters)
        return base_letter.upper() if random.random() < 0.5 else base_letter

    def _get_char_announcement(self, char):
        if char in symbol_pronounciation:
            return symbol_pronounciation[char]
        if char.isupper() and char.isalpha():
            return _format_uppercase_announcement(char, self.is_english)
        return char

    def _next_target(self):
        self.current_target = self._generate_target()
        char_announcements = [self._get_char_announcement(c) for c in self.current_target]
        announcement = ", ".join(char_announcements)
        self.target_display.update_text(self.current_target, announcement)
        self.input_field.textChanged.disconnect(self._on_input_changed)
        self.input_field.clear()
        self.input_field.textChanged.connect(self._on_input_changed)
        if len(self.current_target) == 1:
            if self.base_logic.speaker:
                self.base_logic.speaker.output(announcement)
            self.input_field.setEnabled(True)
            self.input_field.setFocus()
        else:
            self.input_field.setEnabled(False)
            if self.base_logic.speaker:
                self.base_logic.speaker.output(announcement)
            total_ann_len = sum(len(a) for a in char_announcements)
            delay = total_ann_len * 65 + 400
            QTimer.singleShot(delay, self._enable_input_with_beep)

    def _enable_input_with_beep(self):
        winsound.Beep(1000, 100)
        self.input_field.setEnabled(True)
        self.input_field.setFocus()

    def _on_input_changed(self, text):
        if not text or not self.current_target:
            return
        if len(text) < len(self.current_target):
            return
        typed = text[:len(self.current_target)]
        self.input_field.textChanged.disconnect(self._on_input_changed)
        self.input_field.clear()
        self.input_field.textChanged.connect(self._on_input_changed)
        was_correct = (typed == self.current_target)
        if was_correct:
            winsound.Beep(1500, 100)
            self.correct_chars += len(self.current_target)
        else:
            winsound.Beep(400, 200)
            self.incorrect_chars += len(self.current_target)
        if self.current_phase == "random":
            for char in self.current_target:
                if char.isalpha() and char not in symbol_pronounciation:
                    key = char.upper()
                    rec = self.session_letter_stats.setdefault(key, {"correct": 0, "total": 0})
                    rec["total"] += 1
                    if was_correct:
                        rec["correct"] += 1
        self._log_attempt(self.current_target, typed, was_correct)
        self._refresh_stats_display()
        self.input_field.setFocus()
        self._next_target()

    def _refresh_stats_display(self):
        v = (f"Correct Chars: {self.correct_chars}" if self.is_english else f"Caracteres Corrects : {self.correct_chars}")
        a = (f"Correct characters: {self.correct_chars}" if self.is_english else f"Caracteres corrects : {self.correct_chars}")
        self.correct_label.update_text(v, a)
        v = (f"Incorrect Chars: {self.incorrect_chars}" if self.is_english else f"Caracteres Incorrects : {self.incorrect_chars}")
        a = (f"Incorrect characters: {self.incorrect_chars}" if self.is_english else f"Caracteres incorrects : {self.incorrect_chars}")
        self.incorrect_label.update_text(v, a)
        if self.session_elapsed < self.ADAPTIVE_START:
            v = "Accuracy: ?" if self.is_english else "Precision : ?"
            a = ("Accuracy hidden until adaptive phase." if self.is_english else "Precision masquee jusqu'a la phase adaptative.")
        else:
            total = self.correct_chars + self.incorrect_chars
            acc = (self.correct_chars / total * 100) if total > 0 else 0.0
            v = f"Accuracy: {acc:.1f}%" if self.is_english else f"Precision : {acc:.1f}%"
            a = f"Current accuracy: {acc:.1f} percent" if self.is_english else f"Precision actuelle : {acc:.1f} pourcent"
        self.accuracy_label.update_text(v, a)

    def _tick(self):
        self.session_elapsed += 1
        remaining = self.SESSION_DURATION - self.session_elapsed
        if remaining <= 0:
            self._end_session()
            return
        if self.session_elapsed >= self.ADAPTIVE_START and not self.phase_weights_built:
            self._build_adaptive_weights()
            self.current_phase = "adaptive"
            if self.base_logic.speaker:
                msg = ("Adaptive phase started. Focusing on your weak letters." if self.is_english else "Phase adaptative demarree. Concentration sur vos lettres faibles.")
                self.base_logic.speaker.output(msg)
        m = remaining // 60
        s = remaining % 60
        v = f"Remaining: {m}:{s:02d}" if self.is_english else f"Restant : {m}:{s:02d}"
        a = f"{m} minutes {s} seconds remaining" if self.is_english else f"{m} minutes {s} secondes restantes"
        self.timer_label.update_text(v, a)
        self._refresh_stats_display()

    def _build_adaptive_weights(self):
        merged = {}
        for path in (self.warmup_history_path, self.precision_history_path):
            for letter, acc in self._load_char_accuracy(path).items():
                merged.setdefault(letter, []).append(acc)
        for letter, counts in self.session_letter_stats.items():
            if counts["total"] > 0:
                acc = counts["correct"] / counts["total"]
                merged.setdefault(letter, []).append(acc)
        letters = [chr(c) for c in range(ord('a'), ord('z') + 1)]
        for letter in letters:
            key = letter.upper()
            if key in merged and merged[key]:
                avg_acc = sum(merged[key]) / len(merged[key])
            else:
                avg_acc = 0.88
            self.adaptive_weights[letter] = max(1, min(int((1.0 - avg_acc) * 22) + 1, 20))
        self.phase_weights_built = True

    def _load_char_accuracy(self, csv_path):
        result = {}
        if not csv_path or not os.path.exists(csv_path):
            return result
        try:
            counts = {}
            with open(csv_path, 'r', newline='', encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    target = row.get("Target", "")
                    correct_raw = row.get("Correct", "False").strip().lower()
                    correct = correct_raw in ("true", "1", "yes", "correct")
                    for char in target:
                        key = char.upper()
                        if key.isalpha() and char not in symbol_pronounciation:
                            rec = counts.setdefault(key, {"correct": 0, "total": 0})
                            rec["total"] += 1
                            if correct:
                                rec["correct"] += 1
            for letter, rec in counts.items():
                if rec["total"] > 0:
                    result[letter] = rec["correct"] / rec["total"]
        except Exception:
            pass
        return result

    def _end_session(self):
        self.session_timer.stop()
        self.input_field.setEnabled(False)
        total_chars = self.correct_chars + self.incorrect_chars
        accuracy = (self.correct_chars / total_chars * 100) if total_chars > 0 else 0.0
        cpm = total_chars / 7.0
        medal = medal_path = None
        medal_xp = 0
        for m_key, m_thresh, m_file, m_xp in self.MEDALS:
            if accuracy >= m_thresh:
                medal = m_key
                medal_path = m_file
                medal_xp = m_xp
                break
        granted = (medal is not None) and (cpm >= 20)
        passed = granted
        base_xp = 50 if medal else 0
        earned_xp = base_xp + medal_xp
        if medal and not granted:
            earned_xp = earned_xp // 2
        if not medal:
            earned_xp = 0
        boss_damage = 15 if granted else 0
        self._update_challenge_state(earned_xp, boss_damage, passed)
        self._show_results(accuracy, cpm, medal, medal_path, granted, earned_xp, boss_damage, passed)

    def _update_challenge_state(self, earned_xp, boss_damage, passed):
        if not (self.parent_challenge and hasattr(self.parent_challenge, 'logic')):
            return
        logic = self.parent_challenge.logic
        if earned_xp > 0:
            logic.add_xp(earned_xp)
        if boss_damage > 0:
            logic.boss_health = max(0, logic.boss_health - boss_damage)
        if passed:
            logic.modes["precision"]["status"] = "done"
            logic.modes["precision"]["completed"] = True
            logic.completed_modes_count = sum(1 for v in logic.modes.values() if v["completed"])
            for mk, data in logic.modes.items():
                if mk != "crazy_party" and not data["completed"]:
                    data["status"] = "unlocked"
        logic.save_progress()
        self.parent_challenge.update_display()

    def _show_results(self, accuracy, cpm, medal, medal_path, granted, earned_xp, boss_damage, passed):
        medal_display = {"bronze": "Bronze", "silver": "Silver", "gold": "Gold", "diamond": "Diamond", "master": "Master"}
        if self.is_english:
            title = "PRECISION ARENA RESULTS"
            correct_text = f"Correct Characters: {self.correct_chars}"
            incorrect_text = f"Incorrect Characters: {self.incorrect_chars}"
            acc_text = f"Final Accuracy: {accuracy:.1f}%"
            cpm_text = f"Final CPM: {cpm:.1f}"
            medal_text = f"Medal: {medal_display.get(medal, 'None')}"
            grant_text = ("Medal Granted" if granted else ("Not Granted - CPM too low" if medal else "No Medal - below 91%"))
            xp_text = f"XP Earned: {earned_xp}"
            boss_text = f"Boss Health: -{boss_damage}%" if boss_damage else "Boss Health: no change"
            state_text = "PASSED" if passed else "FAILED - retry to earn full rewards"
            retry_text = "Retry"
            return_text = "Return to Challenge Battle"
            go_back_text = "Go Back to Challenge Battle"
        else:
            title = "RESULTATS PRECISION ARENA"
            correct_text = f"Caracteres Corrects : {self.correct_chars}"
            incorrect_text = f"Caracteres Incorrects : {self.incorrect_chars}"
            acc_text = f"Precision Finale : {accuracy:.1f}%"
            cpm_text = f"CPM Final : {cpm:.1f}"
            medal_text = f"Medaille : {medal_display.get(medal, 'Aucune')}"
            grant_text = ("Medaille Accordee" if granted else ("Non Accordee - CPM insuffisant" if medal else "Aucune Medaille - sous 91%"))
            xp_text = f"XP Gagnes : {earned_xp}"
            boss_text = f"Sante Boss : -{boss_damage}%" if boss_damage else "Sante Boss : pas de changement"
            state_text = "REUSSI" if passed else "ECHOUE - recommencez pour les recompenses"
            retry_text = "Recommencer"
            return_text = "Retour au Combat de Defi"
            go_back_text = "Retour au Combat de Defi"

        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setMinimumWidth(560)
        dlg.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout()
        title_label = AccessibleLabel(visual_text=title, accessible_text=title)
        title_label.setStyleSheet("font-size: 26px; font-weight: bold; color: #0fecb0; background-color: transparent; border: none; padding: 6px;")
        layout.addWidget(title_label)
        stats_text = "\n".join([correct_text, incorrect_text, acc_text, cpm_text, medal_text, grant_text, xp_text, boss_text, state_text])
        stats_browser = AccessibleBrowser(text=stats_text, accessible_text=stats_text)
        stats_browser.setMinimumHeight(260)
        layout.addWidget(stats_browser)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        if medal and medal_path:
            full_path = os.path.join(base_dir, medal_path)
            if os.path.exists(full_path):
                pix = QPixmap(full_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_label.setPixmap(pix)
            else:
                icon_label.setFixedSize(60, 60)
                icon_label.setStyleSheet("background-color: #333;")
        else:
            icon_label.setFixedSize(40, 40)
            icon_label.setStyleSheet("background-color: black;")
        layout.addWidget(icon_label)
        btn_row = QHBoxLayout()
        if not passed:
            btn_retry = AccessiblePushButton(retry_text)
            btn_retry.clicked.connect(lambda: self._retry(dlg))
            btn_row.addWidget(btn_retry)
            btn_back = AccessiblePushButton(return_text)
            btn_back.clicked.connect(lambda: self._close_and_return(dlg))
            btn_row.addWidget(btn_back)
        else:
            btn_go = AccessiblePushButton(go_back_text)
            btn_go.clicked.connect(lambda: self._close_and_return(dlg))
            btn_row.addWidget(btn_go)
        layout.addLayout(btn_row)
        dlg.setLayout(layout)
        dlg.exec_()

    def _retry(self, dialog):
        dialog.accept()
        self.session_elapsed = 0
        self.correct_chars = 0
        self.incorrect_chars = 0
        self.current_phase = "random"
        self.phase_weights_built = False
        self.session_letter_stats = {}
        self.four_char_pool = list(self.FOUR_CHAR_WORDS)
        random.shuffle(self.four_char_pool)
        self._init_precision_csv()
        self._refresh_stats_display()
        self.input_field.setEnabled(True)
        self.session_timer.start(1000)
        self._next_target()

    def _close_and_return(self, dialog):
        dialog.accept()
        if self.parent_challenge:
            self.parent_challenge.pages.setCurrentIndex(1)
            self.parent_challenge.update_display()
        self.close()

    def repeat_current_target(self):
        if not self.current_target:
            return
        char_announcements = [self._get_char_announcement(c) for c in self.current_target]
        ann = ", ".join(char_announcements)
        if self.base_logic.speaker:
            self.base_logic.speaker.output(ann)

    def _pause_timers(self):
        if not self._announcement_paused:
            self._announcement_paused = True
            self.session_timer.stop()

    def _resume_timers(self):
        if self._announcement_paused:
            self._announcement_paused = False
            if not self.session_timer.isActive() and self.session_elapsed < self.SESSION_DURATION:
                self.session_timer.start(1000)

    def on_typing_key_pressed(self):
        if self._announcement_paused:
            self._resume_timers()

    def _on_shift_enter(self):
        self._pause_timers()
        remaining = self.SESSION_DURATION - self.session_elapsed
        if remaining < 0:
            remaining = 0
        m = remaining // 60
        s = remaining % 60
        total_chars = self.correct_chars + self.incorrect_chars
        if total_chars > 0 and self.session_elapsed >= self.ADAPTIVE_START:
            acc = (self.correct_chars / total_chars) * 100
            acc_text = f"{acc:.1f}%"
        else:
            acc_text = "?" if self.is_english else "?"
        if self.is_english:
            msg = f"Accuracy: {acc_text}. Time remaining: {m} minutes {s} seconds."
        else:
            msg = f"Précision : {acc_text}. Temps restant : {m} minutes {s} secondes."
        if self.base_logic.speaker:
            self.base_logic.speaker.output(msg)
        self._show_exit_dialog()

    def _announce_status(self):
        self._pause_timers()
        remaining = self.SESSION_DURATION - self.session_elapsed
        if remaining < 0:
            remaining = 0
        m = remaining // 60
        s = remaining % 60
        total_chars = self.correct_chars + self.incorrect_chars
        if total_chars > 0 and self.session_elapsed >= self.ADAPTIVE_START:
            acc = (self.correct_chars / total_chars) * 100
            acc_text = f"{acc:.1f}%"
        else:
            acc_text = "?" if self.is_english else "?"
        if self.is_english:
            msg = f"Accuracy: {acc_text}. Time remaining: {m} minutes {s} seconds."
        else:
            msg = f"Précision : {acc_text}. Temps restant : {m} minutes {s} secondes."
        if self.base_logic.speaker:
            self.base_logic.speaker.output(msg)
        delay = len(msg) * 100 + 500
        QTimer.singleShot(delay, self._resume_timers)

    def _show_exit_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Exit?" if self.is_english else "Quitter ?")
        dlg.setMinimumWidth(480)
        dlg.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout()
        msg_text = ("Exit Precision Arena?\n\nA 50 XP penalty will be applied. Your history CSV is kept." if self.is_english
                    else "Quitter Precision Arena ?\n\nUne penalite de 50 XP sera appliquee. Votre historique CSV est conserve.")
        msg = AccessibleBrowser(text=msg_text, accessible_text=msg_text)
        layout.addWidget(msg)
        btn_row = QHBoxLayout()
        btn_yes = AccessiblePushButton("Yes, exit" if self.is_english else "Oui, quitter")
        btn_no = AccessiblePushButton("No, continue" if self.is_english else "Non, continuer")
        btn_yes.clicked.connect(dlg.accept)
        btn_no.clicked.connect(dlg.reject)
        btn_row.addWidget(btn_yes)
        btn_row.addWidget(btn_no)
        layout.addLayout(btn_row)
        dlg.setLayout(layout)
        if dlg.exec_() == QDialog.Accepted:
            self.leave_session()
        else:
            self._resume_timers()

    def leave_session(self):
        self.session_timer.stop()
        self.input_field.setEnabled(False)
        if self.precision_csv_path and os.path.exists(self.precision_csv_path):
            try:
                os.remove(self.precision_csv_path)
            except Exception:
                pass
        if self.parent_challenge and hasattr(self.parent_challenge, 'logic'):
            logic = self.parent_challenge.logic
            logic.xp_balance = max(0, logic.xp_balance - 50)
            logic.save_progress()
            self.parent_challenge.update_display()
        if self.base_logic.speaker:
            msg = ("Precision Arena exited. 50 XP penalty applied." if self.is_english else "Precision Arena quittee. Penalite de 50 XP appliquee.")
            self.base_logic.speaker.output(msg)
        if self.parent_challenge:
            self.parent_challenge.pages.setCurrentIndex(1)
        self.close()

    def closeEvent(self, event):
        if not hasattr(self, 'session_elapsed') or self.session_elapsed >= self.SESSION_DURATION:
            event.accept()
            return
        self.session_timer.stop()
        self.input_field.setEnabled(False)
        self._show_exit_dialog()
        event.ignore()


# ============= CRAZY PARTY =============

class CrazyPartyTypingInput(QLineEdit):
    def __init__(self, mode, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = mode

    def keyPressEvent(self, event):
        # Ctrl alone: repeat target
        if event.key() == Qt.Key_Control and event.modifiers() == Qt.ControlModifier:
            self.mode.repeat_current_target()
            return
        # Shift+Enter: exit
        if (event.key() in (Qt.Key_Return, Qt.Key_Enter) and event.modifiers() & Qt.ShiftModifier):
            self.mode._on_shift_enter()
            return
        # Shift+Ctrl: status
        if (event.key() == Qt.Key_Control and event.modifiers() & Qt.ShiftModifier):
            self.mode._announce_status()
            return
        # Any other key: interrupt TTS
        self.mode.on_typing_key_pressed()
        super().keyPressEvent(event)


class CrazyParty(QWidget):
    TICKET_COST = 100
    SAFE_ZONE_XP = 100
    WORD_INTERVAL = 100

    def __init__(self, base_logic, is_english=True, parent=None):
        super().__init__()
        self.setWindowFlag(Qt.Window, True)
        self.setWindowModality(Qt.ApplicationModal)
        self.base_logic = base_logic
        self.is_english = is_english
        self.parent_challenge = parent
        self.current_hearts = 5
        self.current_danger = 0
        self.elapsed_seconds = 0
        self.current_target = ""
        self.target_count = 0
        self.countdown_value = 3
        self.session_xp_earned = 0.0
        self.ticket_refunded = False
        self.xp_per_correct = 0.01
        self.correct_streak = 0
        self.error_streak = 0
        self._tts_waiting = False
        self._tts_timers = []
        self._closing = False
        self._build_ui()
        self._build_timers()

    def _build_ui(self):
        self.setStyleSheet("""
            QWidget     { background-color: #0f1626; color: #f9d342;
                          font-family: Arial; font-size: 22px; }
            AccessiblePushButton { background-color: #16213e; border-radius: 10px;
                          padding: 14px; color: white;
                          border: 2px solid #e94560; margin: 4px; }
            AccessiblePushButton:hover { background-color: #e94560; }
            QLineEdit   { padding: 14px; background-color: #131b36;
                          color: #f9d342; border: 2px solid #f9d342;
                          border-radius: 10px; font-size: 28px; }
        """)
        root = QVBoxLayout()
        root.setSpacing(12)
        self.zone_label = AccessibleLabel(
            "RISK ZONE - Ticket not yet refunded",
            "Risk zone. Ticket not yet refunded. Earn 100 XP to enter safe zone."
        )
        self.zone_label.setStyleSheet("padding: 10px; background-color: #3a0a0a; color: #e94560; border: 2px solid #e94560; border-radius: 10px; font-size: 20px;")
        root.addWidget(self.zone_label)
        row1 = QHBoxLayout()
        self.hearts_display = AccessibleLabel("Hearts: 5 / 5", "Hearts remaining: 5.")
        row1.addWidget(self.hearts_display)
        self.danger_display = AccessibleLabel("Danger: 0 / 10", "Danger: 0 out of 10.")
        row1.addWidget(self.danger_display)
        root.addLayout(row1)
        row2 = QHBoxLayout()
        self.session_xp_label = AccessibleLabel("Session XP: 0", "Session XP earned: 0.")
        row2.addWidget(self.session_xp_label)
        self.timer_label = AccessibleLabel("Time: 00:00", "Elapsed time: 0 seconds.")
        row2.addWidget(self.timer_label)
        root.addLayout(row2)
        self.xpc_label = AccessibleLabel("XP/correct: 0.010", "Current XP per correct answer: 0.010.")
        self.xpc_label.setStyleSheet("padding: 10px; background-color: #1a1a2e; color: #0fecb0; border: 2px solid #0fecb0; border-radius: 10px; font-size: 26px;")
        root.addWidget(self.xpc_label)
        self.target_display = AccessibleLabel("", "Current target.")
        self.target_display.setStyleSheet("padding: 12px; background-color: #1a1a2e; color: #f9d342; border: 2px solid #f9d342; border-radius: 10px; font-size: 52px; min-height: 110px;")
        root.addWidget(self.target_display)
        self.countdown_display = AccessibleLabel("", "Countdown.")
        self.countdown_display.setStyleSheet("padding: 12px; background-color: #1a1a2e; color: #0fecb0; border: 2px solid #0fecb0; border-radius: 10px; font-size: 72px; min-height: 120px;")
        self.countdown_display.setVisible(False)
        root.addWidget(self.countdown_display)
        self.input_field = CrazyPartyTypingInput(self)
        self.input_field.setAccessibleName("Typing field." if self.is_english else "Champ de saisie.")
        self.input_field.textChanged.connect(self._on_input_changed)
        root.addWidget(self.input_field)
        hint = ("Ctrl: repeat target | Shift+Ctrl: status | Shift+Enter: exit" if self.is_english else "Ctrl: repeter | Maj+Ctrl: statut | Maj+Entree: quitter")
        hint_lbl = AccessibleLabel(hint, hint)
        hint_lbl.setStyleSheet("padding: 6px; background: transparent; color: #888; border: none; font-size: 15px;")
        root.addWidget(hint_lbl)
        quit_btn = AccessiblePushButton("Quit" if self.is_english else "Quitter")
        quit_btn.clicked.connect(self._on_shift_enter)
        root.addWidget(quit_btn)
        root.addStretch()
        self.setLayout(root)

    def _build_timers(self):
        self.session_timer = QTimer(self)
        self.session_timer.setInterval(1000)
        self.session_timer.timeout.connect(self._on_session_tick)
        self.target_timer = QTimer(self)
        self.target_timer.setSingleShot(True)
        self.target_timer.timeout.connect(self._on_target_timeout)
        self.countdown_timer = QTimer(self)
        self.countdown_timer.setInterval(1000)
        self.countdown_timer.timeout.connect(self._on_countdown_tick)

    def start_session(self):
        if not self._show_welcome():
            self.close()
            return
        logic = getattr(self.parent_challenge, 'logic', None)
        xp_src = logic if logic else self.base_logic
        if xp_src.xp_balance < self.TICKET_COST:
            self._show_dialog(
                "Not enough XP",
                "You need 100 XP to enter Crazy Party." if self.is_english else "Vous avez besoin de 100 XP pour entrer dans la Fete Folle.",
                [("OK", None)]
            )
            self.close()
            return
        xp_src.xp_balance -= self.TICKET_COST
        if logic:
            logic.save_progress()
        self._reset_state()
        self.setWindowState(Qt.WindowMaximized)
        self.raise_()
        self.activateWindow()
        self.countdown_display.setVisible(True)
        self.countdown_display.update_text(str(self.countdown_value), f"Countdown: {self.countdown_value}.")
        self.countdown_timer.start()
        self.input_field.setFocus()

    def _reset_state(self):
        self.current_hearts = 5
        self.current_danger = 0
        self.elapsed_seconds = 0
        self.current_target = ""
        self.target_count = 0
        self.session_xp_earned = 0.0
        self.ticket_refunded = False
        self.xp_per_correct = 0.01
        self.correct_streak = 0
        self.error_streak = 0
        self._tts_waiting = False
        self._clear_tts()
        self.session_timer.stop()
        self.target_timer.stop()
        self.countdown_timer.stop()
        self.countdown_value = 3
        self.input_field.clear()
        self._refresh_display()

    def _show_welcome(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Crazy Keyboard Party" if self.is_english else "Fete Folle Clavier")
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.setMinimumWidth(600)
        dlg.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout()
        title = AccessibleLabel("CRAZY KEYBOARD PARTY", "Crazy Keyboard Party - welcome screen")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #0fecb0; background: transparent; border: none; padding: 6px;")
        layout.addWidget(title)
        if self.is_english:
            desc = (
                "ENTRY COST: 100 XP ticket.\n\n"
                "RISK ZONE: You start here. Your goal is to earn 100 XP inside the party "
                "to recover your ticket. If you leave or lose all hearts in the risk zone, "
                "the ticket is lost and your session XP reward is halved.\n\n"
                "SAFE ZONE: Once you earn 100 XP, your ticket is automatically refunded. "
                "All further rewards are pure gain. You can leave anytime and keep everything.\n\n"
                "HEARTS AND DANGER:\n"
                "- 5 hearts. Danger bar 0-10.\n"
                "- Wrong answer: +1 danger. Timeout: +2 danger.\n"
                "- Danger 10: lose a heart, danger resets, 4-second beep, 5-second pause.\n\n"
                "XP PER CORRECT: Starts at 0.010 per correct answer.\n"
                "- 5 correct in a row: doubles the multiplier (max 2.0).\n"
                "- One incorrect: subtracts current XP/correct from session XP (no halving).\n"
                "- Two consecutive incorrects OR a timeout: halves the multiplier.\n\n"
                "WORD TARGETS: Occasional words appear. Type one correctly to deal "
                "1% boss health damage. Incorrect words do nothing special.\n\n"
                "Ctrl: repeat target. Shift+Ctrl: status. Shift+Enter: exit.\n\n"
                "This is the highest-reward mode. Play for as long as you survive!"
            )
        else:
            desc = (
                "COUT D'ENTREE : Billet de 100 XP.\n\n"
                "ZONE RISQUEE : Vous commencez ici. Votre objectif est de gagner 100 XP "
                "dans la fete pour recuperer votre billet. Si vous partez ou perdez tous "
                "vos coeurs en zone risquee, le billet est perdu et votre XP de session est divisee par deux.\n\n"
                "ZONE SURE : Une fois 100 XP gagne, votre billet est rembourse. "
                "Toutes les recompenses suivantes sont du gain pur. Partez quand vous voulez.\n\n"
                "COEURS ET DANGER :\n"
                "- 5 coeurs. Jauge de danger 0-10.\n"
                "- Mauvaise reponse : +1 danger. Delai : +2 danger.\n"
                "- Danger 10 : perdre un coeur, danger remis a 0, bip 4 secondes, pause 5 secondes.\n\n"
                "XP PAR CORRECT : Commence a 0,010.\n"
                "- 5 bonnes de suite : double le multiplicateur (max 2,0).\n"
                "- Une erreur : soustrait la valeur actuelle de XP/correct des XP de session (pas de division).\n"
                "- Deux erreurs consecutives OU un delai : divise le multiplicateur par deux.\n\n"
                "CIBLES MOT : Des mots apparaissent parfois. Tapez-en un correctement "
                "pour infliger 1% de degats au boss. Un mot incorrect ne fait rien de special.\n\n"
                "Ctrl : repeter. Maj+Ctrl : statut. Maj+Entree : quitter.\n\n"
                "C'est le mode le plus rentable. Jouez aussi longtemps que vous survivez !"
            )
        browser = AccessibleBrowser(desc, desc)
        browser.setMinimumHeight(480)
        layout.addWidget(browser)
        btn_row = QHBoxLayout()
        btn_yes = AccessiblePushButton("I'm ready for it!" if self.is_english else "Je suis pret(e) !")
        btn_yes.clicked.connect(dlg.accept)
        btn_row.addWidget(btn_yes)
        btn_no = AccessiblePushButton("Not yet" if self.is_english else "Pas encore")
        btn_no.clicked.connect(dlg.reject)
        btn_row.addWidget(btn_no)
        layout.addLayout(btn_row)
        dlg.setLayout(layout)
        return dlg.exec_() == QDialog.Accepted

    def _on_countdown_tick(self):
        self.countdown_value -= 1
        if self.countdown_value > 0:
            self.countdown_display.update_text(str(self.countdown_value), f"Countdown: {self.countdown_value}.")
            if self.base_logic.speaker:
                self.base_logic.speaker.output(str(self.countdown_value))
            return
        self.countdown_timer.stop()
        self.countdown_display.setVisible(False)
        self.session_timer.start()
        self._next_target()
        self.input_field.setFocus()

    def _on_session_tick(self):
        self.elapsed_seconds += 1
        self._refresh_display()

    def _refresh_display(self):
        m = self.elapsed_seconds // 60
        s = self.elapsed_seconds % 60
        self.timer_label.update_text(f"Time: {m:02d}:{s:02d}", f"Elapsed time: {m} minutes {s} seconds.")
        self.hearts_display.update_text(f"Hearts: {self.current_hearts} / 5", f"Hearts remaining: {self.current_hearts} out of 5.")
        self.danger_display.update_text(f"Danger: {self.current_danger} / 10", f"Danger level: {self.current_danger} out of 10.")
        self.session_xp_label.update_text(f"Session XP: {self.session_xp_earned:.1f}", f"Session XP earned: {self.session_xp_earned:.1f}.")
        self.xpc_label.update_text(f"XP/correct: {self.xp_per_correct:.3f}", f"Current XP per correct: {self.xp_per_correct:.3f}.")
        if self.ticket_refunded:
            self.zone_label.update_text("SAFE ZONE - Ticket refunded!", "Safe zone. Your ticket has been refunded. All rewards are kept.")
            self.zone_label.setStyleSheet("padding: 10px; background-color: #0a2a0a; color: #0fecb0; border: 2px solid #0fecb0; border-radius: 10px; font-size: 20px;")
        else:
            needed = self.SAFE_ZONE_XP - self.session_xp_earned
            self.zone_label.update_text(f"RISK ZONE - Earn {needed:.0f} more XP to reach safe zone", f"Risk zone. Earn {needed:.0f} more XP to recover your ticket.")
            self.zone_label.setStyleSheet("padding: 10px; background-color: #3a0a0a; color: #e94560; border: 2px solid #e94560; border-radius: 10px; font-size: 20px;")

    def _is_word_turn(self):
        return self.target_count > 0 and self.target_count % self.WORD_INTERVAL == 0

    def _generate_target(self):
        if self._is_word_turn() and w6words:
            return random.choice(w6words)
        lowercase = "abcdefghijklmnopqrstuvwxyz"
        uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        symbols = "".join(symbol_pronounciation.keys())
        pool = lowercase * 15 + uppercase * 5 + symbols * 2
        return random.choice(pool)

    def _get_timeout_ms(self, target):
        n = len(target)
        if n == 1:
            if target in symbol_pronounciation: return 3800
            if target.isupper(): return 3200
            return 2200
        return 5000 + n * 600

    def _get_pronunciation(self, char):
        if char in symbol_pronounciation:
            return symbol_pronounciation[char]
        if char.isupper() and char.isalpha():
            return _format_uppercase_announcement(char, self.is_english)
        return char

    def _next_target(self):
        self.target_timer.stop()
        self._clear_tts()
        self._tts_waiting = False
        self.target_count += 1
        self.current_target = self._generate_target()
        self.input_field.textChanged.disconnect(self._on_input_changed)
        self.input_field.clear()
        self.input_field.textChanged.connect(self._on_input_changed)
        is_word = len(self.current_target) > 1 and self.current_target[0].isalpha()
        if is_word:
            ann = self.current_target
            spelled = ", ".join(self._get_pronunciation(c) for c in self.current_target)
            self.target_display.update_text(self.current_target, spelled)
            self._pause_timers()
            if self.base_logic.speaker:
                self.base_logic.speaker.output(ann)
                delay = 400
                for c in self.current_target:
                    t = QTimer(self)
                    t.setSingleShot(True)
                    p = self._get_pronunciation(c)
                    t.timeout.connect(lambda p=p: self.base_logic.speaker.output(p))
                    t.start(delay)
                    self._tts_timers.append(t)
                    delay += len(p) * 65 + 200
                resume_t = QTimer(self)
                resume_t.setSingleShot(True)
                resume_t.timeout.connect(self._resume_timers)
                resume_t.start(delay + 300)
                self._tts_timers.append(resume_t)
        else:
            ann = self._get_pronunciation(self.current_target)
            self.target_display.update_text(self.current_target, ann)
            if self.base_logic.speaker:
                self.base_logic.speaker.output(ann)
            self.target_timer.start(self._get_timeout_ms(self.current_target))
        self.input_field.setFocus()

    def _pause_timers(self):
        self._tts_waiting = True
        self.session_timer.stop()
        self.target_timer.stop()

    def _resume_timers(self):
        if not self._tts_waiting:
            return
        self._tts_waiting = False
        if not self.session_timer.isActive():
            self.session_timer.start()
        self.target_timer.start(self._get_timeout_ms(self.current_target))
        self.input_field.setFocus()

    def repeat_current_target(self):
        self._clear_tts()
        self._tts_waiting = False
        if not self.current_target:
            return
        is_word = len(self.current_target) > 1 and self.current_target[0].isalpha()
        if is_word:
            self._pause_timers()
            spelled = ", ".join(self._get_pronunciation(c) for c in self.current_target)
            if self.base_logic.speaker:
                self.base_logic.speaker.output(self.current_target)
                QTimer.singleShot(600, lambda: self.base_logic.speaker.output(spelled) if self.base_logic.speaker else None)
            resume_t = QTimer(self)
            resume_t.setSingleShot(True)
            resume_t.timeout.connect(self._resume_timers)
            resume_t.start(len(self.current_target) * 300 + 900)
            self._tts_timers.append(resume_t)
        else:
            ann = self._get_pronunciation(self.current_target)
            if self.base_logic.speaker:
                self.base_logic.speaker.output(ann)

    def on_typing_key_pressed(self):
        if self._tts_waiting:
            self._clear_tts()
            self._resume_timers()

    def _clear_tts(self):
        for t in self._tts_timers:
            t.stop()
        self._tts_timers.clear()

    def _on_input_changed(self, text):
        if not self.current_target:
            return
        is_word = len(self.current_target) > 1 and self.current_target[0].isalpha()
        if is_word:
            if self.current_target.startswith(text):
                if text == self.current_target:
                    self._on_correct_word()
                return
            self._on_incorrect()
        else:
            if text == self.current_target:
                self._on_correct_letter()
            else:
                self._on_incorrect()

    def _on_correct_letter(self):
        self.target_timer.stop()
        winsound.Beep(1500, 100)
        self.correct_streak += 1
        self.error_streak = 0
        xp_gained = round(self.xp_per_correct, 3)
        self.session_xp_earned = round(self.session_xp_earned + xp_gained, 3)
        if self.correct_streak >= 5:
            self.xp_per_correct = round(min(self.xp_per_correct * 2, 2.0), 3)
            self.correct_streak = 0
        self._check_safe_zone()
        self._refresh_display()
        if not self.session_timer.isActive():
            self.session_timer.start()
        self._next_target()
        self.input_field.setFocus()

    def _on_correct_word(self):
        self._clear_tts()
        self.target_timer.stop()
        self._tts_waiting = False
        winsound.Beep(1500, 150)
        logic = getattr(self.parent_challenge, 'logic', None)
        if logic:
            logic.boss_health = max(0, logic.boss_health - 1)
            if self.base_logic.speaker:
                self.base_logic.speaker.output("Word correct! 1% boss damage." if self.is_english else "Mot correct ! 1% de degats au boss.")
        self.correct_streak += 1
        self.error_streak = 0
        self._check_safe_zone()
        self._refresh_display()
        if not self.session_timer.isActive():
            self.session_timer.start()
        self._next_target()
        self.input_field.setFocus()

    def _on_incorrect(self):
        self._clear_tts()
        self.target_timer.stop()
        self._tts_waiting = False
        winsound.Beep(400, 200)
        penalty = round(self.xp_per_correct, 3)
        self.session_xp_earned = round(max(0, self.session_xp_earned - penalty), 3)
        self.error_streak += 1
        self.correct_streak = 0
        if self.error_streak >= 2:
            self.xp_per_correct = round(max(self.xp_per_correct / 2, 0.001), 3)
            self.error_streak = 0
        self.input_field.blockSignals(True)
        self.input_field.clear()
        self.input_field.blockSignals(False)
        self._apply_danger(1)

    def _on_target_timeout(self):
        winsound.Beep(600, 300)
        penalty = round(self.xp_per_correct, 3)
        self.session_xp_earned = round(max(0, self.session_xp_earned - penalty), 3)
        self.xp_per_correct = round(max(self.xp_per_correct / 2, 0.001), 3)
        self.error_streak = 0
        self.correct_streak = 0
        self._apply_danger(2)

    def _apply_danger(self, amount):
        self._clear_tts()
        self.target_timer.stop()
        self._tts_waiting = False
        self.current_danger = min(10, self.current_danger + amount)
        self._refresh_display()
        if self.current_danger >= 10:
            self.current_danger = 0
            self.current_hearts -= 1
            self._refresh_display()
            winsound.Beep(200, 4000)
            self.session_timer.stop()
            self.input_field.setEnabled(False)
            if self.current_hearts <= 0:
                if self.ticket_refunded:
                    QTimer.singleShot(5000, lambda: self._end_session(success=True))
                else:
                    QTimer.singleShot(5000, lambda: self._end_session(success=False))
                return
            ann = (f"Heart lost. {self.current_hearts} remaining." if self.is_english else f"Coeur perdu. {self.current_hearts} restant.")
            if self.base_logic.speaker:
                self.base_logic.speaker.output(ann)
            QTimer.singleShot(5000, self._resume_after_heart_loss)
            return
        if not self.session_timer.isActive():
            self.session_timer.start()
        self._next_target()
        self.input_field.setFocus()

    def _resume_after_heart_loss(self):
        self.input_field.setEnabled(True)
        if not self.session_timer.isActive():
            self.session_timer.start()
        self._next_target()
        self.input_field.setFocus()

    def _check_safe_zone(self):
        if not self.ticket_refunded and self.session_xp_earned >= self.SAFE_ZONE_XP:
            self.ticket_refunded = True
            if self.base_logic.speaker:
                msg = ("Safe zone reached! Ticket refunded. Keep earning!" if self.is_english else "Zone sure atteinte ! Billet rembourse. Continuez !")
                self.base_logic.speaker.output(msg)

    def _announce_status(self):
        msg = (f"Hearts: {self.current_hearts}. Danger: {self.current_danger}." if self.is_english else f"Coeurs : {self.current_hearts}. Danger : {self.current_danger}.")
        if self.base_logic.speaker:
            self.base_logic.speaker.output(msg)

    def _on_shift_enter(self):
        self._on_ctrl_q()

    def _on_ctrl_q(self):
        self.session_timer.stop()
        self.target_timer.stop()
        dlg = QDialog(self)
        dlg.setWindowTitle("Exit?" if self.is_english else "Quitter ?")
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.setMinimumWidth(560)
        dlg.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout()
        if self.ticket_refunded:
            if self.is_english:
                msg_text = (
                    "You are in the SAFE ZONE.\n\n"
                    "Your 100 XP ticket has already been refunded.\n"
                    "All XP earned in the safe zone will be kept.\n"
                    "All boss damage dealt so far will be kept.\n\n"
                    "Exit and collect your rewards?"
                )
            else:
                msg_text = (
                    "Vous etes en ZONE SURE.\n\n"
                    "Votre billet de 100 XP a deja ete rembourse.\n"
                    "Tous les XP gagnes en zone sure seront conserves.\n"
                    "Tous les degats au boss infliges jusqu'ici seront conserves.\n\n"
                    "Quitter et recuperer vos recompenses ?"
                )
        else:
            if self.is_english:
                msg_text = (
                    "You are still in the RISK ZONE.\n\n"
                    "Your 100 XP ticket has NOT been refunded yet.\n"
                    "If you exit now:\n"
                    "- Ticket is LOST\n"
                    "- Session XP reward is HALVED\n"
                    "- Boss damage already dealt is kept\n\n"
                    "Exit anyway?"
                )
            else:
                msg_text = (
                    "Vous etes encore en ZONE RISQUEE.\n\n"
                    "Votre billet de 100 XP n'a PAS encore ete rembourse.\n"
                    "Si vous quittez maintenant :\n"
                    "- Billet PERDU\n"
                    "- Recompense XP de session DIVISEE PAR DEUX\n"
                    "- Degats au boss deja infliges conserves\n\n"
                    "Quitter quand meme ?"
                )
        msg = AccessibleBrowser(text=msg_text, accessible_text=msg_text)
        layout.addWidget(msg)
        btn_row = QHBoxLayout()
        btn_yes = AccessiblePushButton("Yes, exit" if self.is_english else "Oui, quitter")
        btn_no = AccessiblePushButton("No, continue" if self.is_english else "Non, continuer")
        btn_yes.clicked.connect(dlg.accept)
        btn_no.clicked.connect(dlg.reject)
        btn_row.addWidget(btn_yes)
        btn_row.addWidget(btn_no)
        layout.addLayout(btn_row)
        dlg.setLayout(layout)
        if dlg.exec_() == QDialog.Accepted:
            self._exit_session()
        else:
            if not self.session_timer.isActive():
                self.session_timer.start()
            self.target_timer.start(self._get_timeout_ms(self.current_target))

    def _exit_session(self):
        self._clear_tts()
        self.session_timer.stop()
        self.target_timer.stop()
        logic = getattr(self.parent_challenge, 'logic', None)
        xp_src = logic if logic else self.base_logic
        if self.ticket_refunded:
            final_xp = int(self.session_xp_earned)
            if logic:
                logic.add_xp(final_xp)
        else:
            final_xp = int(self.session_xp_earned // 2)
            if logic:
                logic.add_xp(final_xp)
        if logic:
            logic.save_progress()
            if self.parent_challenge:
                self.parent_challenge.update_display()
        if self.is_english:
            msg_text = f"Session ended.\n\nXP credited: {final_xp}\n{'Ticket refunded.' if self.ticket_refunded else 'Ticket lost.'}"
        else:
            msg_text = f"Session terminee.\n\nXP credites : {final_xp}\n{'Billet rembourse.' if self.ticket_refunded else 'Billet perdu.'}"
        self._show_dialog("Session Ended" if self.is_english else "Session Terminee", msg_text, [("OK", None)])
        self._return_to_battle()

    def _end_session(self, success):
        self._clear_tts()
        self.session_timer.stop()
        self.target_timer.stop()
        logic = getattr(self.parent_challenge, 'logic', None)
        if success:
            final_xp = int(self.session_xp_earned)
            if logic:
                logic.add_xp(final_xp)
                mode = logic.modes.get('crazy_party')
                if mode and not mode.get('completed'):
                    mode['status'] = 'done'
                    mode['completed'] = True
                    logic.completed_modes_count = sum(1 for v in logic.modes.values() if v['completed'])
                logic.save_progress()
            if self.is_english:
                msg_text = f"You reached the safe zone and fought until the end!\n\nXP credited: {final_xp}\nBoss damage from words applied.\n\nWell done!"
            else:
                msg_text = f"Vous avez atteint la zone sure et combattu jusqu'au bout !\n\nXP credites : {final_xp}\nDegats au boss des mots appliques.\n\nBravo !"
            self._show_dialog("Success!" if self.is_english else "Succes !", msg_text, [("Return to Battle" if self.is_english else "Retour au Combat", None)])
        else:
            final_xp = int(self.session_xp_earned // 2)
            if logic:
                logic.add_xp(final_xp)
                logic.save_progress()
            m = self.elapsed_seconds // 60
            s = self.elapsed_seconds % 60
            if self.is_english:
                msg_text = f"All hearts lost in the risk zone.\n\nTime survived: {m:02d}:{s:02d}\nTicket lost. Session XP halved.\nXP credited: {final_xp}"
            else:
                msg_text = f"Tous les coeurs perdus en zone risquee.\n\nTemps survecu : {m:02d}:{s:02d}\nBillet perdu. XP de session divisee par deux.\nXP credites : {final_xp}"
            self._show_dialog("Defeated" if self.is_english else "Vaincu", msg_text,
                              [("Retry" if self.is_english else "Recommencer", self._retry),
                               ("Return to Battle" if self.is_english else "Retour au Combat", None)])
        if self.parent_challenge:
            self.parent_challenge.update_display()
        self._return_to_battle()

    def _retry(self):
        self._return_to_battle()
        if self.parent_challenge:
            self.parent_challenge._start_crazy_party()

    def _return_to_battle(self):
        if self.parent_challenge:
            self.parent_challenge.pages.setCurrentIndex(1)
        self.close()

    def _show_dialog(self, title, message, buttons):
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.setMinimumWidth(520)
        dlg.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout()
        title_lbl = AccessibleLabel(title, title)
        title_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #0fecb0; background: transparent; border: none; padding: 4px;")
        layout.addWidget(title_lbl)
        browser = AccessibleBrowser(message, message)
        browser.setMinimumHeight(200)
        layout.addWidget(browser)
        btn_row = QHBoxLayout()
        for label, cb in buttons:
            btn = AccessiblePushButton(label)
            if cb:
                btn.clicked.connect(lambda checked, c=cb: (dlg.accept(), c()))
            else:
                btn.clicked.connect(dlg.accept)
            btn_row.addWidget(btn)
        layout.addLayout(btn_row)
        dlg.setLayout(layout)
        dlg.exec_()

    def closeEvent(self, event):
        if self._closing:
            event.accept()
            return
        if not self.session_timer.isActive() and not self.target_timer.isActive():
            event.accept()
            return
        self._closing = True
        self._on_ctrl_q()
        event.ignore()


# ============= WEEK 6 LOGIC =============

class Week6Logic:
    def __init__(self, base_logic, user_name="", is_english=True):
        self.base_logic = base_logic
        self.user_name = user_name
        self.is_english = is_english
        self.xp_balance = 50
        self.xp_max = 1500
        self.boss_health = 100
        self.modes = {
            "warmup":      {"name": "Warmup Gate",          "status": "open",   "completed": False},
            "combo":       {"name": "Combo Rush",           "status": "locked", "completed": False},
            "precision":   {"name": "Precision Arena",      "status": "locked", "completed": False},
            "sentence":    {"name": "Sentence Mode",        "status": "locked", "completed": False},
            "survival":    {"name": "Survival Gate",        "status": "locked", "completed": False},
            "crazy_party": {"name": "Crazy Keyboard Party", "status": "locked", "completed": False},
        }
        self.completed_modes_count = 0
        self.csv_file_path = None
        self.progress_loaded = False
        self.load_progress()

    def get_rank_from_xp(self):
        if self.is_english:
            if self.xp_balance < 300: return "Beginner"
            if self.xp_balance < 600: return "Challenger"
            if self.xp_balance < 900: return "Elite Typer"
            if self.xp_balance < 1200: return "Warrior"
            return "Master"
        else:
            if self.xp_balance < 300: return "Débutant"
            if self.xp_balance < 600: return "Challenger"
            if self.xp_balance < 900: return "Typer Élite"
            if self.xp_balance < 1200: return "Guerrier"
            return "Maître"

    def add_xp(self, amount):
        self.xp_balance = min(self.xp_balance + amount, self.xp_max)

    def mark_mode_complete(self, mode_key):
        mode = self.modes[mode_key]
        if mode["status"] == "done" or mode["completed"]:
            return
        mode["status"] = "done"
        mode["completed"] = True
        self.completed_modes_count += 1
        if self.completed_modes_count >= 1:
            for mk, data in self.modes.items():
                if mk != "crazy_party" and not data["completed"]:
                    data["status"] = "unlocked"
        if self.completed_modes_count >= 5:
            if not self.modes["crazy_party"]["completed"]:
                self.modes["crazy_party"]["status"] = "unlocked"

    def get_mode_status_text(self, mode_key):
        mode = self.modes[mode_key]
        if self.is_english:
            if mode["completed"]: return "[completed]  -  Press to replay"
            if mode["status"] == "locked":
                return ("[locked]  -  Finish all modes above to unlock" if mode_key == "crazy_party" else "[locked]  -  Complete Warmup Gate to unlock")
            return "[open]  -  Press Enter to start"
        else:
            if mode["completed"]: return "[complété]  -  Appuyez pour rejouer"
            if mode["status"] == "locked":
                return ("[verrouillé]  -  Terminez les modes au-dessus pour déverrouiller" if mode_key == "crazy_party" else "[verrouillé]  -  Terminez le Warmup Gate pour déverrouiller")
            return "[ouvert]  -  Appuyez Entrée pour commencer"

    def is_challenge_complete(self):
        return self.xp_balance >= self.xp_max and self.boss_health <= 0 and self.modes["crazy_party"]["completed"]

    def load_progress(self):
        if not self.user_name:
            return
        clean_name = self.base_logic.get_clean_username()
        if not clean_name:
            return
        csv_path = os.path.join(self.base_logic.data_dir, clean_name, f"{clean_name}_Week6_Challenge.csv")
        if not os.path.exists(csv_path):
            return
        try:
            last_row = None
            with open(csv_path, 'r', newline='', encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    last_row = row
            if last_row is None:
                return
            self.xp_balance = int(float(last_row["XP Balance"]))
            self.boss_health = int(float(last_row["Boss Health"]))
            completed_str = last_row.get("Completed Modes", "none").strip()
            completed_keys = [k.strip() for k in completed_str.split(",") if k.strip() in self.modes] if completed_str.lower() != "none" else []
            for mk in completed_keys:
                self.modes[mk]["status"] = "done"
                self.modes[mk]["completed"] = True
            self.completed_modes_count = len(completed_keys)
            if self.completed_modes_count >= 1:
                for mk, data in self.modes.items():
                    if mk != "crazy_party" and not data["completed"]:
                        data["status"] = "unlocked"
            if self.completed_modes_count >= 5:
                if not self.modes["crazy_party"]["completed"]:
                    self.modes["crazy_party"]["status"] = "unlocked"
            self.csv_file_path = csv_path
            self.progress_loaded = True
        except Exception:
            pass

    def init_challenge_progress_file(self):
        if not self.user_name:
            return
        clean_name = self.base_logic.get_clean_username()
        user_dir = os.path.join(self.base_logic.data_dir, clean_name)
        os.makedirs(user_dir, exist_ok=True)
        self.csv_file_path = os.path.join(user_dir, f"{clean_name}_Week6_Challenge.csv")
        file_exists = os.path.exists(self.csv_file_path)
        try:
            with open(self.csv_file_path, 'a', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                if not file_exists:
                    w.writerow(["Timestamp", "XP Balance", "Boss Health", "Completed Modes", "Modes Status"])
                completed = [k for k, v in self.modes.items() if v["completed"]]
                w.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), self.xp_balance, self.boss_health, ",".join(completed) if completed else "none", str(self.modes)])
        except Exception:
            pass

    def save_progress(self):
        if not self.csv_file_path:
            return
        try:
            with open(self.csv_file_path, 'a', newline='', encoding='utf-8') as f:
                completed = [k for k, v in self.modes.items() if v["completed"]]
                csv.writer(f).writerow([time.strftime("%Y-%m-%d %H:%M:%S"), self.xp_balance, self.boss_health, ",".join(completed) if completed else "none", str(self.modes)])
        except Exception:
            pass


# ============= WEEK 6 UI =============

class Week6UI(QWidget):
    def __init__(self, base_logic, user_name="", is_english=True):
        super().__init__()
        self.base_logic = base_logic
        self.base_logic.user_name = user_name
        self.is_english = is_english
        self.set_lang_strings()
        self.logic = Week6Logic(base_logic, user_name, is_english)
        self.setWindowTitle(self.strings["window_title"])
        self.setWindowState(Qt.WindowMaximized)
        self.setStyleSheet("""
            QWidget      { background-color: #0a0a12; color: #ffffff;
                           font-family: Arial; font-size: 24px; }
            AccessiblePushButton  { background-color: #16213e; border-radius: 12px;
                           padding: 15px; color: white;
                           border: 2px solid #e94560; margin: 5px; }
            AccessiblePushButton:hover    { background-color: #e94560; }
            AccessiblePushButton:disabled { background-color: #444444;
                                   color: #888888; border-color: #666666; }
            QLineEdit    { padding: 18px; background-color: #1a1a2e;
                           color: #0fecb0; border: 2px solid #0fecb0;
                           border-radius: 10px; }
        """)
        self.pages = QStackedWidget()
        self._setup_identification_page()
        self._setup_challenge_page()
        self._setup_victory_page()
        layout = QVBoxLayout()
        layout.addWidget(self.pages)
        self.setLayout(layout)

    def set_lang_strings(self):
        if self.is_english:
            self.strings = {
                "window_title":       "Week 6 Challenge",
                "id_title":           "WEEK 6: ULTIMATE CHALLENGE",
                "id_instructions":    "Welcome to Week 6 Challenge",
                "id_button_start":    "Let's Start!",
                "id_button_back":     "Back",
                "challenge_title":    "CHALLENGE BATTLE",
                "xp_visual":          "{xp}/{xp_max}",
                "xp_accessible":      "{xp} out of {xp_max}, XP balance",
                "health_visual":      "{health}%",
                "health_accessible":  "Boss health: {health} percent",
                "rank_visual":        "{rank}",
                "rank_accessible":    "Current rank: {rank}",
                "modes_header":       "MODES",
                "button_exit":        "Exit",
                "victory_title":      "VICTORY!",
                "victory_message":    "Congratulations! You defeated the boss!",
                "victory_accessible": "Congratulations! You have defeated the boss! Well done!",
                "victory_button":     "Okay",
                "mode_completed":     "{name} completed",
                "mode_replay":        "Replaying {name}",
                "mode_started":       "Starting {name}",
                "boss_defeated":      "You have defeated the boss",
                "locked_crazy":       "Finish all modes above to unlock",
                "locked_other":       "Complete Warmup Gate to unlock this",
                "progress_loaded":    "Welcome back, {name}! Progress restored.",
                "progress_fresh":     "Challenge started for {name}",
            }
        else:
            self.strings = {
                "window_title":       "Semaine 6  -  Défi Ultime",
                "id_title":           "SEMAINE 6 : DÉFI ULTIME",
                "id_instructions":    "Bienvenue au défi de la Semaine 6",
                "id_button_start":    "C'est parti !",
                "id_button_back":     "Retour",
                "challenge_title":    "COMBAT DE DÉFI",
                "xp_visual":          "{xp}/{xp_max}",
                "xp_accessible":      "{xp} sur {xp_max}, solde XP",
                "health_visual":      "{health}%",
                "health_accessible":  "Santé du Boss : {health} pourcent",
                "rank_visual":        "{rank}",
                "rank_accessible":    "Rang actuel : {rank}",
                "modes_header":       "MODES",
                "button_exit":        "Quitter",
                "victory_title":      "VICTOIRE !",
                "victory_message":    "Félicitations ! Vous avez vaincu le boss !",
                "victory_accessible": "Félicitations ! Vous avez vaincu le boss ! Bravo !",
                "victory_button":     "Okay",
                "mode_completed":     "{name} complété",
                "mode_replay":        "Relancer {name}",
                "mode_started":       "Lancement de {name}",
                "boss_defeated":      "Vous avez vaincu le boss",
                "locked_crazy":       "Terminez les modes au-dessus pour déverrouiller",
                "locked_other":       "Terminez le Warmup Gate pour déverrouiller",
                "progress_loaded":    "Bon retour, {name} ! Progression restaurée.",
                "progress_fresh":     "Défi lancé pour {name}",
            }

    def _setup_identification_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        title = AccessibleLabel(visual_text=self.strings["id_title"], accessible_text=self.strings["id_title"])
        title.setStyleSheet("font-size: 30px; font-weight: bold; color: #e94560; background-color: transparent; border: none;")
        layout.addWidget(title)
        instructions = AccessibleBrowser(text=self.strings["id_instructions"], accessible_text=self.strings["id_instructions"])
        instructions.setMinimumHeight(150)
        layout.addWidget(instructions)
        btn_row = QHBoxLayout()
        btn_start = AccessiblePushButton(self.strings["id_button_start"])
        btn_start.clicked.connect(self.start_challenge)
        btn_row.addWidget(btn_start)
        btn_back = AccessiblePushButton(self.strings["id_button_back"])
        btn_back.clicked.connect(self._go_back)
        btn_row.addWidget(btn_back)
        layout.addLayout(btn_row)
        layout.addStretch()
        page.setLayout(layout)
        self.pages.addWidget(page)

    def _setup_challenge_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        title = AccessibleLabel(visual_text=self.strings["challenge_title"], accessible_text=self.strings["challenge_title"])
        title.setStyleSheet("font-size: 30px; font-weight: bold; color: #0fecb0; background-color: transparent; border: none;")
        layout.addWidget(title)
        stats_layout = QHBoxLayout()
        self.xp_display = AccessibleLabel(visual_text=self.strings["xp_visual"].format(xp=50, xp_max=1500), accessible_text=self.strings["xp_accessible"].format(xp=50, xp_max=1500))
        stats_layout.addWidget(self.xp_display)
        self.health_display = AccessibleLabel(visual_text=self.strings["health_visual"].format(health=100), accessible_text=self.strings["health_accessible"].format(health=100))
        stats_layout.addWidget(self.health_display)
        init_rank = self.logic.get_rank_from_xp()
        self.rank_display = AccessibleLabel(visual_text=self.strings["rank_visual"].format(rank=init_rank), accessible_text=self.strings["rank_accessible"].format(rank=init_rank))
        stats_layout.addWidget(self.rank_display)
        layout.addLayout(stats_layout)
        sep = AccessibleLabel(visual_text="-" * 40, accessible_text="")
        sep.setStyleSheet("color: #444; background: transparent; border: none; font-size: 16px;")
        layout.addWidget(sep)
        modes_header = AccessibleLabel(visual_text=self.strings["modes_header"], accessible_text=self.strings["modes_header"])
        modes_header.setStyleSheet("font-weight: bold; color: #f9d342; background-color: transparent; border: none; font-size: 20px;")
        layout.addWidget(modes_header)
        self.mode_buttons = {}
        for mode_key in ["warmup", "combo", "precision", "sentence", "survival", "crazy_party"]:
            data = self.logic.modes[mode_key]
            status_text = self.logic.get_mode_status_text(mode_key)
            btn = AccessiblePushButton(f"{data['name']}  {status_text}")
            btn.clicked.connect(lambda checked, mk=mode_key: self._on_mode_clicked(mk))
            self.mode_buttons[mode_key] = btn
            layout.addWidget(btn)
        btn_exit = AccessiblePushButton(self.strings["button_exit"])
        btn_exit.clicked.connect(self._exit_challenge)
        layout.addWidget(btn_exit)
        page.setLayout(layout)
        self.pages.addWidget(page)

    def _setup_victory_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        title = AccessibleLabel(visual_text=self.strings["victory_title"], accessible_text=self.strings["victory_title"])
        title.setStyleSheet("font-size: 42px; font-weight: bold; color: #0fecb0; background-color: transparent; border: none; padding: 20px;")
        layout.addWidget(title)
        user_name = self.logic.user_name if self.logic.user_name else "Champion"
        if self.is_english:
            congrats = f"Congratulations, {user_name}!"
        else:
            congrats = f"Félicitations, {user_name} !"
        congrats_label = AccessibleLabel(visual_text=congrats, accessible_text=congrats)
        congrats_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #e94560; background-color: transparent; border: none; padding: 10px;")
        layout.addWidget(congrats_label)
        if self.is_english:
            story = (
                f"You have successfully completed all six modes of the Ultimate Challenge!\n\n"
                f"• Warmup Gate - survived 8 minutes of continuous typing.\n"
                f"• Combo Rush - mastered the multiplier stages.\n"
                f"• Precision Arena - earned your medal through accuracy and speed.\n"
                f"• Sentence Mode - proved your command of full sentences.\n"
                f"• Survival Gate - endured the hardest waves.\n"
                f"• Crazy Keyboard Party - fought in the risk zone and reached safety.\n\n"
                f"Your journey as a Blind Keyboard Master has reached a new peak. "
                f"The boss is defeated, and the keyboard now bends to your will.\n\n"
                f"May this skill serve you in all your future adventures. "
                f"Keep typing, keep improving, and never stop challenging yourself.\n\n"
                f"You can now return to the challenge battle to replay any mode freely, "
                f"or go back to the week selection page to continue your overall progress."
            )
        else:
            story = (
                f"Vous avez réussi à terminer les six modes du Défi Ultime !\n\n"
                f"• Porte Réchauffement - survécu 8 minutes de frappe continue.\n"
                f"• Combo Rush - maîtrisé les étapes à multiplicateur.\n"
                f"• Precision Arena - décroché votre médaille par la précision et la vitesse.\n"
                f"• Mode Phrase - prouvé votre maîtrise des phrases complètes.\n"
                f"• Porte de Survie - enduré les vagues les plus difficiles.\n"
                f"• Fête Folle Clavier - combattu en zone risquée et atteint la zone sûre.\n\n"
                f"Votre parcours en tant que Maître du Clavier Aveugle a atteint un nouveau sommet. "
                f"Le boss est vaincu, et le clavier s'incline devant vous.\n\n"
                f"Que cette compétence vous serve dans toutes vos aventures futures. "
                f"Continuez à taper, à vous améliorer, et ne cessez jamais de vous défier.\n\n"
                f"Vous pouvez maintenant retourner au combat de défi pour rejouer n'importe quel mode librement, "
                f"ou revenir à la page de sélection des semaines pour poursuivre votre progression globale."
            )
        story_browser = AccessibleBrowser(text=story, accessible_text=story)
        story_browser.setMinimumHeight(300)
        layout.addWidget(story_browser)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)
        btn_week = AccessiblePushButton("Return to Week Selection" if self.is_english else "Retour à la sélection des semaines")
        btn_week.clicked.connect(self._go_to_week_selection)
        btn_layout.addWidget(btn_week)
        btn_challenge = AccessiblePushButton("Return to Challenge Battle" if self.is_english else "Retour au combat de défi")
        btn_challenge.clicked.connect(self._go_to_challenge_battle)
        btn_layout.addWidget(btn_challenge)
        layout.addLayout(btn_layout)
        layout.addStretch()
        page.setLayout(layout)
        self.pages.addWidget(page)

    def start_challenge(self):
        self.logic.init_challenge_progress_file()
        self.pages.setCurrentIndex(1)
        self.update_display()
        if self.base_logic.speaker:
            key = "progress_loaded" if self.logic.progress_loaded else "progress_fresh"
            self.base_logic.speaker.output(self.strings[key].format(name=self.logic.user_name))

    def _on_mode_clicked(self, mode_key):
        mode = self.logic.modes[mode_key]
        if mode["status"] == "locked":
            if self.base_logic.speaker:
                key = "locked_crazy" if mode_key == "crazy_party" else "locked_other"
                self.base_logic.speaker.output(self.strings[key])
            return
        if mode_key == "warmup":
            if self.base_logic.speaker:
                self.base_logic.speaker.output(self.strings["mode_started"].format(name=mode["name"]))
            self._start_warmup_typing()
            return
        if mode_key == "combo":
            if self.base_logic.speaker:
                self.base_logic.speaker.output(self.strings["mode_started"].format(name=mode["name"]))
            self._start_combo_typing()
            return
        if mode_key == "precision":
            if self.base_logic.speaker:
                self.base_logic.speaker.output(self.strings["mode_started"].format(name=mode["name"]))
            self._start_precision_typing()
            return
        if mode_key == "survival":
            if self.base_logic.speaker:
                self.base_logic.speaker.output(self.strings["mode_started"].format(name=mode["name"]))
            self._start_survival_mode()
            return
        if mode_key == "sentence":
            if self.base_logic.speaker:
                self.base_logic.speaker.output(self.strings["mode_started"].format(name=mode["name"]))
            self._start_sentence_mode()
            return
        if mode_key == "crazy_party":
            if self.base_logic.speaker:
                self.base_logic.speaker.output(self.strings["mode_started"].format(name=mode["name"]))
            self._start_crazy_party()
            return
        if not mode["completed"]:
            self.logic.mark_mode_complete(mode_key)
            self.logic.save_progress()
            self.update_display()
            if self.base_logic.speaker:
                self.base_logic.speaker.output(self.strings["mode_completed"].format(name=mode["name"]))
            if self.logic.is_challenge_complete():
                self.logic.save_progress()
                self.pages.setCurrentIndex(2)
                if self.base_logic.speaker:
                    self.base_logic.speaker.output(self.strings["boss_defeated"])
                winsound.Beep(2000, 300)
        else:
            if self.base_logic.speaker:
                self.base_logic.speaker.output(self.strings["mode_replay"].format(name=mode["name"]))

    def _go_to_week_selection(self):
        self.logic.save_progress()
        self.base_logic.reset()
        self.close()

    def _go_to_challenge_battle(self):
        self.pages.setCurrentIndex(1)
        self.update_display()

    def _start_warmup_typing(self):
        self.warmup_welcome = WarmupWelcomePage(self, is_english=self.is_english)
        self.warmup_welcome.setStyleSheet(self.styleSheet())
        self.warmup_welcome.setWindowTitle("Warmup Gate" if self.is_english else "Porte Réchauffement")
        self.warmup_welcome.setWindowState(Qt.WindowMaximized)
        self.warmup_welcome.show()

    def _start_combo_typing(self):
        self.combo_welcome = ComboWelcomePage(self, is_english=self.is_english)
        self.combo_welcome.setStyleSheet(self.styleSheet())
        self.combo_welcome.setWindowTitle("Combo Rush" if self.is_english else "Combo Rush")
        self.combo_welcome.setWindowState(Qt.WindowMaximized)
        self.combo_welcome.show()

    def launch_warmup_session(self):
        self.warmup_mode = GenericTypingMode(base_logic=self.base_logic, mode_name="Warmup Gate", is_english=self.is_english, parent=self)
        self.warmup_mode.setStyleSheet(self.styleSheet())
        self.warmup_mode.setWindowTitle("Warmup Gate  -  Typing Session" if self.is_english else "Porte Réchauffement  -  Session de Frappe")
        self.warmup_mode.setWindowState(Qt.WindowMaximized)
        self.warmup_mode.show()
        self.warmup_mode.start_session()

    def launch_combo_session(self):
        self.combo_mode = ComboTypingMode(base_logic=self.base_logic, is_english=self.is_english, parent=self)
        self.combo_mode.setStyleSheet(self.styleSheet())
        self.combo_mode.setWindowTitle("Combo Rush  -  Typing Session" if self.is_english else "Combo Rush  -  Session de Frappe")
        self.combo_mode.setWindowState(Qt.WindowMaximized)
        self.combo_mode.show()
        self.combo_mode.start_session()

    def _start_precision_typing(self):
        self.precision_welcome = PrecisionWelcomePage(self, is_english=self.is_english)
        self.precision_welcome.setStyleSheet(self.styleSheet())
        self.precision_welcome.setWindowTitle("Precision Arena" if self.is_english else "Precision Arena")
        self.precision_welcome.setWindowState(Qt.WindowMaximized)
        self.precision_welcome.show()

    def launch_precision_session(self):
        self.precision_mode = PrecisionArenaMode(base_logic=self.base_logic, is_english=self.is_english, parent=self)
        self.precision_mode.setStyleSheet(self.styleSheet())
        self.precision_mode.setWindowTitle("Precision Arena  -  Typing Session" if self.is_english else "Precision Arena  -  Session de Frappe")
        self.precision_mode.setWindowState(Qt.WindowMaximized)
        self.precision_mode.show()
        self.precision_mode.start_session()

    def _start_survival_mode(self):
        self.survival_mode = SurvivalMode(base_logic=self.base_logic, is_english=self.is_english, parent=self)
        self.survival_mode.setStyleSheet(self.styleSheet())
        self.survival_mode.setWindowTitle("Survival Gate" if self.is_english else "Porte de Survie")
        self.survival_mode.setWindowState(Qt.WindowMaximized)
        self.survival_mode.start_session()

    def _start_sentence_mode(self):
        self.sentence_mode = SentenceMode(base_logic=self.base_logic, is_english=self.is_english, parent=self)
        self.sentence_mode.setStyleSheet(self.styleSheet())
        self.sentence_mode.setWindowTitle("Sentence Mode" if self.is_english else "Mode Phrase")
        self.sentence_mode.setWindowState(Qt.WindowMaximized)
        self.sentence_mode.start_session()

    def _start_crazy_party(self):
        self.crazy_party = CrazyParty(base_logic=self.base_logic, is_english=self.is_english, parent=self)
        self.crazy_party.setStyleSheet(self.styleSheet())
        self.crazy_party.setWindowTitle("Crazy Keyboard Party" if self.is_english else "Fete Folle Clavier")
        self.crazy_party.setWindowState(Qt.WindowMaximized)
        self.crazy_party.show()
        self.crazy_party.start_session()

    def update_display(self):
        xp, mx = self.logic.xp_balance, self.logic.xp_max
        self.xp_display.update_text(self.strings["xp_visual"].format(xp=xp, xp_max=mx), self.strings["xp_accessible"].format(xp=xp, xp_max=mx))
        h = self.logic.boss_health
        self.health_display.update_text(self.strings["health_visual"].format(health=h), self.strings["health_accessible"].format(health=h))
        rank = self.logic.get_rank_from_xp()
        self.rank_display.update_text(self.strings["rank_visual"].format(rank=rank), self.strings["rank_accessible"].format(rank=rank))
        for mode_key, btn in self.mode_buttons.items():
            data = self.logic.modes[mode_key]
            status_text = self.logic.get_mode_status_text(mode_key)
            btn.setText(f"{data['name']}  {status_text}")
        if self.logic.is_challenge_complete():
            self.logic.save_progress()
            self.pages.setCurrentIndex(2)
            if self.base_logic.speaker:
                self.base_logic.speaker.output(self.strings["boss_defeated"])
            winsound.Beep(2000, 500)

    def _exit_challenge(self):
        self.logic.save_progress()
        self.base_logic.reset()
        self.close()

    def _go_back(self):
        self.logic.save_progress()
        self.base_logic.reset()
        self.close()

    def _on_victory_complete(self):
        self.logic.save_progress()
        self.base_logic.reset()
        self.close()