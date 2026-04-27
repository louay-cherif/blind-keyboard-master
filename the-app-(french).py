import sys
import random
import winsound
import csv
import os
import time
import w2words
import w3words

try:
    from accessible_output2.outputs import auto
    HAS_ACCESSIBLE = True
except ImportError:
    HAS_ACCESSIBLE = False

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QLineEdit, QLabel, QStackedWidget)
from PyQt5.QtCore import Qt, QTimer

class TypingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Adapted Informatics Initiative Official Keyboard typing app for visually impaired people")
        self.resize(800, 600)
        
        self.speaker = auto.Auto() if HAS_ACCESSIBLE else None
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.weeks = [
            {
                "name": "Semaine 1: Ligne de Base",
                "steps": ["QSDF", "GHJ", "KLM", "QSDFGHJKLM"],
                "practice_letters": ["QSDFGHJKLM"],
                "words": [],
            },
            {
                "name": "Semaine 2: Ligne Supérieure",
                "steps": ["AZER", "TYU", "IOP", "AZERTYUIOP"],
                "letters": "AZERTYUIOP",
                "practice_letters": ["AZERTYUIOP", "AZERTYUIOPQSDFGHJKLM"],
                "words": getattr(w2words, "words", []),
                "learning_flow": [
                    {"mode": "random", "chars": "QSDFGHJKLM", "duration": 300},
                    {"mode": "learn", "chars": "AZER"},
                    {"mode": "random", "chars": "AZER", "count": 20},
                    {"mode": "learn", "chars": "TYU"},
                    {"mode": "random", "chars": "TYU", "count": 20},
                    {"mode": "learn", "chars": "IOP"},
                    {"mode": "random", "chars": "IOP", "count": 20},
                    {"mode": "random", "chars": "AZERTYUIOP", "count": 40},
                    {"mode": "random", "chars": "AZERTYUIOPQSDFGHJKLM", "count": 60},
                ],
            },
            {
                "name": "Semaine 3: Ligne Inférieure",
                "steps": ["WXC", "VBN", "WXCVBN"],
                "letters": "WXCVBN",
                "practice_letters": ["WXCVBN", "AZERTYUIOPQSDFGHJKLMWXCVBN"],
                "words": getattr(w3words, "words", []),
                "learning_flow": [
                    {"mode": "random", "chars": "QSDFGHJKLM", "duration": 300},
                    {"mode": "random", "chars": "AZERTYUIOP", "duration": 300},
                    {"mode": "random", "chars": "AZERTYUIOPQSDFGHJKLM", "count": 100},
                    {"mode": "learn", "chars": "WXC"},
                    {"mode": "random", "chars": "WXC", "count": 20},
                    {"mode": "random", "chars": "AZERTYUIOPWXC", "duration": 180},
                    {"mode": "learn", "chars": "VBN"},
                    {"mode": "random", "chars": "VBN", "duration": 120},
                    {"mode": "random", "chars": "WXCVBN", "duration": 180},
                    {"mode": "random", "chars": "AZERTYUIOPQSDFGHJKLMWXCVBN", "duration": 600},
                ],
            },
            {
                "name": "Semaine 4: Mixage des Lignes",
                "steps": ["QSDFGHJKLM", "AZERTYUIOP", "WXCVBN", "AZERTYUIOPQSDFGHJKLMWXCVBN"],
            },
            {
                "name": "Semaine 5: Majuscules et Symboles",
                "steps": ["ABCDEFGHIJKLMNOPQRSTUVWXYZ", ",;:!?", "./§", "ALL_COMBINED"],
            },
        ]
        
        self.current_week_idx = 0
        self.current_step_idx = 0
        self.repetition_count = 0
        self.in_random_phase = False
        
        self.week_learning_phase_idx = 0
        self.week_phase_start = None
        
        self.mode = ""
        self.target = ""
        self.score = 0
        self.user_name = ""
        
        self.practice_round_counter = 0
        
        self.practice_minute_timer = QTimer()
        self.practice_minute_timer.timeout.connect(self.evaluate_practice_adaptivity)
        self.practice_letter_weights = {}
        self.last_letter_accuracy = {}
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.time_out)

        self.setStyleSheet("""
            QWidget { background-color: #0a0a12; color: #ffffff; font-family: Arial; font-size: 24px; }
            QPushButton { background-color: #16213e; border-radius: 12px; padding: 15px; color: white; border: 2px solid #e94560; margin: 5px; }
            QPushButton:hover { background-color: #e94560; }
            QLineEdit { padding: 18px; background-color: #1a1a2e; color: #0fecb0; border: 2px solid #0fecb0; border-radius: 10px; text-align: center; }
            QLineEdit[readOnly="true"] { color: #f9d342; border-color: #f9d342; }
        """)

        self.pages = QStackedWidget()
        self.setup_week_selection()
        self.setup_identification_page()
        self.setup_learning_page()
        self.setup_practice_selection()
        self.setup_game_page()
        
        layout = QVBoxLayout()
        layout.addWidget(self.pages)
        self.setLayout(layout)

    def get_clean_username(self):
        return "".join(c for c in self.user_name if c.isalnum() or c in (' ', '_')).rstrip()

    def get_user_csv_path(self):
        clean_name = self.get_clean_username()
        return os.path.join(self.base_dir, f"{clean_name}_Week_{self.current_week_idx + 1}.csv")

    def clear_input_field(self, field):
        field.blockSignals(True)
        field.clear()
        field.blockSignals(False)

    def current_week(self):
        return self.weeks[self.current_week_idx]

    def get_current_week_steps(self):
        return self.current_week().get("steps", [])

    def get_current_week_letters(self):
        letters = self.current_week().get("letters")
        if letters:
            return letters
        steps = self.get_current_week_steps()
        letters = set()
        for step in steps:
            for char in step:
                if char.isalpha():
                    letters.add(char.upper())
        return ''.join(sorted(letters))

    def get_current_week_words(self):
        return self.current_week().get("words", [])

    def get_current_week_practice_letters(self):
        practice_letters = self.current_week().get("practice_letters", [])
        if not practice_letters:
            return self.get_current_week_letters()
        idx = min(len(practice_letters) - 1, self.practice_round_counter // 100)
        return practice_letters[idx]

    def get_current_week_letter_stats(self):
        letters = self.get_current_week_letters()
        stats = {letter: {"correct": 0, "total": 0} for letter in letters}
        file_path = self.get_user_csv_path()
        if not os.path.isfile(file_path):
            return {letter: None for letter in letters}

        try:
            with open(file_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    char = row.get("Character", "").upper()
                    if char in stats:
                        stats[char]["total"] += 1
                        if row.get("Status") == "Correct":
                            stats[char]["correct"] += 1
        except:
            return {letter: None for letter in letters}

        accuracy = {}
        for letter, data in stats.items():
            if data["total"] == 0:
                accuracy[letter] = None
            else:
                accuracy[letter] = data["correct"] / data["total"]
        return accuracy

    def compute_practice_weight(self, accuracy, previous_accuracy=None):
        if accuracy is None:
            base = 10
        elif accuracy < 0.8:
            base = 8
        elif accuracy < 0.9:
            base = 4
        else:
            base = 1

        if previous_accuracy is not None and accuracy is not None:
            if accuracy > previous_accuracy:
                base = max(1, base - 1)
            elif accuracy <= previous_accuracy:
                base = base + 2

        return min(max(base, 1), 20)

    def initialize_practice_weights(self):
        accuracies = self.get_current_week_letter_stats()
        self.practice_letter_weights = {}
        for letter, accuracy in accuracies.items():
            self.practice_letter_weights[letter] = self.compute_practice_weight(accuracy)
        self.last_letter_accuracy = accuracies

    def update_practice_weights(self):
        accuracies = self.get_current_week_letter_stats()
        for letter, accuracy in accuracies.items():
            previous = self.last_letter_accuracy.get(letter)
            self.practice_letter_weights[letter] = self.compute_practice_weight(accuracy, previous)
        self.last_letter_accuracy = accuracies

    def has_current_week_learning_flow(self):
        return bool(self.current_week().get("learning_flow"))

    def get_current_week_learning_flow(self):
        return self.current_week().get("learning_flow", [])

    def log_data(self, char, status):
        if not self.user_name: return
        file_path = self.get_user_csv_path()
        file_exists = os.path.isfile(file_path)
        try:
            with open(file_path, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["Character", "Status"])
                writer.writerow([char, status])
        except: pass

    def setup_week_selection(self):
        page = QWidget(); layout = QVBoxLayout()
        layout.addWidget(QLabel("Choisissez votre semaine :"))
        for i, week in enumerate(self.weeks):
            btn = QPushButton(week["name"])
            btn.clicked.connect(lambda checked, idx=i: self.select_week(idx))
            layout.addWidget(btn)
        page.setLayout(layout); self.pages.addWidget(page)

    def select_week(self, idx):
        self.current_week_idx = idx
        self.pages.setCurrentIndex(1)

    def setup_identification_page(self):
        page = QWidget(); layout = QVBoxLayout()
        self.name_input = QLineEdit(); self.name_input.setPlaceholderText("Entrez votre nom...")
        btn_learn = QPushButton("Apprendre"); btn_practice = QPushButton("Pratique")
        btn_learn.clicked.connect(self.start_learning)
        btn_practice.clicked.connect(self.start_practice)
        layout.addWidget(QLabel("IDENTIFICATION")); layout.addWidget(self.name_input)
        layout.addWidget(btn_learn); layout.addWidget(btn_practice)
        page.setLayout(layout); self.pages.addWidget(page)

    def setup_learning_page(self):
        page = QWidget(); layout = QVBoxLayout()
        self.result_output = QLineEdit(); self.result_output.setReadOnly(True); self.result_output.hide()
        self.learn_label = QLabel(""); self.learn_label.setAlignment(Qt.AlignCenter)
        self.learn_label.setStyleSheet("font-size: 130px; color: #e94560; font-weight: bold;")
        self.learn_input = QLineEdit(); self.learn_input.textChanged.connect(self.check_learn_input)
        self.btn_ok = QPushButton("OK"); self.btn_ok.hide()
        self.btn_ok.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        self.btn_stop = QPushButton("Quitter"); self.btn_stop.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        layout.addWidget(self.result_output); layout.addWidget(self.learn_label)
        layout.addWidget(self.learn_input); layout.addWidget(self.btn_ok); layout.addWidget(self.btn_stop)
        page.setLayout(layout); self.pages.addWidget(page)

    def setup_practice_selection(self):
        page = QWidget(); layout = QVBoxLayout()
        btn_letters = QPushButton("Pratique des Lettres"); btn_words = QPushButton("Pratique des Mots"); btn_back = QPushButton("Retour")
        btn_letters.clicked.connect(lambda: self.start_game("LETTERS")); btn_words.clicked.connect(lambda: self.start_game("WORDS"))
        btn_back.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        layout.addWidget(QLabel("MODE PRATIQUE")); layout.addWidget(btn_letters); layout.addWidget(btn_words); layout.addWidget(btn_back)
        page.setLayout(layout); self.pages.addWidget(page)

    def setup_game_page(self):
        page = QWidget(); layout = QVBoxLayout()
        self.target_label = QLabel(""); self.target_label.setAlignment(Qt.AlignCenter)
        self.target_label.setStyleSheet("font-size: 100px; color: #0fecb0; font-weight: bold;")
        self.input_field = QLineEdit(); self.input_field.textChanged.connect(self.check_input)
        self.score_label = QLabel("Score: 0")
        btn_quit = QPushButton("Quitter"); btn_quit.clicked.connect(self.stop_game)
        layout.addWidget(self.target_label); layout.addWidget(self.input_field); layout.addWidget(self.score_label); layout.addWidget(btn_quit)
        page.setLayout(layout); self.pages.addWidget(page)

    def start_learning(self):
        self.user_name = self.name_input.text().strip()
        if self.user_name:
            self.current_step_idx = 0; self.repetition_count = 0; self.in_random_phase = False; self.week_learning_phase_idx = 0
            if self.has_current_week_learning_flow():
                self.week_phase_start = time.time()
            self.result_output.hide(); self.btn_ok.hide(); self.btn_stop.show(); self.learn_input.show()
            self.pages.setCurrentIndex(2); self.update_learning_target()

    def start_practice(self):
        self.user_name = self.name_input.text().strip()
        if self.user_name: self.pages.setCurrentIndex(3)

    def update_learning_target(self):
        self.clear_input_field(self.learn_input)
        if self.has_current_week_learning_flow() and self.week_learning_phase_idx < len(self.get_current_week_learning_flow()):
            self.update_learning_target_flow()
            return
        steps = self.get_current_week_steps()
        current_chars = steps[self.current_step_idx]
        if not self.in_random_phase:
            char_idx = self.repetition_count // 10
            if char_idx < len(current_chars): self.target = current_chars[char_idx]
            else:
                self.in_random_phase = True; self.update_learning_target()
                return
        else:
            self.target = random.choice(current_chars)
        self.learn_label.setText(self.target)
        if self.speaker: self.speaker.output(self.target)

    def update_learning_target_flow(self):
        phase = self.get_current_week_learning_flow()[self.week_learning_phase_idx]
        mode = phase.get("mode"); chars = phase.get("chars", "")
        if mode == "random":
            if phase.get("duration"):
                elapsed = time.time() - self.week_phase_start
                if elapsed >= phase["duration"]:
                    self.advance_week_learning_phase()
                    return
            self.target = random.choice(chars)
        elif mode == "learn":
            char_idx = self.repetition_count // 10
            if char_idx < len(chars):
                self.target = chars[char_idx]
            else:
                self.advance_week_learning_phase()
                return
        self.learn_label.setText(self.target)
        if self.speaker:
            self.speaker.output(self.target)

    def advance_week_learning_phase(self):
        self.week_learning_phase_idx += 1; self.repetition_count = 0
        self.week_phase_start = time.time()
        if self.week_learning_phase_idx >= len(self.get_current_week_learning_flow()):
            self.end_session()
            return
        self.update_learning_target_flow()

    def check_learn_input(self, text):
        if not text: return
        is_correct = (text[-1].upper() == self.target.upper()) if self.current_week_idx < 4 else (text == self.target)
        if is_correct:
            winsound.Beep(1500, 100); self.log_data(self.target, "Correct")
            self.update_learning_target()
        elif len(text) >= len(self.target):
            winsound.Beep(400, 200); self.log_data(self.target, "Error"); self.clear_input_field(self.learn_input)

    def end_session(self):
        self.learn_input.hide(); self.btn_stop.hide(); self.learn_label.setText("FIN")
        self.result_output.setText("Session terminee."); self.result_output.show(); self.btn_ok.show(); self.btn_ok.setFocus()

    def evaluate_practice_adaptivity(self):
        if self.mode != "LETTERS":
            return
        if not self.practice_letter_weights:
            self.initialize_practice_weights()
            return
        self.update_practice_weights()

    def start_game(self, mode):
        self.mode = mode
        self.score = 0
        self.practice_round_counter = 0
        self.pages.setCurrentIndex(4)
        if mode == "LETTERS":
            self.initialize_practice_weights()
            self.practice_minute_timer.start(60000)
        self.next_round()

    def next_round(self):
        self.timer.stop()
        self.clear_input_field(self.input_field)
        
        if self.mode == "LETTERS":
            letters = self.get_current_week_practice_letters()
            if self.practice_letter_weights and self.practice_round_counter >= 100:
                weights = [self.practice_letter_weights.get(letter, 1) for letter in letters]
                self.target = random.choices(letters, weights=weights, k=1)[0]
            else:
                self.target = random.choice(letters)
            self.target_label.setText(self.target)
            if self.speaker:
                self.speaker.output(self.target)
            self.input_field.setEnabled(True)
            self.input_field.setFocus()
            self.timer.start(5000)
            self.practice_round_counter += 1
        else:
            week_words = self.get_current_week_words()
            if week_words:
                self.target = random.choice(week_words).upper()
            else:
                steps = self.get_current_week_steps()
                self.target = random.choice(steps)
            wait_time = len(self.target) * 2000

            self.target_label.setText(self.target)
            
            if self.speaker:
                self.input_field.setEnabled(False) 
                spelling = ", ".join(list(self.target))
                self.speaker.output(spelling)
                
                spelling_delay = len(self.target) * 150 + 400
                word_audio_delay = len(self.target) * 100 + 300
                total_delay = spelling_delay + word_audio_delay
                
                QTimer.singleShot(spelling_delay, lambda: self.speaker.output(self.target))
                QTimer.singleShot(total_delay, lambda: self.start_counting(wait_time))
            else:
                self.start_counting(wait_time)

    def start_counting(self, wait_time):
        self.input_field.setEnabled(True)
        self.input_field.setFocus()
        winsound.Beep(1000, 150)
        self.timer.start(wait_time)

    def check_input(self, text):
        if not text: return
        if text.upper() == self.target.upper():
            self.timer.stop()
            winsound.Beep(1500, 100)
            self.log_data(self.target, "Correct")
            self.score += 1
            self.score_label.setText(f"Score: {self.score}")
            self.next_round()
        elif len(text) >= len(self.target):
            winsound.Beep(400, 200)
            self.log_data(self.target, "Error")
            self.clear_input_field(self.input_field)
            self.next_round()

    def time_out(self):
        winsound.Beep(600, 800) 
        self.log_data(self.target, "Error")
        self.next_round()

    def stop_game(self):
        self.timer.stop()
        self.practice_minute_timer.stop()
        self.pages.setCurrentIndex(3)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TypingApp()
    win.show()
    sys.exit(app.exec_())