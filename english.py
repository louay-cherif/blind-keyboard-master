import sys
import winsound
import time
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
                             QLabel, QStackedWidget, QDialog, QApplication)
from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from weeks import Week4Logic


class AppFrontend(QWidget):
    """GUI layer for the typing application. Handles all user interface elements."""
    
    def __init__(self, logic):
        super().__init__()
        self.logic = logic  # Reference to AppBackend instance
        self._base_logic = logic  # Keep original logic reference for Week4Logic initialization
        
        self.setWindowTitle("Adapted Informatics Initiative Official Keyboard typing app for visually impaired people")
        self.resize(800, 600)
        
        # Timer for game mode
        self.timer = QTimer()
        self.timer.timeout.connect(self.time_out)
        
        # Timer for practice adaptivity (every minute)
        self.practice_minute_timer = QTimer()
        self.practice_minute_timer.timeout.connect(self.evaluate_practice_adaptivity)
        
        # Timer for random_timed learning mode
        self.random_timed_timer = QTimer()
        self.random_timed_timer.timeout.connect(self.update_random_timed_target)
        
        # Media player for end-of-week message
        self.player = None
        
        # Apply dark theme stylesheet
        self.setStyleSheet("""
            QWidget { background-color: #0a0a12; color: #ffffff; font-family: Arial; font-size: 24px; }
            QPushButton { background-color: #16213e; border-radius: 12px; padding: 15px; color: white; border: 2px solid #e94560; margin: 5px; }
            QPushButton:hover { background-color: #e94560; }
            QLineEdit { padding: 18px; background-color: #1a1a2e; color: #0fecb0; border: 2px solid #0fecb0; border-radius: 10px; text-align: center; }
            QLineEdit[readOnly="true"] { color: #f9d342; border-color: #f9d342; }
        """)
        
        # Setup pages
        self.pages = QStackedWidget()
        self.setup_week_selection()
        self.setup_identification_page()
        self.setup_learning_page()
        self.setup_practice_selection()
        self.setup_game_page()
        self.setup_week4_entry_page()
        self.setup_week4_game_page()
        self.setup_week4_end_page()
        self.setup_week6_identification_page()
        
        layout = QVBoxLayout()
        layout.addWidget(self.pages)
        self.setLayout(layout)

    def setup_week_selection(self):
        """Page 0: Week selection"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Choose your week:"))
        for i, week in enumerate(self.logic.weeks):
            btn = QPushButton(week["name"])
            btn.clicked.connect(lambda checked, idx=i: self.select_week(idx))
            layout.addWidget(btn)
        btn_quit = QPushButton("Quit Application")
        btn_quit.clicked.connect(self.confirm_quit)
        layout.addWidget(btn_quit)
        page.setLayout(layout)
        self.pages.addWidget(page)

    def confirm_quit(self):
        """Show a confirmation dialog before exiting the app."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Quit")
        dialog.setMinimumWidth(480)
        dialog.setStyleSheet(self.styleSheet())

        layout = QVBoxLayout()

        msg = QLineEdit("Are you sure you want to quit the application?")
        msg.setReadOnly(True)
        msg.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_ok = QPushButton("OK — Quit")
        btn_cancel.clicked.connect(dialog.reject)
        btn_ok.clicked.connect(dialog.accept)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            QApplication.quit()

    def select_week(self, idx):
        """Select a week and move to identification page or special entry"""
        self.logic.current_week_idx = idx
        if idx == 3:
            self.pages.setCurrentIndex(5)  # Week4 entry page
        elif idx == 5:
            self.pages.setCurrentIndex(8)  # Week6 identification page
        else:
            self.pages.setCurrentIndex(1)  # Normal identification page

    def go_back_to_week_selection(self):
        """Go back to week selection and reset everything"""
        self.logic = self._base_logic  # Reset to original logic
        self.logic.reset()
        self.name_input.clear()
        self.pages.setCurrentIndex(0)

    def setup_identification_page(self):
        """Page 1: User identification and mode selection"""
        page = QWidget()
        layout = QVBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your name...")
        btn_learn = QPushButton("Learn")
        btn_practice = QPushButton("Practice")
        btn_retour = QPushButton("Back")
        btn_learn.clicked.connect(self.start_learning)
        btn_practice.clicked.connect(self.start_practice)
        btn_retour.clicked.connect(self.go_back_to_week_selection)
        layout.addWidget(QLabel("IDENTIFICATION"))
        layout.addWidget(self.name_input)
        layout.addWidget(btn_learn)
        layout.addWidget(btn_practice)
        layout.addWidget(btn_retour)
        page.setLayout(layout)
        self.pages.addWidget(page)

    def setup_learning_page(self):
        """Page 2: Learning mode - Input first, Display second"""
        page = QWidget()
        layout = QVBoxLayout()
        
        self.result_output = QLineEdit()
        self.result_output.setReadOnly(True)
        self.result_output.hide()
        
        # 1. مربع الكتابة أصبح هو الأول
        self.learn_input = QLineEdit()
        self.learn_input.textChanged.connect(self.check_learn_input)
        
        # 2. مربع العرض أصبح هو الثاني
        self.char_display_box = QLineEdit()
        self.char_display_box.setReadOnly(True)
        self.char_display_box.setAlignment(Qt.AlignCenter)
        self.char_display_box.setStyleSheet("font-size: 110px; color: #f9d342; border: 3px solid #f9d342; height: 160px;")
        
        self.learn_label = QLabel("")
        self.learn_label.setAlignment(Qt.AlignCenter)
        self.learn_label.setStyleSheet("font-size: 130px; color: #e94560; font-weight: bold;")
        
        self.btn_ok = QPushButton("OK")
        self.btn_ok.hide()
        self.btn_ok.clicked.connect(self.on_ok_clicked)
        
        self.btn_stop = QPushButton("Quit")
        self.btn_stop.clicked.connect(self.on_ok_clicked)
        
        layout.addWidget(self.result_output)
        layout.addWidget(self.learn_input)      # First
        layout.addWidget(self.char_display_box) # Second
        layout.addWidget(self.learn_label)
        layout.addWidget(self.btn_ok)
        layout.addWidget(self.btn_stop)
        page.setLayout(layout)
        self.pages.addWidget(page)

    def setup_practice_selection(self):
        """Page 3: Practice mode selection"""
        page = QWidget()
        layout = QVBoxLayout()
        btn_letters = QPushButton("Letter Practice")
        btn_words = QPushButton("Word Practice")
        btn_back = QPushButton("Back")
        btn_letters.clicked.connect(lambda: self.start_game("LETTERS"))
        btn_words.clicked.connect(lambda: self.start_game("WORDS"))
        btn_back.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        layout.addWidget(QLabel("PRACTICE MODE"))
        layout.addWidget(btn_letters)
        layout.addWidget(btn_words)
        layout.addWidget(btn_back)
        page.setLayout(layout)
        self.pages.addWidget(page)

    def setup_game_page(self):
        """Page 4: Game/practice mode"""
        page = QWidget()
        layout = QVBoxLayout()
        self.target_label = QLabel("")
        self.target_label.setAlignment(Qt.AlignCenter)
        self.target_label.setStyleSheet("font-size: 100px; color: #0fecb0; font-weight: bold;")
        self.input_field = QLineEdit()
        self.input_field.textChanged.connect(self.check_input)
        self.score_label = QLabel("Score: 0")
        btn_quit = QPushButton("Quit")
        btn_quit.clicked.connect(self.stop_game)
        layout.addWidget(self.target_label)
        layout.addWidget(self.input_field)
        layout.addWidget(self.score_label)
        layout.addWidget(btn_quit)
        page.setLayout(layout)
        self.pages.addWidget(page)

    def clear_input_field(self, field):
        """Clear input field without triggering text change signal"""
        field.blockSignals(True)
        field.clear()
        field.blockSignals(False)

    # ===== LEARNING MODE =====

    def start_learning(self):
        """Start learning mode"""
        self.logic.user_name = self.name_input.text().strip()
        if self.logic.user_name:
            self.logic.current_step_idx = 0
            self.logic.repetition_count = 0
            self.logic.in_random_phase = False
            self.logic.week_learning_phase_idx = 0
            if self.logic.has_current_week_learning_flow():
                self.logic.week_phase_start = time.time()
            self.result_output.hide()
            self.btn_ok.hide()
            self.btn_stop.show()
            self.learn_input.show()
            self.char_display_box.show()
            self.pages.setCurrentIndex(2)
            # Start random_timed timer BEFORE showing first target so the
            # first character gets a full time_per_char window from the start
            if self.logic.has_current_week_learning_flow() and self.logic.week_learning_phase_idx < len(self.logic.get_current_week_learning_flow()):
                phase = self.logic.get_current_week_learning_flow()[self.logic.week_learning_phase_idx]
                if phase.get("mode") == "random_timed":
                    time_per_char = phase.get("time_per_char", 1.5)
                    self.random_timed_timer.start(int(time_per_char * 1000))
            self.update_learning_target()

    def update_learning_target(self):
        """Update target for learning mode"""
        self.clear_input_field(self.learn_input)
        target = self.logic.generate_learning_target()
        
        if target is None:
            # Stop random_timed timer if active
            self.random_timed_timer.stop()
            self.logic.advance_week_learning_phase()
            if self.logic.should_end_week_learning():
                self.end_session()
                return
            # Check if next phase is random_timed
            if self.logic.has_current_week_learning_flow() and self.logic.week_learning_phase_idx < len(self.logic.get_current_week_learning_flow()):
                phase = self.logic.get_current_week_learning_flow()[self.logic.week_learning_phase_idx]
                if phase.get("mode") == "random_timed":
                    time_per_char = phase.get("time_per_char", 1.5)
                    self.random_timed_timer.start(int(time_per_char * 1000))
            self.update_learning_target()
            return
        
        self.learn_label.setText(target)
        self.char_display_box.setText(target) 
        if self.logic.speaker:
            announcement_text = self.logic.get_announcement_text(target)
            self.logic.speaker.output(announcement_text)
    
    def update_random_timed_target(self):
        """Update target in random_timed mode - called by timer"""
        self.clear_input_field(self.learn_input)
        
        # Use the backend method to get next char for random_timed
        target = self.logic.generate_random_timed_char()
        
        if target is None:
            # Phase ended, move to next
            self.random_timed_timer.stop()
            self.logic.advance_week_learning_phase()
            if self.logic.should_end_week_learning():
                self.end_session()
                return
            # Check if next phase is random_timed
            if self.logic.has_current_week_learning_flow() and self.logic.week_learning_phase_idx < len(self.logic.get_current_week_learning_flow()):
                phase = self.logic.get_current_week_learning_flow()[self.logic.week_learning_phase_idx]
                if phase.get("mode") == "random_timed":
                    time_per_char = phase.get("time_per_char", 1.5)
                    self.random_timed_timer.start(int(time_per_char * 1000))
                    self.update_random_timed_target()
                else:
                    self.update_learning_target()
            return
        
        self.learn_label.setText(target)
        self.char_display_box.setText(target)
        # Play sound for character change
        winsound.Beep(800, 50)
        if self.logic.speaker:
            announcement_text = self.logic.get_announcement_text(target)
            self.logic.speaker.output(announcement_text)

    def check_learn_input(self, text):
        """Validate learning input"""
        result = self.logic.check_learning_input(text, self.logic.target)
        if result is None:
            return
        
        # Check if we're in random_timed mode
        is_random_timed = False
        if self.logic.has_current_week_learning_flow() and self.logic.week_learning_phase_idx < len(self.logic.get_current_week_learning_flow()):
            phase = self.logic.get_current_week_learning_flow()[self.logic.week_learning_phase_idx]
            is_random_timed = phase.get("mode") == "random_timed"
        
        if result["correct"]:
            winsound.Beep(1500, 100)
            if result["should_log"]:
                self.logic.log_data(self.logic.target, "Correct")
            if is_random_timed:
                # Advance immediately on correct answer, and reset the timer so
                # the new character gets a fresh full time_per_char window.
                time_per_char = phase.get("time_per_char", 1.5)
                self.random_timed_timer.start(int(time_per_char * 1000))
                self.update_random_timed_target()
            else:
                self.logic.repetition_count += 1
                self.update_learning_target()
        elif result["should_clear"]:
            winsound.Beep(400, 200)
            if result["should_log"]:
                self.logic.log_data(self.logic.target, "Error")
            self.clear_input_field(self.learn_input)
            # Only update learning target if not in random_timed mode
            if not is_random_timed:
                # In non-random_timed mode, the error just clears the input
                # The user needs to try again for this character
                pass

    def end_session(self):
        """End learning session"""
        self.learn_input.hide()
        self.btn_stop.hide()
        self.random_timed_timer.stop()  # Stop random_timed timer if active
        self.char_display_box.hide()  # Hide the display box on end screen
        self.char_display_box.setText("END")
        self.learn_label.setText("END")
        self.result_output.setText("Session complete.")
        self.result_output.show()
        self.btn_ok.show()
        self.btn_ok.setFocus()
        
        if self.logic.current_week_idx == 2:
            if not self.player:
                self.player = QMediaPlayer()
                self.player.mediaStatusChanged.connect(self.on_media_status_changed)
            media_path = os.path.join(self.logic.base_dir, "halfway.mp3")
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(media_path)))
            self.player.setVolume(50)
            self.player.play()

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.player.play()

    def on_ok_clicked(self):
        if self.player and self.player.state() == QMediaPlayer.PlayingState:
            self.player.stop()
        self.random_timed_timer.stop()  # Stop random_timed timer if active
        self.pages.setCurrentIndex(1)
        if self.logic.mode != "LETTERS":
            return
        if not self.logic.practice_letter_weights:
            self.logic.initialize_practice_weights()
            return
        self.logic.update_practice_weights()

    # ===== PRACTICE MODE =====

    def start_practice(self):
        self.logic.user_name = self.name_input.text().strip()
        if self.logic.user_name:
            self.pages.setCurrentIndex(3)

    def start_game(self, mode):
        self.logic.mode = mode
        self.logic.score = 0
        self.logic.practice_round_counter = 0
        self.pages.setCurrentIndex(4)
        if mode == "LETTERS":
            self.logic.initialize_practice_weights()
            self.practice_minute_timer.start(60000)
        self.next_round()

    def next_round(self):
        self.timer.stop()
        self.clear_input_field(self.input_field)
        
        if self.logic.mode == "LETTERS":
            self.logic.generate_game_target()
            self.target_label.setText(self.logic.target)
            if self.logic.speaker:
                announcement_text = self.logic.get_announcement_text(self.logic.target)
                self.logic.speaker.output(announcement_text)
            self.input_field.setEnabled(True)
            self.input_field.setFocus()
            self.timer.start(5000)
            self.logic.practice_round_counter += 1
        else:
            self.logic.generate_game_target()
            self.target_label.setText(self.logic.target)
            
            if self.logic.speaker:
                self.input_field.setEnabled(False)
                pronun = self.logic.get_word_pronunciation()
                self.logic.speaker.output(pronun["spelling"])
                QTimer.singleShot(pronun["spelling_delay"], 
                                lambda: self.logic.speaker.output(self.logic.target))
                QTimer.singleShot(pronun["total_delay"], 
                                lambda: self.start_counting(pronun["wait_time"]))
            else:
                wait_time = self.logic.get_word_pronunciation()["wait_time"]
                self.start_counting(wait_time)

    def start_counting(self, wait_time):
        self.input_field.setEnabled(True)
        self.input_field.setFocus()
        winsound.Beep(1000, 150)
        self.timer.start(wait_time)

    def check_input(self, text):
        result = self.logic.check_game_input(text, self.logic.target)
        if result is None:
            return
        
        if result["correct"]:
            self.timer.stop()
            winsound.Beep(1500, 100)
            self.logic.log_data(self.logic.target, "Correct")
            self.logic.score += 1
            self.score_label.setText(f"Score: {self.logic.score}")
            self.next_round()
        elif result["should_clear"]:
            winsound.Beep(400, 200)
            self.logic.log_data(self.logic.target, "Error")
            self.clear_input_field(self.input_field)
            self.next_round()

    def time_out(self):
        winsound.Beep(600, 800)
        self.logic.log_data(self.logic.target, "Error")
        self.next_round()

    def stop_game(self):
        self.timer.stop()
        self.practice_minute_timer.stop()
        self.random_timed_timer.stop()  # Stop random_timed timer if active
        self.pages.setCurrentIndex(3)

    def evaluate_practice_adaptivity(self):
        pass

    # ===== WEEK 4: MASTERY MODE =====

    def setup_week4_entry_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        self.w4_name_input = QLineEdit()
        self.w4_name_input.setPlaceholderText("Enter your name...")
        self.w4_instructions = QLineEdit()
        self.w4_instructions.setReadOnly(True)
        instructions_text = (
            "In this section, you will master the letters you have learned so far.\n"
            "You will not learn anything new, but will focus on the previous three weeks.\n"
            "Congratulations on making it this far.\n"
            "Time is important and adaptive.\n"
            "When a letter reaches good accuracy and stable speed, it will be marked as mastered and disappear.\n"
            "Continue until all letters are mastered to become an AZERTY keyboard expert."
        )
        self.w4_instructions.setText(instructions_text)
        self.w4_instructions.setMinimumHeight(150)
        btn_start = QPushButton("Start Mastery Session")
        btn_start.clicked.connect(self.start_week4_session)
        btn_back = QPushButton("Back")
        btn_back.clicked.connect(self.go_back_to_week_selection)
        layout.addWidget(QLabel("WEEK 4: MASTERY"))
        layout.addWidget(self.w4_name_input)
        layout.addWidget(self.w4_instructions)
        layout.addWidget(btn_start)
        layout.addWidget(btn_back)
        page.setLayout(layout)
        self.pages.addWidget(page)

    def start_week4_session(self):
        username = self.w4_name_input.text().strip()
        if not username:
            if self.logic.speaker:
                self.logic.speaker.output("Please enter your name")
            return
        self.logic = Week4Logic(self._base_logic)
        self.logic.user_name = username
        self.logic.mode_start_time = time.time()
        self.w4_round_start_time = None
        self.w4_current_attempt = None
        self.pages.setCurrentIndex(6)
        self.week4_next_round()

    def setup_week4_game_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        self.w4_target_label = QLabel("")
        self.w4_target_label.setAlignment(Qt.AlignCenter)
        self.w4_target_label.setStyleSheet("font-size: 100px; color: #0fecb0; font-weight: bold;")
        self.w4_input_field = QLineEdit()
        self.w4_input_field.textChanged.connect(self.check_week4_input)
        self.w4_phase_label = QLabel("")
        self.w4_phase_label.setStyleSheet("font-size: 14px; color: #f9d342;")
        btn_quit = QPushButton("Quit")
        btn_quit.clicked.connect(self.stop_week4_game)
        self.w4_timer = QTimer()
        self.w4_timer.timeout.connect(self.week4_time_out)
        layout.addWidget(self.w4_phase_label)
        layout.addWidget(self.w4_target_label)
        layout.addWidget(self.w4_input_field)
        layout.addWidget(btn_quit)
        page.setLayout(layout)
        self.pages.addWidget(page)

    def week4_next_round(self):
        self.w4_timer.stop()
        self.clear_input_field(self.w4_input_field)
        if self.logic.is_session_complete():
            self.pages.setCurrentIndex(7)
            return
            
        if self.logic.should_advance_phase():
            self.logic.advance_phase()
            new_phase = self.logic.get_current_phase()
            if new_phase:
                # Announce mode switch and disable input
                self.w4_input_field.setEnabled(False)
                mode_announcement = f"{new_phase['name']}"
                if self.logic.speaker:
                    self.logic.speaker.output(mode_announcement)
                # Wait for announcement, then continue
                announcement_duration = len(mode_announcement) * 100 + 500
                QTimer.singleShot(announcement_duration, lambda: self.week4_continue_round_after_phase_switch())
                return
        
        # Get current phase
        phase = self.logic.get_current_phase()
        
        # Handle PAUSE mode
        if phase and phase["mode"] == "PAUSE":
            self.w4_input_field.setEnabled(False)
            self.w4_target_label.setText(f"PAUSE\n{phase['duration']} seconds")
            self.w4_phase_label.setText("Rest...")
            if self.logic.speaker:
                self.logic.speaker.output(f"PAUSE for {phase['duration']} seconds. Rest.")
            # Wait for pause duration then advance
            pause_duration = int(phase['duration'] * 1000)
            QTimer.singleShot(pause_duration, lambda: self.week4_advance_past_pause())
            return
        
        # Generate next target
        target = self.logic.generate_target()
        if target is None:
            self.pages.setCurrentIndex(7)
            return
        
        self.w4_phase_label.setText(phase["name"] if phase else "")
        display_time = self.logic.get_target_display_time()
        self.w4_target_label.setText(target)
        if phase and phase["mode"] in ["WORDS", "COUPLE"]:
            if self.logic.speaker:
                self.w4_input_field.setEnabled(False)
                pronun = self.logic.get_word_pronunciation()
                self.logic.speaker.output(pronun["spelling"])
                QTimer.singleShot(pronun["spelling_delay"], 
                                lambda: self.logic.speaker.output(self.logic.target))
                QTimer.singleShot(pronun["total_delay"], 
                                lambda: self.w4_start_input())
            else:
                wait_time = len(self.logic.target) * 2000
                self.w4_start_input_with_delay(wait_time)
        else:
            if self.logic.speaker:
                self.logic.speaker.output(target)
            self.w4_input_field.setEnabled(True)
            self.w4_input_field.setFocus()
            self.w4_round_start_time = time.time()
            self.w4_timer.start(int(display_time * 1000))

    def w4_start_input(self):
        self.w4_input_field.setEnabled(True)
        self.w4_input_field.setFocus()
        self.w4_round_start_time = time.time()
        display_time = self.logic.get_target_display_time()
        winsound.Beep(1000, 150)
        self.w4_timer.start(int(display_time * 1000))

    def w4_start_input_with_delay(self, wait_time):
        self.w4_input_field.setEnabled(True)
        self.w4_input_field.setFocus()
        self.w4_round_start_time = time.time()
        winsound.Beep(1000, 150)
        self.w4_timer.start(wait_time)

    def week4_continue_round_after_phase_switch(self):
        """Continue round after phase switch announcement"""
        # Get current phase first to check for PAUSE mode
        phase = self.logic.get_current_phase()
        
        # Handle PAUSE mode (if phase switch led into a PAUSE)
        if phase and phase["mode"] == "PAUSE":
            self.w4_input_field.setEnabled(False)
            self.w4_target_label.setText(f"PAUSE\n{phase['duration']} seconds")
            self.w4_phase_label.setText("Rest...")
            if self.logic.speaker:
                self.logic.speaker.output(f"PAUSE for {phase['duration']} seconds. Rest.")
            # Wait for pause duration then advance
            pause_duration = int(phase['duration'] * 1000)
            QTimer.singleShot(pause_duration, lambda: self.week4_advance_past_pause())
            return
        
        # Generate next target
        target = self.logic.generate_target()
        if target is None:
            self.pages.setCurrentIndex(7)  # End page
            return
        
        self.w4_phase_label.setText(phase["name"] if phase else "")
        
        display_time = self.logic.get_target_display_time()
        self.w4_target_label.setText(target)
        
        # Handle WORDS and COUPLE modes
        if phase and phase["mode"] in ["WORDS", "COUPLE"]:
            if self.logic.speaker:
                self.w4_input_field.setEnabled(False)
                pronun = self.logic.get_word_pronunciation()
                self.logic.speaker.output(pronun["spelling"])
                QTimer.singleShot(pronun["spelling_delay"], 
                                lambda: self.logic.speaker.output(self.logic.target))
                QTimer.singleShot(pronun["total_delay"], 
                                lambda: self.w4_start_input())
            else:
                wait_time = len(self.logic.target) * 2000
                self.w4_start_input_with_delay(wait_time)
        else:
            if self.logic.speaker:
                self.logic.speaker.output(target)
            self.w4_input_field.setEnabled(True)
            self.w4_input_field.setFocus()
            self.w4_round_start_time = time.time()
            self.w4_timer.start(int(display_time * 1000))

    def week4_advance_past_pause(self):
        """Advance past pause and continue with next phase"""
        self.logic.advance_phase()
        self.week4_next_round()

    def show_week4_mastery_notification(self, newly_mastered_letters):
        mastery_messages = [f"{letter} is mastered" for letter in newly_mastered_letters]
        full_message = " ".join(mastery_messages)
        self.w4_input_field.setEnabled(False)
        self.w4_target_label.setText(full_message)
        if self.logic.speaker:
            self.logic.speaker.output(full_message)
            speak_duration = len(full_message) * 100 + 500
            QTimer.singleShot(speak_duration, lambda: self.week4_next_round())
        else:
            QTimer.singleShot(1500, lambda: self.week4_next_round())

    def check_week4_input(self, text):
        if not text: return
        is_correct = self.logic.check_input(text, self.logic.target)
        if is_correct:
            self.w4_timer.stop()
            winsound.Beep(1500, 100)
            
            # Record correct attempt
            offered_time = self.logic.get_target_display_time()
            newly_mastered = self.logic.record_attempt(self.logic.target, "correct", offered_time)
            
            self.logic.score += 1
            if newly_mastered: self.show_week4_mastery_notification(newly_mastered)
            else: self.week4_next_round()
        elif len(text) >= len(self.logic.target):
            winsound.Beep(400, 200)
            
            # Record error
            offered_time = self.logic.get_target_display_time()
            newly_mastered = self.logic.record_attempt(self.logic.target, "error", offered_time)
            
            self.clear_input_field(self.w4_input_field)
            if newly_mastered: self.show_week4_mastery_notification(newly_mastered)
            else: self.week4_next_round()

    def week4_time_out(self):
        winsound.Beep(600, 800)
        
        # Record timeout
        offered_time = self.logic.get_target_display_time()
        newly_mastered = self.logic.record_attempt(self.logic.target, "timeout", offered_time)
        
        if newly_mastered:
            self.show_week4_mastery_notification(newly_mastered)
        else:
            self.week4_next_round()

    def stop_week4_game(self):
        self.w4_timer.stop()
        self.logic = self._base_logic
        self.logic.reset()
        self.pages.setCurrentIndex(0)

    def setup_week4_end_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        self.w4_end_message = QLineEdit()
        self.w4_end_message.setReadOnly(True)
        end_text = "Congratulations!\nYou have completed the adventure.\nPress OK."
        self.w4_end_message.setText(end_text)
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.week4_end_ok)
        layout.addWidget(self.w4_end_message)
        layout.addWidget(btn_ok)
        page.setLayout(layout)
        self.pages.addWidget(page)

    def week4_end_ok(self):
        self.logic = self._base_logic
        self.logic.reset()
        self.pages.setCurrentIndex(0)

    # ===== WEEK 6: ULTIMATE CHALLENGE =====

    def setup_week6_identification_page(self):
        """Page 8: Week 6 instructions page (username from page 1)"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("WEEK 6: ULTIMATE CHALLENGE")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #e94560;")
        layout.addWidget(title)
        
        # Instructions readonly field
        self.w6_instructions = QLineEdit()
        self.w6_instructions.setReadOnly(True)
        self.w6_instructions.setText(
            "WEEK 6 — THE ULTIMATE CHALLENGE! "
            "This is it. Six legendary modes stand between you and total keyboard mastery. "
            "Conquer the Warmup Gate, blaze through Combo Rush, sharpen your aim in Precision Arena, "
            "power through Sentence Mode, survive the Survival Gate, "
            "and unleash chaos in the Crazy Keyboard Party! "
            "Every mode you defeat drains the Boss health and earns you XP. "
            "Climb the ranks from Beginner all the way to Master. "
            "Reach 1500 XP and the Boss falls — VICTORY is yours. "
            "Enter your name below and let the battle begin!"
        )
        self.w6_instructions.setMinimumHeight(150)
        layout.addWidget(self.w6_instructions)

        self.w6_name_input = QLineEdit()
        self.w6_name_input.setPlaceholderText("Enter your name...")
        layout.addWidget(self.w6_name_input)

        # Buttons
        btn_row = QHBoxLayout()

        btn_start = QPushButton("Let's Start!")
        btn_start.clicked.connect(self.start_week6_challenge)
        btn_row.addWidget(btn_start)
        
        btn_back = QPushButton("Back")
        btn_back.clicked.connect(self.go_back_to_week_selection)
        btn_row.addWidget(btn_back)
        
        layout.addLayout(btn_row)
        layout.addStretch()
        
        page.setLayout(layout)
        self.pages.addWidget(page)

    def start_week6_challenge(self):
        """Start Week 6 challenge with username from identification page"""
        username = self.w6_name_input.text().strip()
        if not username:
            if self.logic.speaker:
                self.logic.speaker.output("Please enter your name")
            return
        
        # Import and launch Week 6 challenge with username.
        # Call start_challenge() immediately so Week6UI jumps straight to the
        # battle page — Page 8 of the main app already served as the intro.
        from w6challenge import Week6UI
        self.w6_ui = Week6UI(self.logic, user_name=username, is_english=True)
        self.w6_ui.show()
        self.w6_ui.start_challenge()
