
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
Includes WarmupWelcomePage, GenericTypingMode (warmup session), Week6Logic, Week6UI.
All accessible widgets defined here; imported by english.py and french.py.
"""

import time
import os
import csv
import random
import winsound
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
                             QLabel, QStackedWidget, QDialog, QApplication, QMessageBox,
                             QTextBrowser)
from PyQt5.QtCore import Qt, QTimer
from weeks import symbol_pronounciation


# ============= ACCESSIBLE WIDGETS =============

class AccessibleLabel(QLabel):
    """
    A keyboard-focusable QLabel with separate visual and accessible text.

    visual_text      -  compact text shown on screen  (e.g. "50/1500").
    accessible_text  -  verbose text read by screen reader on focus
                      (e.g. "50 out of 1500 XP balance").

    Tab-focusable so blind users can navigate with the keyboard.
    """

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
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)

    def update_text(self, visual_text, accessible_text=None):
        """Update both displayed and screen-reader text in one call."""
        self.setText(visual_text)
        self.setAccessibleName(
            accessible_text if accessible_text is not None else visual_text
        )


class AccessibleBrowser(QTextBrowser):
    """
    Read-only word-wrapped text area for long multiline content.
    Replaces readonly QLineEdit for paragraphs and descriptions.
    Tab-focusable; screen reader announces full content on focus.
    """

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


# ============= WARMUP WELCOME PAGE =============

class WarmupWelcomePage(QWidget):
    """Welcome screen shown before the Warmup typing session."""

    def __init__(self, parent, is_english=True):
        super().__init__()
        self.parent_challenge = parent
        self.is_english = is_english
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        if self.is_english:
            title_text   = "WARMUP GATE  -  Training Phase 1"
            welcome_text = "Welcome to Warmup Training"
            instructions = (
                "You are entering the first training phase of Boss Mode.\n"
                "Your objective is to survive 8 minutes of continuous typing practice.\n"
                "This will prepare you for future battles.\n\n"
                "Type the characters as they appear. Stay focused and keep typing.\n"
                "Ready? Let's begin!"
            )
            button_text  = "I Am Ready"
        else:
            title_text   = "PORTE RÉCHAUFFEMENT  -  Phase d'Entraînement 1"
            welcome_text = "Bienvenue à l'Entraînement"
            instructions = (
                "Vous entrez dans la première phase d'entraînement du Mode Boss.\n"
                "Votre objectif est de survivre 8 minutes de pratique dactylographique continue.\n"
                "Cela vous préparera pour les batailles futures.\n\n"
                "Tapez les caractères au fur et à mesure qu'ils apparaissent. Restez concentré.\n"
                "Prêt ? Commençons !"
            )
            button_text  = "Je Suis Prêt"

        title = AccessibleLabel(visual_text=title_text, accessible_text=title_text)
        title.setStyleSheet(
            "font-size: 28px; font-weight: bold; color: #0fecb0;"
            "background-color: transparent; border: none; padding: 8px;"
        )
        layout.addWidget(title)

        welcome = AccessibleLabel(visual_text=welcome_text, accessible_text=welcome_text)
        welcome.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #e94560;"
            "background-color: transparent; border: none; padding: 4px;"
        )
        layout.addWidget(welcome)

        inst_field = AccessibleBrowser(text=instructions, accessible_text=instructions)
        inst_field.setMinimumHeight(180)
        layout.addWidget(inst_field)

        btn_ready = QPushButton(button_text)
        btn_ready.clicked.connect(self._launch)
        layout.addWidget(btn_ready)

        layout.addStretch()
        self.setLayout(layout)

    def _launch(self):
        if hasattr(self.parent_challenge, 'launch_warmup_session'):
            self.parent_challenge.launch_warmup_session()
        self.close()


# ============= GENERIC TYPING MODE =============

class GenericTypingMode(QWidget):
    """
    Reusable 8-minute typing session for all Week 6 battle modes.
    Override get_random_target() in subclasses for different character pools.
    """

    def __init__(self, base_logic, mode_name="Warmup Gate", is_english=True, parent=None):
        super().__init__()
        self.base_logic       = base_logic
        self.mode_name        = mode_name
        self.is_english       = is_english
        self.parent_challenge = parent

        # Session state
        self.session_start_time = None
        self.session_duration   = 480        # 8 minutes
        self.current_target     = ""
        self.target_start_time  = None
        self.target_timeout     = 2.0
        self._original_target   = ""

        # Stats
        self.correct_count   = 0
        self.incorrect_count = 0
        self.timeout_count   = 0
        self.xp_earned       = 0.0
        self.session_xp      = 0.0
        self.accuracy        = 0.0

        # CSV
        self.warmup_csv_path = None

        self._setup_ui()
        self._setup_timers()

    # ---- UI ----

    def _setup_ui(self):
        layout = QVBoxLayout()

        if self.is_english:
            mode_label_text   = "WARMUP GATE  -  Continuous Practice"
            instructions_text = (
                "Type each character that appears.\n"
                "Incorrect entries and timeouts do not stop the session  -  keep typing!"
            )
            xp_text           = "XP Earned: 0"
            timer_text        = "Time: 8:00"
            button_text       = "Leave and Go Back to Challenge Battle"
        else:
            mode_label_text   = "PORTE RÉCHAUFFEMENT  -  Pratique Continue"
            instructions_text = (
                "Tapez chaque caractère qui apparaît.\n"
                "Les erreurs et dépassements ne stoppent pas la session  -  continuez !"
            )
            xp_text           = "XP Gagné : 0"
            timer_text        = "Temps : 8:00"
            button_text       = "Quitter et Retourner au Combat de Défi"

        mode_title = AccessibleLabel(
            visual_text=mode_label_text, accessible_text=mode_label_text
        )
        mode_title.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #0fecb0;"
            "background-color: transparent; border: none; padding: 6px;"
        )
        layout.addWidget(mode_title)

        self.instructions_display = AccessibleBrowser(
            text=instructions_text, accessible_text=instructions_text
        )
        self.instructions_display.setMinimumHeight(70)
        layout.addWidget(self.instructions_display)

        # Stats row
        stats_layout = QHBoxLayout()
        self.xp_label = AccessibleLabel(visual_text=xp_text, accessible_text=xp_text)
        stats_layout.addWidget(self.xp_label)
        self.timer_label = AccessibleLabel(
            visual_text=timer_text, accessible_text=timer_text
        )
        stats_layout.addWidget(self.timer_label)
        layout.addLayout(stats_layout)

        # Target display  -  large character; AccessibleLabel so screen reader tracks it
        self.target_display = AccessibleLabel(
            visual_text="", accessible_text="Waiting for session to start"
        )
        self.target_display.setStyleSheet(
            "font-size: 120px; color: #f9d342;"
            "border: 3px solid #f9d342; border-radius: 10px;"
            "background-color: #1a1a2e; padding: 8px;"
            "min-height: 160px;"
        )
        layout.addWidget(self.target_display)

        # Typing input
        self.input_field = QLineEdit()
        self.input_field.textChanged.connect(self._on_input_changed)
        layout.addWidget(self.input_field)

        btn_leave = QPushButton(button_text)
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

    # ---- Session lifecycle ----

    def start_session(self):
        """Call after show() to begin the timed session."""
        self.session_start_time = time.time()
        self.correct_count   = 0
        self.incorrect_count = 0
        self.timeout_count   = 0
        self.session_xp      = 0.0
        self.xp_earned       = 0.0

        self._init_warmup_csv()
        self.session_timer.start(1000)
        self._next_target()

        if self.base_logic.speaker:
            msg = ("Warmup session started. Begin typing!"
                   if self.is_english else
                   "Session de réchauffement démarrée. Commencez à taper !")
            self.base_logic.speaker.output(msg)

    # ---- CSV ----

    def _init_warmup_csv(self):
        clean_name = self.base_logic.get_clean_username()
        user_dir = os.path.join(self.base_logic.data_dir, clean_name)
        os.makedirs(user_dir, exist_ok=True)
        self.warmup_csv_path = os.path.join(
            user_dir, f"{clean_name}_Warmup_Session.csv"
        )
        try:
            with open(self.warmup_csv_path, 'w', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow(
                    ["Timestamp", "Target", "Status", "Typing Time (s)"]
                )
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
                    round(typing_time, 3)
                    if status == "correct" and typing_time is not None
                    else "!",
                ])
        except Exception:
            pass

    # ---- Target generation ----

    def get_random_target(self):
        """
        Warmup character pool - case-sensitive, like week 5.
        Lowercase (most common), uppercase (less frequent, requires Shift),
        symbols from the pronunciation dictionary (least frequent).
        """
        lowercase = "abcdefghijklmnopqrstuvwxyz"
        uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        symbols   = "".join(symbol_pronounciation.keys())
        # 15 lowercase : 5 uppercase : 3 symbols
        pool = lowercase * 15 + uppercase * 5 + symbols * 3
        return random.choice(pool)

    def _next_target(self):
        self.target_timer.stop()
        self.current_target    = self.get_random_target()
        self.target_start_time = time.time()

        # Symbols/uppercase -> 4 s timeout; lowercase only -> 2 s
        if self.current_target in symbol_pronounciation or self.current_target.isupper():
            self.target_timeout = 4.0
        else:
            self.target_timeout = 2.0

        # Build announcement
        if self.current_target in symbol_pronounciation:
            announcement = symbol_pronounciation[self.current_target]
        elif self.current_target.isupper():
            announcement = f"{self.current_target.lower()} majuscule"
        else:
            announcement = self.current_target

        self.target_display.update_text(self.current_target, announcement)

        if self.base_logic.speaker:
            self.base_logic.speaker.output(announcement)

        self.input_field.blockSignals(True)
        self.input_field.clear()
        self.input_field.blockSignals(False)
        self.input_field.setFocus()

        self.target_timer.start(int(self.target_timeout * 1000))

    # ---- Input handling ----

    def _on_input_changed(self, text):
        if not text:
            return

        typed = text[-1]

        if typed == self.current_target:
            # Correct - exact case match required (like week 5)
            self.target_timer.stop()
            typing_time = time.time() - self.target_start_time
            winsound.Beep(1500, 100)
            self.correct_count += 1
            self.session_xp    += 0.25
            self.xp_earned     += 0.25
            self._update_xp_display()
            self._log_attempt(self.current_target, "correct", typing_time)
            self._next_target()

        else:
            # Incorrect - wrong key or wrong case; penalise and move on immediately
            self.target_timer.stop()
            winsound.Beep(400, 200)
            self.incorrect_count += 1
            self.session_xp      -= 0.5
            self.xp_earned       -= 0.5
            self._update_xp_display()
            self._log_attempt(self.current_target, "incorrect")
            self.input_field.blockSignals(True)
            self.input_field.clear()
            self.input_field.blockSignals(False)
            self._next_target()

    def _on_target_timeout(self):
        winsound.Beep(600, 300)
        self.timeout_count += 1
        self.session_xp    -= 1.0
        self.xp_earned     -= 1.0
        self._update_xp_display()
        self._log_attempt(self.current_target, "timeout")
        self._next_target()

    # ---- Display helpers ----

    def _update_xp_display(self):
        v = (f"XP Earned: {self.xp_earned:.2f}"
             if self.is_english else
             f"XP Gagné : {self.xp_earned:.2f}")
        a = (f"{self.xp_earned:.2f} XP earned this session"
             if self.is_english else
             f"{self.xp_earned:.2f} XP gagnés cette session")
        self.xp_label.update_text(v, a)

    def _update_session_timer(self):
        elapsed   = time.time() - self.session_start_time
        remaining = self.session_duration - elapsed
        if remaining <= 0:
            self._end_session()
            return
        m = int(remaining) // 60
        s = int(remaining) % 60
        v = f"Time: {m}:{s:02d}" if self.is_english else f"Temps : {m}:{s:02d}"
        a = (f"{m} minutes {s} seconds remaining"
             if self.is_english else
             f"{m} minutes {s} secondes restantes")
        self.timer_label.update_text(v, a)

    # ---- Temporary message overlay ----

    def show_temporary_message(self, message, duration=2000):
        """Flash a message in the target area; typing continues in background."""
        self._original_target = self.current_target
        self.target_display.update_text(message, message)
        self.target_display.setStyleSheet(
            "font-size: 60px; color: #0fecb0;"
            "border: 3px solid #0fecb0; border-radius: 10px;"
            "background-color: #1a1a2e; padding: 8px; min-height: 160px;"
        )
        self.message_timer.start(duration)

    def _clear_message_display(self):
        t = self._original_target
        if t:
            ann = symbol_pronounciation.get(
                t,
                f"{t.lower()} majuscule" if t.isupper() else t
            )
            self.target_display.update_text(t, ann)
        self.target_display.setStyleSheet(
            "font-size: 120px; color: #f9d342;"
            "border: 3px solid #f9d342; border-radius: 10px;"
            "background-color: #1a1a2e; padding: 8px; min-height: 160px;"
        )

    # ---- Session end ----

    def _end_session(self):
        self.session_timer.stop()
        self.target_timer.stop()
        self.message_timer.stop()

        total = self.correct_count + self.incorrect_count
        self.accuracy = (self.correct_count / total * 100) if total > 0 else 0.0

        self.session_xp += 30
        self.xp_earned  += 30

        accuracy_bonus = boss_damage_bonus = 0
        if self.accuracy >= 90:
            accuracy_bonus    = 20
            boss_damage_bonus = 5
            self.session_xp  += 20
            self.xp_earned   += 20

        self._update_challenge_state(accuracy_bonus, boss_damage_bonus)
        self._show_results_page()

    def _update_challenge_state(self, accuracy_bonus, boss_damage_bonus):
        if not (self.parent_challenge and hasattr(self.parent_challenge, 'logic')):
            return
        logic = self.parent_challenge.logic
        logic.add_xp(int(self.session_xp))
        if boss_damage_bonus > 0:
            logic.boss_health = max(0, logic.boss_health - boss_damage_bonus)
        logic.modes["warmup"]["status"]    = "done"
        logic.modes["warmup"]["completed"] = True
        logic.completed_modes_count = sum(
            1 for v in logic.modes.values() if v["completed"]
        )
        for mk, data in logic.modes.items():
            if mk != "crazy_party" and not data["completed"]:
                data["status"] = "unlocked"
        logic.save_progress()
        self.parent_challenge.update_display()

    def _show_results_page(self):
        if self.is_english:
            title          = "WARMUP COMPLETE"
            correct_text   = f"Correct Answers: {self.correct_count}"
            incorrect_text = f"Incorrect Answers: {self.incorrect_count}"
            timeout_text   = f"Timeouts: {self.timeout_count}"
            accuracy_text  = f"Accuracy: {self.accuracy:.1f}%"
            xp_text        = f"Total XP Earned: {int(self.xp_earned)}"
            bonus_text     = (
                "Accuracy Bonus: +20 XP  |  Boss Damage: -5%"
                if self.accuracy >= 90 else
                "Tip: reach 90%+ accuracy for a bonus!"
            )
            button_text    = "Return to Challenge Battle"
        else:
            title          = "ÉCHAUFFEMENT COMPLET"
            correct_text   = f"Bonnes Réponses : {self.correct_count}"
            incorrect_text = f"Mauvaises Réponses : {self.incorrect_count}"
            timeout_text   = f"Dépassements : {self.timeout_count}"
            accuracy_text  = f"Précision : {self.accuracy:.1f}%"
            xp_text        = f"XP Total Gagné : {int(self.xp_earned)}"
            bonus_text     = (
                "Bonus Précision : +20 XP  |  Dommage Boss : -5%"
                if self.accuracy >= 90 else
                "Conseil : atteignez 90%+ de précision pour un bonus !"
            )
            button_text    = "Retour au Combat de Défi"

        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setMinimumWidth(520)
        dlg.setStyleSheet(self.styleSheet())

        layout = QVBoxLayout()

        title_label = AccessibleLabel(visual_text=title, accessible_text=title)
        title_label.setStyleSheet(
            "font-size: 26px; font-weight: bold; color: #0fecb0;"
            "background-color: transparent; border: none; padding: 6px;"
        )
        layout.addWidget(title_label)

        stats_text = (
            f"{correct_text}\n{incorrect_text}\n{timeout_text}\n"
            f"{accuracy_text}\n\n{xp_text}\n{bonus_text}"
        )
        stats_browser = AccessibleBrowser(
            text=stats_text, accessible_text=stats_text
        )
        stats_browser.setMinimumHeight(220)
        layout.addWidget(stats_browser)

        btn_return = QPushButton(button_text)
        btn_return.clicked.connect(lambda: self._return_to_challenge(dlg))
        layout.addWidget(btn_return)

        dlg.setLayout(layout)
        dlg.exec_()

    def _return_to_challenge(self, dialog):
        dialog.accept()
        if self.parent_challenge:
            self.parent_challenge.pages.setCurrentIndex(1)  # challenge battle = page 1
            self.parent_challenge.update_display()
        self.close()

    # ---- Early exit ----

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
            msg = ("Session exited. 50 XP penalty applied."
                   if self.is_english else
                   "Session quittée. Pénalité de 50 XP appliquée.")
            self.base_logic.speaker.output(msg)

        if self.parent_challenge:
            self.parent_challenge.pages.setCurrentIndex(1)
        self.close()

    def closeEvent(self, event):
        self.session_timer.stop()
        self.target_timer.stop()
        self.message_timer.stop()
        event.accept()


# ============= COMBO MODE WELCOME PAGE =============

class ComboWelcomePage(QWidget):
    """Welcome screen explaining Combo Mode mechanics before the challenge begins."""

    def __init__(self, parent, is_english=True):
        super().__init__()
        self.parent_challenge = parent
        self.is_english = is_english
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        if self.is_english:
            title_text = "COMBO RUSH  -  Stage-Based Multiplier Challenge"
            welcome_text = "Welcome to Combo Mode"
            instructions = (
                "Build your combo score through precision and survive increasing complexity!\n\n"
                "SCORING MECHANICS:\n"
                "Correct answer: Doubles your current combo score\n"
                "Incorrect answer: Divides your score by 3\n"
                "Timeout: Resets score\n\n"
                "STAGE PROGRESSION:\n"
                "Stage 1 (5 min): Single characters\n"
                "Stage 2 (5 min): Two-character combos\n"
                "Stage 3 (5 min): Three-character combos\n"
                "Continue infinitely with longer combos for bonus rewards\n\n"
                "OBJECTIVE:\n"
                "Complete Stage 3 with at least 70% accuracy to win."
            )
            button_text = "I Am Ready"
        else:
            title_text = "COMBO RUSH  -  Défi de Multiplicateur par Étape"
            welcome_text = "Bienvenue au Mode Combo"
            instructions = (
                "Construisez votre score de combo par la précision et survivez à la complexité croissante !\n\n"
                "MÉCANIQUE DE NOTATION :\n"
                "Bonne réponse : Double votre score de combo\n"
                "Mauvaise réponse : Divise votre score par 3\n"
                "Dépassement : Réinitialise le score\n\n"
                "PROGRESSION PAR ÉTAPE :\n"
                "Étape 1 (5 min) : Caractères uniques\n"
                "Étape 2 (5 min) : Combos de deux caractères\n"
                "Étape 3 (5 min) : Combos de trois caractères\n"
                "Continuez indéfiniment avec des combos plus longs pour des récompenses bonus\n\n"
                "OBJECTIF :\n"
                "Terminez l'étape 3 avec au moins 70 % de précision pour gagner."
            )
            button_text = "Je Suis Prêt"

        title = AccessibleLabel(visual_text=title_text, accessible_text=title_text)
        title.setStyleSheet(
            "font-size: 26px; font-weight: bold; color: #0fecb0;"
            "background-color: transparent; border: none; padding: 8px;"
        )
        layout.addWidget(title)

        welcome = AccessibleLabel(visual_text=welcome_text, accessible_text=welcome_text)
        welcome.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #e94560;"
            "background-color: transparent; border: none; padding: 4px;"
        )
        layout.addWidget(welcome)

        inst_field = AccessibleBrowser(text=instructions, accessible_text=instructions)
        inst_field.setMinimumHeight(300)
        layout.addWidget(inst_field)

        btn_ready = QPushButton(button_text)
        btn_ready.clicked.connect(self._launch)
        layout.addWidget(btn_ready)

        layout.addStretch()
        self.setLayout(layout)

    def _launch(self):
        if hasattr(self.parent_challenge, 'launch_combo_session'):
            self.parent_challenge.launch_combo_session()
        self.close()


# ============= COMBO MODE TYPING SESSION =============

class ComboTypingMode(GenericTypingMode):
    """
    Multi-stage Combo Mode with progression-based infinite challenge.
    Extends GenericTypingMode with stage progression, combo scoring, and XP conversion.
    """

    def __init__(self, base_logic, is_english=True, parent=None):
        # Initialize parent but override session_duration
        super().__init__(
            base_logic,
            mode_name="Combo Rush",
            is_english=is_english,
            parent=parent
        )
        
        # Override for Combo Mode
        self.session_duration = 999999  # Controlled by stage transitions instead
        
        # Combo-specific state
        self.current_stage = 1
        self.stage_start_time = None
        self.stage_duration = 300  # 5 minutes per stage
        self.combo_score = 0.01  # Start at 0.01 to prevent XP farming
        self.highest_combo = 0.01
        self.xp_conversion_rates = {1: 0.1, 2: 0.2, 3: 0.4}  # Stage -> multiplier
        self.total_session_xp = 0.0
        self.session_complete = False
        self.continue_challenge = False
        self.combo_csv_path = None
        self.session_accuracy = 0.0
        self.failed_mode = False
        
    def _setup_ui(self):
        """Override parent UI to include combo-specific indicators."""
        layout = QVBoxLayout()

        if self.is_english:
            mode_label_text = "COMBO RUSH  -  Stage-Based Progression"
            instructions_text = (
                "Type the combo as it appears. Build your streak and maximize score!\n"
                "Correct: 2x score | Incorrect: ÷3 | Timeout: Reset"
            )
            xp_text = "XP Balance: 0"
            stage_text = "Stage: 1 - Single Character"
            score_text = "Combo Score: 0.01"
            timer_text = "Stage Time: 5:00"
            button_text = "Leave and Go Back to Challenge Battle"
        else:
            mode_label_text = "COMBO RUSH  -  Progression par Etape"
            instructions_text = (
                "Tapez le combo au fur et a mesure. Construisez votre serie et maximisez le score !\n"
                "Correct : 2x score | Incorrect : ÷3 | Depassement : Reinitialiser"
            )
            xp_text = "Solde XP : 0"
            stage_text = "Etape : 1 - Caractere Unique"
            score_text = "Score Combo : 0.01"
            timer_text = "Temps d'Etape : 5:00"
            button_text = "Quitter et Retourner au Combat de Defi"

        mode_title = AccessibleLabel(
            visual_text=mode_label_text, accessible_text=mode_label_text
        )
        mode_title.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #0fecb0;"
            "background-color: transparent; border: none; padding: 6px;"
        )
        layout.addWidget(mode_title)

        self.instructions_display = AccessibleBrowser(
            text=instructions_text, accessible_text=instructions_text
        )
        self.instructions_display.setMinimumHeight(70)
        layout.addWidget(self.instructions_display)

        # Stats row 1: XP and Stage
        stats_layout1 = QHBoxLayout()
        self.xp_label = AccessibleLabel(visual_text=xp_text, accessible_text=xp_text)
        stats_layout1.addWidget(self.xp_label)
        
        self.stage_label = AccessibleLabel(
            visual_text=stage_text, 
            accessible_text=stage_text
        )
        stats_layout1.addWidget(self.stage_label)
        layout.addLayout(stats_layout1)

        # Stats row 2: Combo score and timer
        stats_layout2 = QHBoxLayout()
        self.combo_score_label = AccessibleLabel(
            visual_text=score_text,
            accessible_text=score_text
        )
        stats_layout2.addWidget(self.combo_score_label)
        
        self.timer_label = AccessibleLabel(
            visual_text=timer_text, accessible_text=timer_text
        )
        stats_layout2.addWidget(self.timer_label)
        layout.addLayout(stats_layout2)

        # Target display - large combo text
        self.target_display = AccessibleLabel(
            visual_text="", accessible_text="Waiting for stage to start"
        )
        self.target_display.setStyleSheet(
            "font-size: 100px; color: #f9d342;"
            "border: 3px solid #f9d342; border-radius: 10px;"
            "background-color: #1a1a2e; padding: 8px;"
            "min-height: 160px;"
        )
        layout.addWidget(self.target_display)

        # Typing input
        self.input_field = QLineEdit()
        self.input_field.textChanged.connect(self._on_input_changed)
        layout.addWidget(self.input_field)

        btn_leave = QPushButton(button_text)
        btn_leave.clicked.connect(self.leave_session)
        layout.addWidget(btn_leave)

        self.setLayout(layout)

    def start_session(self):
        """Start the Combo Mode challenge with Stage 1."""
        self.session_start_time = time.time()
        self.stage_start_time = time.time()
        self.current_stage = 1
        self.combo_score = 0.01
        self.highest_combo = 0.01
        self.total_session_xp = 0.0
        self.correct_count = 0
        self.incorrect_count = 0
        self.timeout_count = 0
        self.session_accuracy = 0.0

        self._init_combo_csv()
        self.session_timer.start(1000)
        self._next_target()

        if self.base_logic.speaker:
            msg = (
                f"Combo Mode started. Stage 1 begins. Type the character as it appears!"
                if self.is_english else
                f"Mode Combo lancé. L'étape 1 commence. Tapez le caractère au fur et à mesure !"
            )
            self.base_logic.speaker.output(msg)

    def _init_combo_csv(self):
        """Initialize CSV for detailed combo session logging."""
        clean_name = self.base_logic.get_clean_username()
        user_dir = os.path.join(self.base_logic.data_dir, clean_name)
        os.makedirs(user_dir, exist_ok=True)
        self.combo_csv_path = os.path.join(
            user_dir, f"{clean_name}_Combo_Session_{int(time.time())}.csv"
        )
        try:
            with open(self.combo_csv_path, 'w', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow([
                    "Timestamp", "Generated Combo", "Result Status", "Response Time (s)",
                    "Stage", "Current Combo Score"
                ])
        except Exception:
            pass

    def _log_combo_attempt(self, combo, status, response_time, score_after_action):
        """Log a combo attempt to CSV.
        
        Args:
            combo: The generated combo string
            status: "correct", "incorrect", or "timeout"
            response_time: Time taken (only for correct attempts)
            score_after_action: Combo score AFTER this action is applied
        """
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
        """Override parent to generate combos based on current stage."""
        lowercase = "abcdefghijklmnopqrstuvwxyz"
        uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        symbols = "".join(symbol_pronounciation.keys())
        char_pool = lowercase + uppercase + symbols

        combo_length = min(self.current_stage, 10)  # Stage 1=1, Stage 2=2, etc, max 10 chars
        combo = "".join(random.choice(char_pool) for _ in range(combo_length))
        return combo

    def _next_target(self):
        """Generate next combo and set up timeout."""
        self.target_timer.stop()
        self.current_target = self.get_random_target()
        self.target_start_time = time.time()

        # Dynamic timeout: 4 sec for symbols/uppercase, 2 sec for lowercase only
        has_symbol = any(char in symbol_pronounciation for char in self.current_target)
        has_uppercase = any(char.isupper() for char in self.current_target)
        
        if has_symbol or has_uppercase:
            self.target_timeout = 4.0
        else:
            self.target_timeout = 2.0

        # Build announcement
        announcement = self._get_combo_announcement(self.current_target)
        self.target_display.update_text(self.current_target, announcement)

        self.input_field.blockSignals(True)
        self.input_field.clear()
        self.input_field.blockSignals(False)

        # For Stage 1: immediate timer start
        # For Stage 2+: disable input during announcement, then enable with beep
        if self.current_stage == 1:
            self.input_field.setFocus()
            if self.base_logic.speaker:
                self.base_logic.speaker.output(announcement)
            self.target_timer.start(int(self.target_timeout * 1000))
        else:
            # Disable input during pronunciation phase
            self.input_field.setEnabled(False)
            if self.base_logic.speaker:
                self.base_logic.speaker.output(announcement)
            # Calculate delay based on announcement length (like word practice mode)
            announcement_length = len(announcement)
            spelling_delay = announcement_length * 60 + 400
            QTimer.singleShot(spelling_delay, self._start_combo_timer)

    def _get_combo_announcement(self, combo):
        """Convert combo string to screen reader announcement."""
        parts = []
        for char in combo:
            if char in symbol_pronounciation:
                parts.append(symbol_pronounciation[char])
            elif char.isupper():
                parts.append(f"{char.lower()} majuscule" if not self.is_english else f"{char.lower()} capital")
            else:
                parts.append(char)
        return ", ".join(parts)

    def _start_combo_timer(self):
        """Start the combo timer with beep signal (for stages 2+)."""
        # Update target_start_time to now so timer duration is accurate
        self.target_start_time = time.time()
        # Play start signal beep (1000Hz, 150ms like word practice mode)
        winsound.Beep(1000, 150)
        # Enable input and set focus
        self.input_field.setEnabled(True)
        self.input_field.setFocus()
        # Start the timer
        self.target_timer.start(int(self.target_timeout * 1000))

    def _on_input_changed(self, text):
        """Handle typing input - check for combo match."""
        if not text:
            return

        typed = text.strip()

        if typed == self.current_target:
            # Correct - exact match
            self.target_timer.stop()
            typing_time = time.time() - self.target_start_time
            
            winsound.Beep(1500, 100)
            self.correct_count += 1
            
            # Double the combo score, rounded to 2dp to avoid float drift
            self.combo_score = round(self.combo_score * 2, 2)
            
            # Cap at 128 - auto-convert integer part to XP and reset to 0.01
            if self.combo_score >= 128:
                multiplier = self.get_xp_multiplier(self.current_stage)
                xp_gained = round(int(self.combo_score) * multiplier, 1)
                self.total_session_xp += xp_gained
                self.xp_earned = self.total_session_xp
                self.combo_score = 0.01
                if self.base_logic.speaker:
                    msg = (
                        f"Combo cap! {xp_gained} XP converted."
                        if self.is_english else
                        f"Plafond combo ! {xp_gained} XP convertis."
                    )
                    self.base_logic.speaker.output(msg)
            
            # Track highest combo reached
            if self.combo_score > self.highest_combo:
                self.highest_combo = self.combo_score
            
            # Log attempt with current score after doubling
            self._log_combo_attempt(self.current_target, "correct", typing_time, self.combo_score)
            
            self._update_displays()
            self._next_target()
            return

        elif len(text) >= len(self.current_target) or (text and text != self.current_target[:len(text)]):
            # Incorrect if: typed past target length, OR typed text doesn't match target start
            self.target_timer.stop()
            winsound.Beep(400, 200)
            self.incorrect_count += 1
            
            # Divide score by 3, rounded to 2dp to prevent infinite float expansion
            self.combo_score = round(self.combo_score / 3.0, 2)
            # Minimum floor of 0.01 so score never reaches exactly zero
            if self.combo_score < 0.01:
                self.combo_score = 0.01
            
            # Log attempt with current score after division
            self._log_combo_attempt(self.current_target, "incorrect", None, self.combo_score)
            
            self._update_displays()
            self._next_target()  # Immediately move to next target
            return

    def _on_target_timeout(self):
        """Handle timeout - reset score to 0.01."""
        winsound.Beep(600, 300)
        self.timeout_count += 1
        
        # Reset score to 0.01 on timeout
        self.combo_score = 0.01
        
        self._log_combo_attempt(self.current_target, "timeout", None, self.combo_score)
        
        self._update_displays()
        self._next_target()

    def _update_session_timer(self):
        """Update timers and check for stage transitions."""
        # Calculate stage elapsed time
        stage_elapsed = time.time() - self.stage_start_time
        stage_remaining = self.stage_duration - stage_elapsed

        if stage_remaining <= 0:
            # Stage complete - convert XP and transition to next stage
            self._convert_stage_xp()
            self._transition_stage()
            return

        m = int(stage_remaining) // 60
        s = int(stage_remaining) % 60
        v = f"Stage Time: {m}:{s:02d}" if self.is_english else f"Temps d'Étape : {m}:{s:02d}"
        a = (f"{m} minutes {s} seconds remaining in this stage"
             if self.is_english else
             f"{m} minutes {s} secondes restantes dans cette étape")
        self.timer_label.update_text(v, a)

    def _convert_mini_xp(self):
        """Convert combo score to XP when it reaches 128 mid-stage."""
        multiplier = self.get_xp_multiplier(self.current_stage)
        xp_gained = round(int(self.combo_score) * multiplier, 1)
        self.total_session_xp += xp_gained
        self.xp_earned = self.total_session_xp
        self._update_displays()

    def _convert_stage_xp(self):
        """Convert current combo score to XP at end of stage."""
        multiplier = self.get_xp_multiplier(self.current_stage)
        xp_gained = round(int(self.combo_score) * multiplier, 1)
        self.total_session_xp += xp_gained
        self.xp_earned = self.total_session_xp
        self._update_displays()

    def _transition_stage(self):
        """Move to the next stage or handle stage completion."""
        if self.current_stage < 3:
            # Transition from mandatory stages (1→2, 2→3)
            self.current_stage += 1
            self.stage_start_time = time.time()
            self.combo_score = 0.01  # Reset score for new stage
            
            stage_names = {
                1: ("Stage 1 – Single Character", "Étape 1 – Caractère Unique"),
                2: ("Stage 2 – Two Character Combos", "Étape 2 – Combos de Deux Caractères"),
                3: ("Stage 3 – Three Character Combos", "Étape 3 – Combos de Trois Caractères"),
            }
            eng_name, fr_name = stage_names[self.current_stage]
            display_text = eng_name if self.is_english else fr_name
            
            self.stage_label.update_text(display_text, display_text)
            
            if self.base_logic.speaker:
                self.base_logic.speaker.output(
                    f"Stage {self.current_stage} started!" if self.is_english
                    else f"L'étape {self.current_stage} a commencé !"
                )
            
            self._next_target()
        elif self.current_stage == 3:
            # Stage 3 complete - check accuracy
            self._complete_mandatory_stages()
        else:
            # Bonus stage (4+) complete - offer to continue or exit
            self._complete_bonus_stage()

    def _complete_mandatory_stages(self):
        """Handle completion of mandatory Stage 3."""
        self.session_timer.stop()
        self.target_timer.stop()
        self.message_timer.stop()

        total = self.correct_count + self.incorrect_count
        self.session_accuracy = (self.correct_count / total * 100) if total > 0 else 0.0

        if self.session_accuracy < 70:
            self.failed_mode = True
            self._show_failure_page()
        else:
            # Mandatory stages passed - can continue or exit
            self._show_stage3_complete_page()

    def _complete_bonus_stage(self):
        """Handle completion of a bonus stage (Stage 4+)."""
        self.session_timer.stop()
        self.target_timer.stop()
        self.message_timer.stop()

        # Calculate accuracy for this entire session
        total = self.correct_count + self.incorrect_count
        self.session_accuracy = (self.correct_count / total * 100) if total > 0 else 0.0

        # Show bonus stage completion with option to continue
        if self.is_english:
            title = f"STAGE {self.current_stage} COMPLETE"
            stats_text = (
                f"Stage Accuracy: {self.session_accuracy:.1f}%\n"
                f"Highest Combo This Stage: {self.highest_combo:.2f}\n"
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
                f"Combo le Plus Élevé de cette Étape : {self.highest_combo:.2f}\n"
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
        title_label.setStyleSheet(
            "font-size: 26px; font-weight: bold; color: #0fecb0;"
            "background-color: transparent; border: none; padding: 6px;"
        )
        layout.addWidget(title_label)

        stats_browser = AccessibleBrowser(text=stats_text, accessible_text=stats_text)
        stats_browser.setMinimumHeight(220)
        layout.addWidget(stats_browser)

        btn_layout = QHBoxLayout()

        btn_continue = QPushButton(btn_continue_text)
        btn_continue.clicked.connect(self._continue_to_next_bonus_stage)
        btn_layout.addWidget(btn_continue)

        btn_return = QPushButton(btn_return_text)
        btn_return.clicked.connect(lambda: self._exit_bonus_stages(dlg))
        btn_layout.addWidget(btn_return)

        layout.addLayout(btn_layout)
        dlg.setLayout(layout)
        dlg.exec_()

    def _continue_to_next_bonus_stage(self):
        """Continue from current bonus stage to the next one."""
        # Apply bonus stage rewards
        if self.parent_challenge and hasattr(self.parent_challenge, 'logic'):
            logic = self.parent_challenge.logic
            logic.add_xp(20)
            logic.boss_health = max(0, logic.boss_health - 5)

        # Move to next bonus stage
        self.combo_score = 0.01  # Reset for new stage
        self.current_stage += 1
        self.highest_combo = 0.01  # Reset highest for new stage
        self.stage_start_time = time.time()
        
        stage_names = {
            4: ("Stage 4 – Four Character Combos", "Étape 4 – Combos de Quatre Caractères"),
            5: ("Stage 5 – Five Character Combos", "Étape 5 – Combos de Cinq Caractères"),
        }
        eng_name, fr_name = stage_names.get(
            self.current_stage, 
            (f"Stage {self.current_stage} – Bonus Challenge", 
             f"Étape {self.current_stage} – Défi Bonus")
        )
        display_text = eng_name if self.is_english else fr_name
        
        self.stage_label.update_text(display_text, display_text)
        
        if self.base_logic.speaker:
            self.base_logic.speaker.output(
                f"Bonus Stage {self.current_stage} started!" if self.is_english
                else f"L'étape bonus {self.current_stage} a commencé !"
            )
        
        self.session_timer.start(1000)
        self._next_target()

    def _exit_bonus_stages(self, dialog):
        """Exit from bonus stages and return to battle."""
        dialog.accept()
        
        # Apply final bonus stage rewards before exiting
        if self.parent_challenge and hasattr(self.parent_challenge, 'logic'):
            logic = self.parent_challenge.logic
            logic.add_xp(20)
            logic.boss_health = max(0, logic.boss_health - 5)
            logic.save_progress()
            self.parent_challenge.update_display()
        
        # Show final results and return
        self._show_final_results_page()

    def _show_failure_page(self):
        """Show failure screen when accuracy < 70%."""
        if self.is_english:
            title = "ACCURACY TOO LOW"
            message = (
                f"Final Accuracy: {self.session_accuracy:.1f}%\n\n"
                f"You need at least 70% accuracy to complete Combo Mode.\n"
                f"Please try again later!"
            )
            button_text = "Return to Challenge Battle"
        else:
            title = "PRÉCISION INSUFFISANTE"
            message = (
                f"Précision Finale : {self.session_accuracy:.1f} %\n\n"
                f"Vous avez besoin d'au moins 70 % de précision pour terminer le Mode Combo.\n"
                f"Veuillez réessayer plus tard !"
            )
            button_text = "Retour au Combat de Défi"

        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setMinimumWidth(520)
        dlg.setStyleSheet(self.styleSheet())

        layout = QVBoxLayout()

        title_label = AccessibleLabel(visual_text=title, accessible_text=title)
        title_label.setStyleSheet(
            "font-size: 26px; font-weight: bold; color: #e94560;"
            "background-color: transparent; border: none; padding: 6px;"
        )
        layout.addWidget(title_label)

        msg_browser = AccessibleBrowser(text=message, accessible_text=message)
        msg_browser.setMinimumHeight(180)
        layout.addWidget(msg_browser)

        btn_return = QPushButton(button_text)
        btn_return.clicked.connect(lambda: self._return_to_challenge(dlg))
        layout.addWidget(btn_return)

        dlg.setLayout(layout)
        dlg.exec_()

    def _show_stage3_complete_page(self):
        """Show completion screen with option to continue or return."""
        if self.is_english:
            title = "STAGE 3 COMPLETE"
            stats_text = (
                f"Correct Answers: {self.correct_count}\n"
                f"Incorrect Answers: {self.incorrect_count}\n"
                f"Timeouts: {self.timeout_count}\n"
                f"Final Accuracy: {self.session_accuracy:.1f}%\n"
                f"Highest Combo Score: {self.highest_combo:.2f}\n"
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
                f"Score Combo le Plus Élevé : {self.highest_combo:.2f}\n"
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
        title_label.setStyleSheet(
            "font-size: 26px; font-weight: bold; color: #0fecb0;"
            "background-color: transparent; border: none; padding: 6px;"
        )
        layout.addWidget(title_label)

        stats_browser = AccessibleBrowser(text=stats_text, accessible_text=stats_text)
        stats_browser.setMinimumHeight(260)
        layout.addWidget(stats_browser)

        btn_layout = QHBoxLayout()

        btn_continue = QPushButton(btn_continue_text)
        btn_continue.clicked.connect(self._continue_to_next_bonus_stage)
        btn_layout.addWidget(btn_continue)

        btn_return = QPushButton(btn_return_text)
        btn_return.clicked.connect(lambda: self._end_session_and_return(dlg))
        btn_layout.addWidget(btn_return)

        layout.addLayout(btn_layout)
        dlg.setLayout(layout)
        dlg.exec_()


    def _end_session_and_return(self, dialog):
        """End the session after Stage 3 completion (success) and return to battle."""
        dialog.accept()
        
        # Final XP conversion from the completed stage
        self._convert_stage_xp()
        
        # Update challenge state with success rewards
        self._update_challenge_state_success()
        self._show_final_results_page()

    def _update_displays(self):
        """Update all display labels."""
        # XP label with 1 decimal place
        v = f"XP Balance: {self.xp_earned:.1f}" if self.is_english else f"Solde XP : {self.xp_earned:.1f}"
        a = f"{self.xp_earned:.1f} XP earned" if self.is_english else f"{self.xp_earned:.1f} XP gagnés"
        self.xp_label.update_text(v, a)

        # Combo score label with 2 decimal places
        v = f"Combo Score: {self.combo_score:.2f}" if self.is_english else f"Score Combo : {self.combo_score:.2f}"
        a = f"Current combo score is {self.combo_score:.2f}" if self.is_english else f"Le score de combo actuel est {self.combo_score:.2f}"
        self.combo_score_label.update_text(v, a)

    def get_xp_multiplier(self, stage):
        """Get XP conversion multiplier for a stage. Linear scaling: stage / 10."""
        return stage / 10.0

    def _update_challenge_state_success(self):
        """Update challenge state after successful Combo Mode completion."""
        if not (self.parent_challenge and hasattr(self.parent_challenge, 'logic')):
            return
        
        logic = self.parent_challenge.logic
        
        # Add base completion reward
        logic.add_xp(40)
        logic.boss_health = max(0, logic.boss_health - 15)
        
        logic.modes["combo"]["status"] = "done"
        logic.modes["combo"]["completed"] = True
        logic.completed_modes_count = sum(
            1 for v in logic.modes.values() if v["completed"]
        )
        
        # Unlock other modes
        for mk, data in logic.modes.items():
            if mk != "crazy_party" and not data["completed"]:
                data["status"] = "unlocked"
        
        logic.save_progress()
        self.parent_challenge.update_display()

    def _show_final_results_page(self):
        """Show final results after mode completion."""
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
        title_label.setStyleSheet(
            "font-size: 26px; font-weight: bold; color: #0fecb0;"
            "background-color: transparent; border: none; padding: 6px;"
        )
        layout.addWidget(title_label)

        msg_browser = AccessibleBrowser(text=message, accessible_text=message)
        msg_browser.setMinimumHeight(240)
        layout.addWidget(msg_browser)

        btn_return = QPushButton(button_text)
        btn_return.clicked.connect(lambda: self._return_to_challenge(dlg))
        layout.addWidget(btn_return)

        dlg.setLayout(layout)
        dlg.exec_()

    def leave_session(self):
        """Exit early - penalty and cleanup."""
        self.session_timer.stop()
        self.target_timer.stop()
        self.message_timer.stop()

        # Delete combo CSV on exit
        if self.combo_csv_path and os.path.exists(self.combo_csv_path):
            try:
                os.remove(self.combo_csv_path)
            except Exception:
                pass

        # Apply penalty
        if self.parent_challenge and hasattr(self.parent_challenge, 'logic'):
            logic = self.parent_challenge.logic
            logic.xp_balance = max(0, logic.xp_balance - 50)
            logic.save_progress()
            self.parent_challenge.update_display()

        if self.base_logic.speaker:
            msg = (
                "Combo session exited. 50 XP penalty applied."
                if self.is_english else
                "Session Combo quittée. Pénalité de 50 XP appliquée."
            )
            self.base_logic.speaker.output(msg)

        if self.parent_challenge:
            self.parent_challenge.pages.setCurrentIndex(1)
        self.close()

    def _return_to_challenge(self, dialog):
        """Return to main challenge battle."""
        dialog.accept()
        if self.parent_challenge:
            self.parent_challenge.pages.setCurrentIndex(1)
            self.parent_challenge.update_display()
        self.close()


# ============= WEEK 6 LOGIC =============

class Week6Logic:
    """
    Logic layer for Week 6 challenge.
    Manages XP, boss health, rank, mode progression, CSV persistence.
    """

    def __init__(self, base_logic, user_name="", is_english=True):
        self.base_logic  = base_logic
        self.user_name   = user_name
        self.is_english  = is_english

        self.xp_balance  = 50
        self.xp_max      = 1500
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
        self.csv_file_path         = None
        self.progress_loaded       = False

        self.load_progress()

    def get_rank_from_xp(self):
        if self.is_english:
            if self.xp_balance < 300:  return "Beginner"
            if self.xp_balance < 600:  return "Challenger"
            if self.xp_balance < 900:  return "Elite Typer"
            if self.xp_balance < 1200: return "Warrior"
            return "Master"
        else:
            if self.xp_balance < 300:  return "Débutant"
            if self.xp_balance < 600:  return "Challenger"
            if self.xp_balance < 900:  return "Typer Élite"
            if self.xp_balance < 1200: return "Guerrier"
            return "Maître"

    def add_xp(self, amount):
        self.xp_balance = min(self.xp_balance + amount, self.xp_max)

    def mark_mode_complete(self, mode_key):
        mode = self.modes[mode_key]
        if mode["status"] == "done" or mode["completed"]:
            return
        mode["status"]    = "done"
        mode["completed"] = True
        self.completed_modes_count += 1
        self.boss_health = max(0, self.boss_health - 20)
        self.add_xp(225)
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
            if mode["completed"]:    return "[completed]  -  Press to replay"
            if mode["status"] == "locked":
                return ("[locked]  -  Finish all modes above to unlock"
                        if mode_key == "crazy_party" else
                        "[locked]  -  Complete Warmup Gate to unlock")
            return "[open]  -  Press Enter to start"
        else:
            if mode["completed"]:    return "[complété]  -  Appuyez pour rejouer"
            if mode["status"] == "locked":
                return ("[verrouillé]  -  Terminez les modes au-dessus pour déverrouiller"
                        if mode_key == "crazy_party" else
                        "[verrouillé]  -  Terminez le Warmup Gate pour déverrouiller")
            return "[ouvert]  -  Appuyez Entrée pour commencer"

    def is_challenge_complete(self):
        return self.xp_balance >= self.xp_max and self.modes["crazy_party"]["completed"]

    def load_progress(self):
        if not self.user_name:
            return
        clean_name = self.base_logic.get_clean_username()
        if not clean_name:
            return
        csv_path = os.path.join(
            self.base_logic.data_dir, clean_name,
            f"{clean_name}_Week6_Challenge.csv"
        )
        if not os.path.exists(csv_path):
            return
        try:
            last_row = None
            with open(csv_path, 'r', newline='', encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    last_row = row
            if last_row is None:
                return
            self.xp_balance  = int(float(last_row["XP Balance"]))
            self.boss_health = int(float(last_row["Boss Health"]))
            completed_str    = last_row.get("Completed Modes", "none").strip()
            completed_keys   = (
                [k.strip() for k in completed_str.split(",")
                 if k.strip() in self.modes]
                if completed_str.lower() != "none" else []
            )
            for mk in completed_keys:
                self.modes[mk]["status"]    = "done"
                self.modes[mk]["completed"] = True
            self.completed_modes_count = len(completed_keys)
            if self.completed_modes_count >= 1:
                for mk, data in self.modes.items():
                    if mk != "crazy_party" and not data["completed"]:
                        data["status"] = "unlocked"
            if self.completed_modes_count >= 5:
                if not self.modes["crazy_party"]["completed"]:
                    self.modes["crazy_party"]["status"] = "unlocked"
            self.csv_file_path   = csv_path
            self.progress_loaded = True
        except Exception:
            pass

    def init_challenge_progress_file(self):
        if not self.user_name:
            return
        clean_name = self.base_logic.get_clean_username()
        user_dir   = os.path.join(self.base_logic.data_dir, clean_name)
        os.makedirs(user_dir, exist_ok=True)
        self.csv_file_path = os.path.join(
            user_dir, f"{clean_name}_Week6_Challenge.csv"
        )
        file_exists = os.path.exists(self.csv_file_path)
        try:
            with open(self.csv_file_path, 'a', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                if not file_exists:
                    w.writerow(["Timestamp", "XP Balance", "Boss Health",
                                "Completed Modes", "Modes Status"])
                completed = [k for k, v in self.modes.items() if v["completed"]]
                w.writerow([
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    self.xp_balance, self.boss_health,
                    ",".join(completed) if completed else "none",
                    str(self.modes),
                ])
        except Exception:
            pass

    def save_progress(self):
        if not self.csv_file_path:
            return
        try:
            with open(self.csv_file_path, 'a', newline='', encoding='utf-8') as f:
                completed = [k for k, v in self.modes.items() if v["completed"]]
                csv.writer(f).writerow([
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    self.xp_balance, self.boss_health,
                    ",".join(completed) if completed else "none",
                    str(self.modes),
                ])
        except Exception:
            pass


# ============= WEEK 6 UI =============

class Week6UI(QWidget):
    """
    UI layer for Week 6 Challenge Battle.
    Page 0 = identification (bypassed at runtime).
    Page 1 = challenge battle.
    Page 2 = victory.
    """

    def __init__(self, base_logic, user_name="", is_english=True):
        super().__init__()
        self.base_logic  = base_logic
        self.base_logic.user_name = user_name
        self.is_english  = is_english

        self.set_lang_strings()
        self.logic = Week6Logic(base_logic, user_name, is_english)

        self.setWindowTitle(self.strings["window_title"])
        self.setWindowState(Qt.WindowMaximized)

        self.setStyleSheet("""
            QWidget      { background-color: #0a0a12; color: #ffffff;
                           font-family: Arial; font-size: 24px; }
            QPushButton  { background-color: #16213e; border-radius: 12px;
                           padding: 15px; color: white;
                           border: 2px solid #e94560; margin: 5px; }
            QPushButton:hover    { background-color: #e94560; }
            QPushButton:disabled { background-color: #444444;
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

    # ---- Strings ----

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

    # ---- Pages ----

    def _setup_identification_page(self):
        """Page 0  -  kept for standalone use; bypassed at runtime."""
        page   = QWidget()
        layout = QVBoxLayout()

        title = AccessibleLabel(
            visual_text=self.strings["id_title"],
            accessible_text=self.strings["id_title"],
        )
        title.setStyleSheet(
            "font-size: 30px; font-weight: bold; color: #e94560;"
            "background-color: transparent; border: none;"
        )
        layout.addWidget(title)

        instructions = AccessibleBrowser(
            text=self.strings["id_instructions"],
            accessible_text=self.strings["id_instructions"],
        )
        instructions.setMinimumHeight(150)
        layout.addWidget(instructions)

        btn_row   = QHBoxLayout()
        btn_start = QPushButton(self.strings["id_button_start"])
        btn_start.clicked.connect(self.start_challenge)
        btn_row.addWidget(btn_start)

        btn_back  = QPushButton(self.strings["id_button_back"])
        btn_back.clicked.connect(self._go_back)
        btn_row.addWidget(btn_back)

        layout.addLayout(btn_row)
        layout.addStretch()
        page.setLayout(layout)
        self.pages.addWidget(page)

    def _setup_challenge_page(self):
        """Page 1  -  main challenge battle."""
        page   = QWidget()
        layout = QVBoxLayout()

        title = AccessibleLabel(
            visual_text=self.strings["challenge_title"],
            accessible_text=self.strings["challenge_title"],
        )
        title.setStyleSheet(
            "font-size: 30px; font-weight: bold; color: #0fecb0;"
            "background-color: transparent; border: none;"
        )
        layout.addWidget(title)

        # Stats row
        stats_layout = QHBoxLayout()

        self.xp_display = AccessibleLabel(
            visual_text=self.strings["xp_visual"].format(xp=50, xp_max=1500),
            accessible_text=self.strings["xp_accessible"].format(xp=50, xp_max=1500),
        )
        stats_layout.addWidget(self.xp_display)

        self.health_display = AccessibleLabel(
            visual_text=self.strings["health_visual"].format(health=100),
            accessible_text=self.strings["health_accessible"].format(health=100),
        )
        stats_layout.addWidget(self.health_display)

        init_rank = self.logic.get_rank_from_xp()
        self.rank_display = AccessibleLabel(
            visual_text=self.strings["rank_visual"].format(rank=init_rank),
            accessible_text=self.strings["rank_accessible"].format(rank=init_rank),
        )
        stats_layout.addWidget(self.rank_display)

        layout.addLayout(stats_layout)

        # Separator
        sep = AccessibleLabel(visual_text="-" * 40, accessible_text="")
        sep.setStyleSheet(
            "color: #444; background: transparent; border: none; font-size: 16px;"
        )
        layout.addWidget(sep)

        # Modes header
        modes_header = AccessibleLabel(
            visual_text=self.strings["modes_header"],
            accessible_text=self.strings["modes_header"],
        )
        modes_header.setStyleSheet(
            "font-weight: bold; color: #f9d342;"
            "background-color: transparent; border: none; font-size: 20px;"
        )
        layout.addWidget(modes_header)

        self.mode_buttons = {}
        for mode_key in ["warmup", "combo", "precision", "sentence", "survival", "crazy_party"]:
            data        = self.logic.modes[mode_key]
            status_text = self.logic.get_mode_status_text(mode_key)
            btn = QPushButton(f"{data['name']}  {status_text}")
            btn.clicked.connect(lambda checked, mk=mode_key: self._on_mode_clicked(mk))
            self.mode_buttons[mode_key] = btn
            layout.addWidget(btn)

        btn_exit = QPushButton(self.strings["button_exit"])
        btn_exit.clicked.connect(self._exit_challenge)
        layout.addWidget(btn_exit)

        page.setLayout(layout)
        self.pages.addWidget(page)

    def _setup_victory_page(self):
        """Page 2  -  victory screen."""
        page   = QWidget()
        layout = QVBoxLayout()

        title = AccessibleLabel(
            visual_text=self.strings["victory_title"],
            accessible_text=self.strings["victory_title"],
        )
        title.setStyleSheet(
            "font-size: 38px; font-weight: bold; color: #0fecb0;"
            "background-color: transparent; border: none;"
        )
        layout.addWidget(title)

        message = AccessibleLabel(
            visual_text=self.strings["victory_message"],
            accessible_text=self.strings["victory_accessible"],
        )
        message.setMinimumHeight(100)
        layout.addWidget(message)

        btn_ok = QPushButton(self.strings["victory_button"])
        btn_ok.clicked.connect(self._on_victory_complete)
        layout.addWidget(btn_ok)

        layout.addStretch()
        page.setLayout(layout)
        self.pages.addWidget(page)

    # ---- Actions ----

    def start_challenge(self):
        """Jump straight to battle page and refresh from loaded state."""
        self.logic.init_challenge_progress_file()
        self.pages.setCurrentIndex(1)
        self.update_display()
        if self.base_logic.speaker:
            key = "progress_loaded" if self.logic.progress_loaded else "progress_fresh"
            self.base_logic.speaker.output(
                self.strings[key].format(name=self.logic.user_name)
            )

    def _on_mode_clicked(self, mode_key):
        mode = self.logic.modes[mode_key]

        if mode["status"] == "locked":
            if self.base_logic.speaker:
                key = "locked_crazy" if mode_key == "crazy_party" else "locked_other"
                self.base_logic.speaker.output(self.strings[key])
            return

        # Warmup  -  launch actual session
        if mode_key == "warmup":
            if self.base_logic.speaker:
                self.base_logic.speaker.output(
                    self.strings["mode_started"].format(name=mode["name"])
                )
            self._start_warmup_typing()
            return

        # Combo  -  launch actual session
        if mode_key == "combo":
            if self.base_logic.speaker:
                self.base_logic.speaker.output(
                    self.strings["mode_started"].format(name=mode["name"])
                )
            self._start_combo_typing()
            return

        # Other modes (placeholder until implemented)
        if not mode["completed"]:
            self.logic.mark_mode_complete(mode_key)
            self.logic.save_progress()
            self.update_display()
            if self.base_logic.speaker:
                self.base_logic.speaker.output(
                    self.strings["mode_completed"].format(name=mode["name"])
                )
            if self.logic.is_challenge_complete():
                self.logic.save_progress()
                self.pages.setCurrentIndex(2)
                if self.base_logic.speaker:
                    self.base_logic.speaker.output(self.strings["boss_defeated"])
                winsound.Beep(2000, 300)
        else:
            if self.base_logic.speaker:
                self.base_logic.speaker.output(
                    self.strings["mode_replay"].format(name=mode["name"])
                )

    def _start_warmup_typing(self):
        """Show the warmup welcome page as a separate maximised window."""
        self.warmup_welcome = WarmupWelcomePage(self, is_english=self.is_english)
        self.warmup_welcome.setStyleSheet(self.styleSheet())
        self.warmup_welcome.setWindowTitle(
            "Warmup Gate" if self.is_english else "Porte Réchauffement"
        )
        self.warmup_welcome.setWindowState(Qt.WindowMaximized)
        self.warmup_welcome.show()

    def _start_combo_typing(self):
        """Show the combo welcome page as a separate maximised window."""
        self.combo_welcome = ComboWelcomePage(self, is_english=self.is_english)
        self.combo_welcome.setStyleSheet(self.styleSheet())
        self.combo_welcome.setWindowTitle(
            "Combo Rush" if self.is_english else "Combo Rush"
        )
        self.combo_welcome.setWindowState(Qt.WindowMaximized)
        self.combo_welcome.show()

    def launch_warmup_session(self):
        """Called by WarmupWelcomePage when user presses 'I Am Ready'."""
        self.warmup_mode = GenericTypingMode(
            base_logic=self.base_logic,
            mode_name="Warmup Gate",
            is_english=self.is_english,
            parent=self,
        )
        self.warmup_mode.setStyleSheet(self.styleSheet())
        self.warmup_mode.setWindowTitle(
            "Warmup Gate  -  Typing Session"
            if self.is_english else
            "Porte Réchauffement  -  Session de Frappe"
        )
        self.warmup_mode.setWindowState(Qt.WindowMaximized)
        self.warmup_mode.show()
        self.warmup_mode.start_session()

    def launch_combo_session(self):
        """Called by ComboWelcomePage when user presses 'I Am Ready'."""
        self.combo_mode = ComboTypingMode(
            base_logic=self.base_logic,
            is_english=self.is_english,
            parent=self,
        )
        self.combo_mode.setStyleSheet(self.styleSheet())
        self.combo_mode.setWindowTitle(
            "Combo Rush  -  Typing Session"
            if self.is_english else
            "Combo Rush  -  Session de Frappe"
        )
        self.combo_mode.setWindowState(Qt.WindowMaximized)
        self.combo_mode.show()
        self.combo_mode.start_session()

    def update_display(self):
        """Refresh all stat widgets from current logic state."""
        xp, mx = self.logic.xp_balance, self.logic.xp_max
        self.xp_display.update_text(
            self.strings["xp_visual"].format(xp=xp, xp_max=mx),
            self.strings["xp_accessible"].format(xp=xp, xp_max=mx),
        )
        h = self.logic.boss_health
        self.health_display.update_text(
            self.strings["health_visual"].format(health=h),
            self.strings["health_accessible"].format(health=h),
        )
        rank = self.logic.get_rank_from_xp()
        self.rank_display.update_text(
            self.strings["rank_visual"].format(rank=rank),
            self.strings["rank_accessible"].format(rank=rank),
        )
        for mode_key, btn in self.mode_buttons.items():
            data        = self.logic.modes[mode_key]
            status_text = self.logic.get_mode_status_text(mode_key)
            btn.setText(f"{data['name']}  {status_text}")

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
