# Blind Keyboard Master - Survival Mode
# 15-minute endurance challenge for Week 6
# Self-contained: GUI + gameplay logic in one file.
# Copyright (C) 2026 Louay Cherif - Apache License 2.0

import random
import winsound
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QLabel, QDialog, QTextBrowser, QApplication)
from PyQt5.QtCore import Qt, QTimer
from weeks import symbol_pronounciation, w6words
from static.accessible_widgets import AccessiblePushButton, AccessibleLabel, AccessibleBrowser


# Create aliases for backward compatibility with existing code
SurvivalAccessibleLabel = AccessibleLabel
SurvivalAccessibleBrowser = AccessibleBrowser


class SurvivalTypingInput(QLineEdit):
    """
    Typing field.
    - Ctrl key repeats the current target.
    - Any other key press interrupts TTS and resumes timers immediately.
    """

    def __init__(self, mode, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = mode

    def keyPressEvent(self, event):
        # Ctrl alone: repeat target, do NOT resume timers
        if event.key() == Qt.Key_Control:
            self.mode.repeat_current_target()
            return

        # Any other key: interrupt TTS and resume timers, then let Qt handle the key
        self.mode.on_typing_key_pressed()
        super().keyPressEvent(event)


# ============= SURVIVAL MODE =============

class SurvivalMode(QWidget):
    """
    15-minute endurance challenge.
    3 hearts + danger bar (0-10). Danger 10 = heart lost + reset.
    Success  = survive full 15 min.
    Failure  = all hearts lost before time runs out.
    Rewards  = 200 XP, -20% boss health (fixed, no performance grading).
    """

    SESSION_DURATION = 900   # 15 minutes in seconds

    # Phase boundaries in elapsed seconds
    PHASE_BOUNDS = [
        (0,   180, "Initial Phase",   "Phase Initiale"),
        (180, 360, "Capital Arrival", "Arrivee Majuscules"),
        (360, 420, "Symbol Arrival",  "Arrivee Symboles"),
        (420, 600, "Couple Arrival",  "Arrivee Couples"),
        (600, 900, "Final Phase",     "Phase Finale"),
    ]

    def __init__(self, base_logic, is_english=True, parent=None):
        super().__init__()
        self.setWindowFlag(Qt.Window, True)
        self.setWindowModality(Qt.ApplicationModal)

        self.base_logic       = base_logic
        self.is_english       = is_english
        self.parent_challenge = parent

        # Session state
        self.elapsed_seconds  = 0
        self.current_hearts   = 3
        self.current_danger   = 0
        self.current_target   = ""
        self.countdown_value  = 3

        # TTS state
        self._tts_waiting     = False
        self._tts_timers      = []

        self._build_ui()
        self._build_timers()

    # ============= UI CONSTRUCTION =============

    def _build_ui(self):
        self.setStyleSheet("""
            QWidget     { background-color: #0f1626; color: #f9d342;
                          font-family: Arial; font-size: 22px; }
            QPushButton { background-color: #16213e; border-radius: 10px;
                          padding: 14px; color: white;
                          border: 2px solid #e94560; margin: 4px; }
            QPushButton:hover { background-color: #e94560; }
            QLineEdit   { padding: 14px; background-color: #131b36;
                          color: #f9d342; border: 2px solid #f9d342;
                          border-radius: 10px; font-size: 28px; }
        """)

        root = QVBoxLayout()
        root.setSpacing(14)

        # Phase label
        self.phase_label = SurvivalAccessibleLabel(
            "Initial Phase",
            "Current phase: Initial Phase. Lowercase letters only."
        )
        root.addWidget(self.phase_label)

        # Session timer
        self.timer_display = SurvivalAccessibleLabel(
            "15:00",
            "Remaining session time: 15 minutes."
        )
        root.addWidget(self.timer_display)

        # Hearts
        self.hearts_display = SurvivalAccessibleLabel(
            "Hearts: 3 / 3",
            "Hearts remaining: 3 out of 3."
        )
        root.addWidget(self.hearts_display)

        # Danger bar
        self.danger_display = SurvivalAccessibleLabel(
            "Danger: 0 / 10",
            "Danger level: 0 out of 10."
        )
        root.addWidget(self.danger_display)

        # Target display - large font
        self.target_display = SurvivalAccessibleLabel("", "Current target.")
        self.target_display.setStyleSheet(
            "padding: 12px; background-color: #1a1a2e; color: #f9d342;"
            "border: 2px solid #f9d342; border-radius: 10px;"
            "font-size: 52px; min-height: 110px;"
        )
        root.addWidget(self.target_display)

        # Countdown overlay (hidden during play)
        self.countdown_display = SurvivalAccessibleLabel("", "Countdown.")
        self.countdown_display.setStyleSheet(
            "padding: 12px; background-color: #1a1a2e; color: #0fecb0;"
            "border: 2px solid #0fecb0; border-radius: 10px;"
            "font-size: 72px; min-height: 120px;"
        )
        self.countdown_display.setVisible(False)
        root.addWidget(self.countdown_display)

        # Typing input - focus set here on gameplay start
        self.input_field = SurvivalTypingInput(self)
        self.input_field.setAccessibleName(
            "Typing field. Type the displayed target."
            if self.is_english else
            "Champ de saisie. Tapez la cible affichee."
        )
        self.input_field.textChanged.connect(self._on_input_changed)
        root.addWidget(self.input_field)

        # Help hint
        hint = (
            "Ctrl repeats the current target. Incorrect answers and timeouts increase danger."
            if self.is_english else
            "Ctrl repete la cible. Les erreurs et delais augmentent le danger."
        )
        self.hint_label = SurvivalAccessibleLabel(hint, hint)
        self.hint_label.setStyleSheet(
            "padding: 8px; background-color: transparent;"
            "color: #888888; border: none; font-size: 16px;"
        )
        root.addWidget(self.hint_label)

        # Quit button
        quit_text = "Quit" if self.is_english else "Quitter"
        self.quit_btn = AccessiblePushButton(quit_text)
        self.quit_btn.clicked.connect(self._on_quit)
        root.addWidget(self.quit_btn)

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

    # ============= SESSION ENTRY POINT =============

    def start_session(self):
        """Show welcome dialog. If accepted, begin countdown then gameplay."""
        if not self._show_welcome_dialog():
            return

        self._reset_state()
        self.setWindowState(Qt.WindowMaximized)
        self.show()
        self.raise_()
        self.activateWindow()

        # Start 3-second countdown
        self.countdown_display.setVisible(True)
        self.countdown_display.update_text(
            str(self.countdown_value),
            f"Countdown: {self.countdown_value}."
        )
        self.countdown_timer.start()

    def _reset_state(self):
        self.elapsed_seconds = 0
        self.current_hearts  = 3
        self.current_danger  = 0
        self.current_target  = ""
        self.countdown_value = 3
        self._tts_waiting    = False
        self._clear_tts_timers()
        self.session_timer.stop()
        self.target_timer.stop()
        self.countdown_timer.stop()
        self.input_field.clear()
        self._refresh_display()

    # ============= WELCOME DIALOG =============

    def _show_welcome_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle(
            "Survival Gate" if self.is_english else "Porte de Survie"
        )
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.setMinimumWidth(600)
        dlg.setStyleSheet("""
            QDialog     { background-color: #0a0a12; color: #ffffff;
                          font-family: Arial; font-size: 22px; }
            QPushButton { background-color: #16213e; border-radius: 10px;
                          padding: 14px; color: white;
                          border: 2px solid #e94560; margin: 4px; }
            QPushButton:hover { background-color: #e94560; }
        """)

        layout = QVBoxLayout()

        title = SurvivalAccessibleLabel(
            "SURVIVAL GATE" if self.is_english else "PORTE DE SURVIE",
            "Survival Gate - welcome screen" if self.is_english else "Porte de Survie - ecran d'accueil"
        )
        title.setStyleSheet(
            "font-size: 28px; font-weight: bold; color: #0fecb0;"
            "background: transparent; border: none; padding: 8px;"
        )
        layout.addWidget(title)

        if self.is_english:
            description = (
                "SURVIVAL GATE: A 15-minute endurance challenge.\n\n"
                "You start with 3 hearts and a danger bar from 0 to 10.\n"
                "Each incorrect answer adds 1 danger.\n"
                "Each timeout adds 2 danger.\n"
                "When danger reaches 10, you lose one heart and the bar resets.\n\n"
                "Lose all 3 hearts before 15 minutes: FAILURE.\n"
                "Survive the full 15 minutes: SUCCESS.\n\n"
                "5 PHASES:\n"
                "- Initial Phase (3 min): lowercase letters only\n"
                "- Capital Arrival (3 min): lowercase and uppercase mixed\n"
                "- Symbol Arrival (1 min): letters, symbols and accented chars\n"
                "- Couple Arrival (3 min): character pairs and combinations\n"
                "- Final Phase (5 min): words\n\n"
                "Press Ctrl at any time to repeat the current target.\n"
                "For word targets, the timer pauses while the word is spelled out.\n"
                "Press any key to immediately stop spelling and resume the timer.\n\n"
                "SAVE HEART: If you lose your last heart inside the final 5 minutes,\n"
                "you may spend 70 XP to restore one heart and keep going.\n\n"
                "SUCCESS REWARDS: 200 XP + Boss health -20%.\n"
                "Perfection is NOT required. Only survival counts."
            )
        else:
            description = (
                "PORTE DE SURVIE : Un defi d'endurance de 15 minutes.\n\n"
                "Vous commencez avec 3 coeurs et une jauge de danger de 0 a 10.\n"
                "Chaque reponse incorrecte ajoute 1 danger.\n"
                "Chaque delai ajoute 2 danger.\n"
                "Quand le danger atteint 10, vous perdez un coeur et la jauge recommence.\n\n"
                "Perdre les 3 coeurs avant 15 minutes : ECHEC.\n"
                "Survivre les 15 minutes completes : SUCCES.\n\n"
                "5 PHASES :\n"
                "- Phase Initiale (3 min) : lettres minuscules uniquement\n"
                "- Arrivee Majuscules (3 min) : minuscules et majuscules melangees\n"
                "- Arrivee Symboles (1 min) : lettres, symboles et accents\n"
                "- Arrivee Couples (3 min) : paires et combinaisons de caracteres\n"
                "- Phase Finale (5 min) : mots\n\n"
                "Appuyez sur Ctrl a tout moment pour repeter la cible.\n"
                "Pour les mots, le timer se met en pause pendant l'epellation.\n"
                "Appuyez sur n'importe quelle touche pour arreter l'epellation et reprendre.\n\n"
                "SAUVER UN COEUR : Si vous perdez votre dernier coeur dans les 5 dernieres minutes,\n"
                "vous pouvez depenser 70 XP pour restaurer un coeur et continuer.\n\n"
                "RECOMPENSES DE SUCCES : 200 XP + Sante du Boss -20%.\n"
                "La perfection n'est PAS requise. Seule la survie compte."
            )

        browser = SurvivalAccessibleBrowser(description, description)
        browser.setMinimumHeight(400)
        layout.addWidget(browser)

        btn_row = QHBoxLayout()
        btn_ready = AccessiblePushButton(
            "I'm ready for it!" if self.is_english else "Je suis pret(e) !"
        )
        btn_ready.clicked.connect(dlg.accept)
        btn_row.addWidget(btn_ready)

        btn_not_yet = AccessiblePushButton("Not yet" if self.is_english else "Pas encore")
        btn_not_yet.clicked.connect(dlg.reject)
        btn_row.addWidget(btn_not_yet)

        layout.addLayout(btn_row)
        dlg.setLayout(layout)
        return dlg.exec_() == QDialog.Accepted

    # ============= COUNTDOWN =============

    def _on_countdown_tick(self):
        self.countdown_value -= 1
        if self.countdown_value > 0:
            self.countdown_display.update_text(
                str(self.countdown_value),
                f"Countdown: {self.countdown_value}."
            )
            if self.base_logic.speaker:
                self.base_logic.speaker.output(str(self.countdown_value))
            return

        # Countdown done - hide overlay, start gameplay
        self.countdown_timer.stop()
        self.countdown_display.setVisible(False)
        self.session_timer.start()
        self._next_target()
        # CRITICAL: focus typing field immediately so user can type without Tab
        self.input_field.setFocus()

    # ============= SESSION TICK =============

    def _on_session_tick(self):
        self.elapsed_seconds += 1
        self._refresh_display()
        if self.elapsed_seconds >= self.SESSION_DURATION:
            self._complete_session(success=True)

    # ============= DISPLAY =============

    def _refresh_display(self):
        # Session timer
        remaining = max(0, self.SESSION_DURATION - self.elapsed_seconds)
        m = remaining // 60
        s = remaining % 60
        self.timer_display.update_text(
            f"{m:02d}:{s:02d}",
            f"Session time remaining: {m} minutes {s} seconds."
        )

        # Phase label with time remaining in phase
        phase_en, phase_fr, phase_remaining = self._get_phase_info()
        phase_name = phase_en if self.is_english else phase_fr
        pr_m = phase_remaining // 60
        pr_s = phase_remaining % 60
        visual = f"{phase_name} - {pr_m:02d}:{pr_s:02d} remaining"
        accessible = f"Current phase: {phase_name}. {pr_m} minutes {pr_s} seconds left."
        self.phase_label.update_text(visual, accessible)

        # Hearts
        filled   = "H" * self.current_hearts
        empty    = "-" * (3 - self.current_hearts)
        self.hearts_display.update_text(
            f"Hearts: {self.current_hearts} / 3",
            f"Hearts remaining: {self.current_hearts} out of 3."
        )

        # Danger
        self.danger_display.update_text(
            f"Danger: {self.current_danger} / 10",
            f"Danger level: {self.current_danger} out of 10."
        )

    def _get_phase_info(self):
        """Return (english_name, french_name, seconds_remaining_in_phase)."""
        for start, end, en, fr in self.PHASE_BOUNDS:
            if self.elapsed_seconds < end:
                return en, fr, end - self.elapsed_seconds
        # Past all phases (shouldn't happen but safe fallback)
        return "Final Phase", "Phase Finale", 0

    # ============= TARGET GENERATION =============

    def _generate_target(self):
        t = self.elapsed_seconds
        lowercase = "abcdefghijklmnopqrstuvwxyz"
        uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        symbols   = "".join(symbol_pronounciation.keys())

        if t < 180:
            # Phase 1: lowercase only
            return random.choice(lowercase)

        if t < 360:
            # Phase 2: lowercase + uppercase single char
            return random.choice(lowercase + uppercase)

        if t < 420:
            # Phase 3: lowercase, uppercase, symbols, accented (all single chars)
            pool = lowercase + uppercase + symbols
            return random.choice(pool)

        if t < 600:
            # Phase 4: couples - 2 chars from full pool
            pool = lowercase + uppercase + symbols
            return random.choice(pool) + random.choice(pool)

        # Phase 5: words from w6words; fallback to random 3-char if empty
        if w6words:
            return random.choice(w6words)
        return "".join(random.choice(lowercase) for _ in range(3))

    def _get_pronunciation(self, char):
        """Get TTS announcement for a single character."""
        if char in symbol_pronounciation:
            return symbol_pronounciation[char]
        if char.isupper() and char.isalpha():
            return f"{char.lower()} majuscule"
        return char

    def _get_timeout_ms(self, target):
        """Adaptive timeout based on target complexity."""
        n = len(target)
        if n == 1:
            # Lowercase: 2.2s, uppercase: 3.2s, symbol: 3.8s
            if target in symbol_pronounciation:
                return 3800
            if target.isupper():
                return 3200
            return 2200
        if n == 2:
            return 4500
        # Word: base + per-char
        return 5000 + n * 600

    # ============= TARGET LIFECYCLE =============

    def _next_target(self):
        """Generate, display, announce next target."""
        self.target_timer.stop()
        self._clear_tts_timers()
        self._tts_waiting = False

        self.current_target = self._generate_target()

        self.input_field.blockSignals(True)
        self.input_field.clear()
        self.input_field.blockSignals(False)

        # Build announcement
        ann = self._build_announcement(self.current_target)

        self.target_display.update_text(
            self.current_target,
            ann
        )

        self._announce_target()

    def _build_announcement(self, target):
        """Build the full TTS string for a target."""
        if len(target) == 1:
            return self._get_pronunciation(target)
        # Multi-char: spell letter by letter
        return ", ".join(self._get_pronunciation(c) for c in target)

    def _announce_target(self):
        """Speak the current target via TTS, pausing timers for multi-char."""
        self._clear_tts_timers()
        if not (self.base_logic and getattr(self.base_logic, 'speaker', None)):
            # No speaker - start timer immediately
            self.target_timer.start(self._get_timeout_ms(self.current_target))
            return

        target = self.current_target
        n = len(target)

        if n == 1:
            # Single char: speak pronunciation, start timer immediately
            self.base_logic.speaker.output(self._get_pronunciation(target))
            self.target_timer.start(self._get_timeout_ms(target))
        else:
            # Multi-char: pause both timers, spell out, resume on first keypress
            self._pause_timers()
            # Speak each character with staggered delays
            delay = 0
            for i, char in enumerate(target):
                pron = self._get_pronunciation(char)
                t = QTimer(self)
                t.setSingleShot(True)
                char_delay = delay
                t.timeout.connect(lambda p=pron: self.base_logic.speaker.output(p))
                t.start(char_delay)
                self._tts_timers.append(t)
                delay += len(pron) * 65 + 200

            # Resume timers after all chars have been spoken
            resume_timer = QTimer(self)
            resume_timer.setSingleShot(True)
            resume_timer.timeout.connect(self._resume_timers)
            resume_timer.start(delay + 300)
            self._tts_timers.append(resume_timer)

    def _pause_timers(self):
        self._tts_waiting = True
        self.session_timer.stop()
        self.target_timer.stop()

    def _resume_timers(self):
        if not self._tts_waiting:
            return
        self._tts_waiting = False
        if self.elapsed_seconds < self.SESSION_DURATION:
            if not self.session_timer.isActive():
                self.session_timer.start()
        self.target_timer.start(self._get_timeout_ms(self.current_target))
        try:
            self.input_field.setFocus()
        except Exception:
            pass

    def repeat_current_target(self):
        """Called by Ctrl key - re-announce current target."""
        self._clear_tts_timers()
        self._tts_waiting = False
        self._announce_target()

    def on_typing_key_pressed(self):
        """Called on any non-Ctrl key press. Stops TTS and resumes timers."""
        if self._tts_waiting:
            self._clear_tts_timers()
            self._resume_timers()

    def _clear_tts_timers(self):
        for t in self._tts_timers:
            t.stop()
        self._tts_timers.clear()

    # ============= INPUT HANDLING =============

    def _on_input_changed(self, text):
        if not self.current_target:
            return

        # Prefix match: keep typing
        if self.current_target.startswith(text):
            if text == self.current_target:
                self._on_correct()
            return

        # Wrong character
        winsound.Beep(400, 200)
        self._apply_danger(1)
        self.input_field.blockSignals(True)
        self.input_field.clear()
        self.input_field.blockSignals(False)

    def _on_target_timeout(self):
        winsound.Beep(600, 300)
        self._apply_danger(2)

    def _on_correct(self):
        self._clear_tts_timers()
        self.target_timer.stop()
        self._tts_waiting = False
        winsound.Beep(1500, 100)
        if not self.session_timer.isActive():
            self.session_timer.start()
        self._next_target()
        self.input_field.setFocus()

    # ============= DANGER AND HEARTS =============

    def _apply_danger(self, amount):
        """Add danger. If reaches 10, lose a heart."""
        self._clear_tts_timers()
        self.target_timer.stop()
        self._tts_waiting = False

        self.current_danger = min(10, self.current_danger + amount)
        self._refresh_display()

        if self.current_danger >= 10:
            self.current_danger = 0
            self.current_hearts -= 1
            self._refresh_display()

            # 1.5-second low beep signals heart loss, then 3-second full pause
            winsound.Beep(300, 1500)
            self.session_timer.stop()
            self.input_field.setEnabled(False)

            if self.current_hearts <= 0:
                # Edge case: time ended at exact same moment
                if self.elapsed_seconds >= self.SESSION_DURATION:
                    QTimer.singleShot(3000, lambda: self._complete_session(success=True))
                    return
                # Final 5 minutes: offer save heart after pause
                if self.elapsed_seconds >= self.SESSION_DURATION - 300:
                    QTimer.singleShot(3000, self._offer_save_heart)
                else:
                    QTimer.singleShot(3000, lambda: self._complete_session(success=False))
                return

            # Heart lost but still alive - resume after 3-second pause
            QTimer.singleShot(3000, self._resume_after_heart_loss)
            return

        # No heart lost - resume immediately
        if self.elapsed_seconds < self.SESSION_DURATION:
            if not self.session_timer.isActive():
                self.session_timer.start()
        self._next_target()
        self.input_field.setFocus()

    def _resume_after_heart_loss(self):
        """Called 3 seconds after a heart is lost (but player still alive)."""
        self.input_field.setEnabled(True)
        if self.elapsed_seconds < self.SESSION_DURATION:
            if not self.session_timer.isActive():
                self.session_timer.start()
        self._next_target()
        self.input_field.setFocus()

    # ============= SAVE HEART SCREEN =============

    def _offer_save_heart(self):
        """Show save-heart dialog in the final 5 minutes."""
        self.session_timer.stop()
        self.target_timer.stop()

        dlg = QDialog(self)
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.setWindowTitle(
            "Last Chance" if self.is_english else "Derniere Chance"
        )
        dlg.setMinimumWidth(500)
        dlg.setStyleSheet(self.styleSheet())

        layout = QVBoxLayout()

        title = SurvivalAccessibleLabel(
            "SAVE HEART" if self.is_english else "SAUVER UN COEUR",
            "Save heart screen" if self.is_english else "Ecran sauver un coeur"
        )
        title.setStyleSheet(
            "font-size: 26px; font-weight: bold; color: #e94560;"
            "background: transparent; border: none; padding: 6px;"
        )
        layout.addWidget(title)

        if self.is_english:
            msg = (
                "You lost your last heart inside the final 5 minutes!\n\n"
                "You can spend 70 XP to restore one heart and immediately continue.\n\n"
                "The challenge resumes the moment you agree."
            )
            btn_agree_text = "I agree - spend 70 XP"
            btn_no_text    = "No, let me lose and I'll try again later"
        else:
            msg = (
                "Vous avez perdu votre dernier coeur dans les 5 dernieres minutes !\n\n"
                "Vous pouvez depenser 70 XP pour restaurer un coeur et continuer immediatement.\n\n"
                "Le defi reprend des que vous acceptez."
            )
            btn_agree_text = "Je suis d'accord - depenser 70 XP"
            btn_no_text    = "Non, je vais perdre et reessayer plus tard"

        browser = SurvivalAccessibleBrowser(msg, msg)
        browser.setMinimumHeight(180)
        layout.addWidget(browser)

        btn_row = QHBoxLayout()
        btn_agree = AccessiblePushButton(btn_agree_text)
        btn_agree.clicked.connect(dlg.accept)
        btn_row.addWidget(btn_agree)
        btn_no = AccessiblePushButton(btn_no_text)
        btn_no.clicked.connect(dlg.reject)
        btn_row.addWidget(btn_no)
        layout.addLayout(btn_row)

        dlg.setLayout(layout)

        if dlg.exec_() == QDialog.Accepted:
            logic = getattr(self.parent_challenge, 'logic', None)
            xp    = getattr(logic, 'xp_balance', None) if logic else getattr(self.base_logic, 'xp_balance', None)
            if xp is not None and xp >= 70:
                # Deduct from challenge logic if available, else from base_logic
                if logic and hasattr(logic, 'xp_balance'):
                    logic.xp_balance = max(0, logic.xp_balance - 70)
                else:
                    self.base_logic.xp_balance = max(0, self.base_logic.xp_balance - 70)
                self.current_hearts = 1
                self.current_danger = 0
                self._refresh_display()
                if self.base_logic.speaker:
                    msg_tts = (
                        "One heart restored. Keep going!"
                        if self.is_english else
                        "Un coeur restaure. Continuez !"
                    )
                    self.base_logic.speaker.output(msg_tts)
                # Resume immediately
                self.session_timer.start()
                self._next_target()
                self.input_field.setFocus()
            else:
                if self.base_logic.speaker:
                    msg_tts = (
                        "Not enough XP. Session ended."
                        if self.is_english else
                        "Pas assez de XP. Session terminee."
                    )
                    self.base_logic.speaker.output(msg_tts)
                self._complete_session(success=False)
        else:
            self._complete_session(success=False)

    # ============= SESSION COMPLETION =============

    def _complete_session(self, success):
        """Stop all timers, apply rewards/penalties, show result screen."""
        self._clear_tts_timers()
        self.session_timer.stop()
        self.target_timer.stop()
        self.countdown_timer.stop()

        if success:
            self._apply_success_rewards()
            self._show_success_screen()
        else:
            self._show_failure_screen()   # no XP penalty on heart-loss defeat

        if self.parent_challenge:
            self.parent_challenge.update_display()
            self.parent_challenge.logic.save_progress()

        self.close()

    def _apply_success_rewards(self):
        """Award 200 XP and -20% boss health to challenge logic."""
        logic = getattr(self.parent_challenge, 'logic', None)
        if not logic:
            return
        mode = logic.modes.get('survival')
        if mode and not mode.get('completed'):
            mode['status']    = 'done'
            mode['completed'] = True
            logic.completed_modes_count = sum(
                1 for v in logic.modes.values() if v['completed']
            )
            # Unlock remaining non-crazy modes
            for mk, data in logic.modes.items():
                if mk != 'crazy_party' and not data['completed']:
                    data['status'] = 'unlocked'
            # Unlock crazy party once all 5 others done
            if logic.completed_modes_count >= 5:
                if not logic.modes['crazy_party']['completed']:
                    logic.modes['crazy_party']['status'] = 'unlocked'
        logic.boss_health = max(0, logic.boss_health - 20)
        logic.add_xp(200)

    def _apply_failure_penalty(self):
        """Apply -50 XP penalty. Called ONLY on manual quit, never on heart-loss defeat."""
        logic = getattr(self.parent_challenge, 'logic', None)
        if logic and hasattr(logic, 'xp_balance'):
            logic.xp_balance = max(0, logic.xp_balance - 50)
        elif self.base_logic and hasattr(self.base_logic, 'xp_balance'):
            self.base_logic.xp_balance = max(0, self.base_logic.xp_balance - 50)

    # ============= RESULT SCREENS =============

    def _show_success_screen(self):
        dlg = QDialog(self)
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.setWindowTitle("SUCCESS!" if self.is_english else "SUCCES !")
        dlg.setMinimumWidth(500)
        dlg.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout()

        title = SurvivalAccessibleLabel(
            "VICTORY - You Survived!" if self.is_english else "VICTOIRE - Vous avez survecu !",
            "Success! You survived the full 15 minutes." if self.is_english else "Succes ! Vous avez survecu les 15 minutes completes."
        )
        title.setStyleSheet(
            "font-size: 26px; font-weight: bold; color: #0fecb0;"
            "background: transparent; border: none; padding: 6px;"
        )
        layout.addWidget(title)

        if self.is_english:
            msg = (
                "You survived the full 15 minutes!\n\n"
                "Rewards earned:\n"
                "- 200 XP\n"
                "- Boss health reduced by 20%"
            )
        else:
            msg = (
                "Vous avez survecu les 15 minutes completes !\n\n"
                "Recompenses obtenues :\n"
                "- 200 XP\n"
                "- Sante du boss reduite de 20%"
            )

        browser = SurvivalAccessibleBrowser(msg, msg)
        browser.setMinimumHeight(180)
        layout.addWidget(browser)

        btn = AccessiblePushButton(
            "Return to Challenge Battle" if self.is_english else "Retour au Combat de Defi"
        )
        btn.clicked.connect(dlg.accept)
        layout.addWidget(btn)

        dlg.setLayout(layout)
        dlg.exec_()

    def _show_failure_screen(self):
        dlg = QDialog(self)
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.setWindowTitle("Defeated" if self.is_english else "Vaincu")
        dlg.setMinimumWidth(500)
        dlg.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout()

        title = SurvivalAccessibleLabel(
            "DEFEATED" if self.is_english else "VAINCU",
            "You were defeated." if self.is_english else "Vous avez ete vaincu."
        )
        title.setStyleSheet(
            "font-size: 26px; font-weight: bold; color: #e94560;"
            "background: transparent; border: none; padding: 6px;"
        )
        layout.addWidget(title)

        m = self.elapsed_seconds // 60
        s = self.elapsed_seconds % 60
        if self.is_english:
            msg = (
                f"You survived {m}:{s:02d} before being defeated.\n\n"
                "No penalty applied. Try again to push further!"
            )
        else:
            msg = (
                f"Vous avez survecu {m}:{s:02d} avant d'etre vaincu.\n\n"
                "Aucune penalite appliquee. Recommencez pour aller plus loin !"
            )

        browser = SurvivalAccessibleBrowser(msg, msg)
        browser.setMinimumHeight(160)
        layout.addWidget(browser)

        btn_row = QHBoxLayout()

        btn_retry = AccessiblePushButton("Retry" if self.is_english else "Recommencer")
        btn_retry.clicked.connect(lambda: self._retry_from_failure(dlg))
        btn_row.addWidget(btn_retry)

        btn_back = AccessiblePushButton(
            "Return to Challenge Battle" if self.is_english else "Retour au Combat de Defi"
        )
        btn_back.clicked.connect(dlg.accept)
        btn_row.addWidget(btn_back)

        layout.addLayout(btn_row)
        dlg.setLayout(layout)
        dlg.exec_()

    def _retry_from_failure(self, dialog):
        """Close failure dialog and restart the session."""
        dialog.accept()
        self.start_session()

    # ============= QUIT =============

    def _on_quit(self):
        """Quit button - applies failure penalty."""
        self._clear_tts_timers()
        self.session_timer.stop()
        self.target_timer.stop()
        self.countdown_timer.stop()
        self._apply_failure_penalty()
        if self.parent_challenge:
            self.parent_challenge.update_display()
            self.parent_challenge.logic.save_progress()
        self.close()

    def closeEvent(self, event):
        self._clear_tts_timers()
        self.session_timer.stop()
        self.target_timer.stop()
        self.countdown_timer.stop()
        super().closeEvent(event)
