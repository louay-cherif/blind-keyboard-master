# the imports
import winsound
import time
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLineEdit, 
                             QLabel, QStackedWidget)
from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent


class AppFrontend(QWidget):
    """GUI layer for the application. Handles all user interface elements."""
    
    def __init__(self, logic):
        super().__init__()
        self.logic = logic  # Reference to AppBackend instance
        
        self.setWindowTitle("Adapted Informatics Initiative Official Keyboard typing app for visually impaired people")
        self.resize(800, 600)
        
        # Timer for game mode
        self.timer = QTimer()
        self.timer.timeout.connect(self.time_out)
        
        # Timer for practice adaptivity (every minute)
        self.practice_minute_timer = QTimer()
        self.practice_minute_timer.timeout.connect(self.evaluate_practice_adaptivity)
        
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
        
        layout = QVBoxLayout()
        layout.addWidget(self.pages)
        self.setLayout(layout)

    def setup_week_selection(self):
        """Page 0: Week selection"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Choisissez votre semaine :"))
        for i, week in enumerate(self.logic.weeks):
            btn = QPushButton(week["name"])
            btn.clicked.connect(lambda checked, idx=i: self.select_week(idx))
            layout.addWidget(btn)
        page.setLayout(layout)
        self.pages.addWidget(page)

    def select_week(self, idx):
        """Select a week and move to identification page"""
        self.logic.current_week_idx = idx
        self.pages.setCurrentIndex(1)

    def setup_identification_page(self):
        """Page 1: User identification and mode selection"""
        page = QWidget()
        layout = QVBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Entrez votre nom...")
        btn_learn = QPushButton("Apprendre")
        btn_practice = QPushButton("Pratique")
        btn_learn.clicked.connect(self.start_learning)
        btn_practice.clicked.connect(self.start_practice)
        layout.addWidget(QLabel("IDENTIFICATION"))
        layout.addWidget(self.name_input)
        layout.addWidget(btn_learn)
        layout.addWidget(btn_practice)
        page.setLayout(layout)
        self.pages.addWidget(page)

    def setup_learning_page(self):
        """Page 2: Learning mode"""
        page = QWidget()
        layout = QVBoxLayout()
        self.result_output = QLineEdit()
        self.result_output.setReadOnly(True)
        self.result_output.hide()
        self.learn_label = QLabel("")
        self.learn_label.setAlignment(Qt.AlignCenter)
        self.learn_label.setStyleSheet("font-size: 130px; color: #e94560; font-weight: bold;")
        self.learn_input = QLineEdit()
        self.learn_input.textChanged.connect(self.check_learn_input)
        self.btn_ok = QPushButton("OK")
        self.btn_ok.hide()
        self.btn_ok.clicked.connect(self.on_ok_clicked)
        self.btn_stop = QPushButton("Quitter")
        self.btn_stop.clicked.connect(self.on_ok_clicked)
        layout.addWidget(self.result_output)
        layout.addWidget(self.learn_label)
        layout.addWidget(self.learn_input)
        layout.addWidget(self.btn_ok)
        layout.addWidget(self.btn_stop)
        page.setLayout(layout)
        self.pages.addWidget(page)

    def setup_practice_selection(self):
        """Page 3: Practice mode selection"""
        page = QWidget()
        layout = QVBoxLayout()
        btn_letters = QPushButton("Pratique des Lettres")
        btn_words = QPushButton("Pratique des Mots")
        btn_back = QPushButton("Retour")
        btn_letters.clicked.connect(lambda: self.start_game("LETTERS"))
        btn_words.clicked.connect(lambda: self.start_game("WORDS"))
        btn_back.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        layout.addWidget(QLabel("MODE PRATIQUE"))
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
        btn_quit = QPushButton("Quitter")
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
            self.pages.setCurrentIndex(2)
            self.update_learning_target()

    def update_learning_target(self):
        """Update target for learning mode"""
        self.clear_input_field(self.learn_input)
        target = self.logic.generate_learning_target()
        
        if target is None:  # Signal to advance phase
            self.logic.advance_week_learning_phase()
            if self.logic.should_end_week_learning():
                self.end_session()
                return
            self.update_learning_target()
            return
        
        self.learn_label.setText(target)
        if self.logic.speaker:
            self.logic.speaker.output(target)

    def check_learn_input(self, text):
        """Validate learning input"""
        result = self.logic.check_learning_input(text, self.logic.target)
        if result is None:
            return
        
        if result["correct"]:
            winsound.Beep(1500, 100)
            if result["should_log"]:
                self.logic.log_data(self.logic.target, "Correct")
            self.logic.repetition_count += 1
            self.update_learning_target()
        elif result["should_clear"]:
            winsound.Beep(400, 200)
            if result["should_log"]:
                self.logic.log_data(self.logic.target, "Error")
            self.clear_input_field(self.learn_input)

    def end_session(self):
        """End learning session"""
        self.learn_input.hide()
        self.btn_stop.hide()
        self.learn_label.setText("FIN")
        self.result_output.setText("Session terminee.")
        self.result_output.show()
        self.btn_ok.show()
        self.btn_ok.setFocus()
        
        # Play end-of-week audio for week 3
        if self.logic.current_week_idx == 2:
            if not self.player:
                self.player = QMediaPlayer()
                self.player.mediaStatusChanged.connect(self.on_media_status_changed)
            media_path = os.path.join(self.logic.base_dir, "halfway.mp3")
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(media_path)))
            self.player.setVolume(50)
            self.player.play()

    def on_media_status_changed(self, status):
        """Handle media player status changes"""
        if status == QMediaPlayer.EndOfMedia:
            self.player.play()

    def on_ok_clicked(self):
        """OK button clicked after learning session"""
        if self.player and self.player.state() == QMediaPlayer.PlayingState:
            self.player.stop()
        self.pages.setCurrentIndex(1)
        if self.logic.mode != "LETTERS":
            return
        if not self.logic.practice_letter_weights:
            self.logic.initialize_practice_weights()
            return
        self.logic.update_practice_weights()

    # ===== PRACTICE MODE =====

    def start_practice(self):
        """Start practice mode"""
        self.logic.user_name = self.name_input.text().strip()
        if self.logic.user_name:
            self.pages.setCurrentIndex(3)

    def start_game(self, mode):
        """Start game with specified mode (LETTERS or WORDS)"""
        self.logic.mode = mode
        self.logic.score = 0
        self.logic.practice_round_counter = 0
        self.pages.setCurrentIndex(4)
        if mode == "LETTERS":
            self.logic.initialize_practice_weights()
            self.practice_minute_timer.start(60000)
        self.next_round()

    def next_round(self):
        """Setup next round of practice"""
        self.timer.stop()
        self.clear_input_field(self.input_field)
        
        if self.logic.mode == "LETTERS":
            self.logic.generate_game_target()
            self.target_label.setText(self.logic.target)
            if self.logic.speaker:
                self.logic.speaker.output(self.logic.target)
            self.input_field.setEnabled(True)
            self.input_field.setFocus()
            self.timer.start(5000)
            self.logic.practice_round_counter += 1
        else:  # WORDS mode
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
                wait_time = len(self.logic.target) * 2000
                self.start_counting(wait_time)

    def start_counting(self, wait_time):
        """Start timer for user input"""
        self.input_field.setEnabled(True)
        self.input_field.setFocus()
        winsound.Beep(1000, 150)
        self.timer.start(wait_time)

    def check_input(self, text):
        """Validate game input"""
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
        """Handle timeout during input"""
        winsound.Beep(600, 800)
        self.logic.log_data(self.logic.target, "Error")
        self.next_round()

    def stop_game(self):
        """Stop game and return to menu"""
        self.timer.stop()
        self.practice_minute_timer.stop()
        self.pages.setCurrentIndex(3)

    def evaluate_practice_adaptivity(self):
        """Evaluate practice adaptivity (called every minute)"""
        # This can be expanded to analyze performance and adjust difficulty
        pass
