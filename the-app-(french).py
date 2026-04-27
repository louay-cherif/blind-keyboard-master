import sys
import random
import winsound
import csv
import os
import time
import w2words
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QLineEdit, QLabel, QStackedWidget)
from PyQt5.QtCore import Qt, QTimer

class TypingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Adapted Informatics Initiative Official Keyboard typing app for visually impaired people")
        self.resize(800, 600)
        
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.curriculum = {
            "Semaine 1: Ligne de Base": ["QSDF", "GHJ", "KLM", "QSDFGHJKLM"],
            "Semaine 2: Ligne Supérieure": ["AZER", "TYU", "IOP", "AZERTYUIOP"],
            "Semaine 3: Ligne Inférieure": ["WXC", "VBN", "WXCVBN"],
            "Semaine 4: Mixage des Lignes": ["QSDFGHJKLM", "AZERTYUIOP", "WXCVBN", "AZERTYUIOPQSDFGHJKLMWXCVBN"],
            "Semaine 5: Majuscules et Symboles": ["ABCDEFGHIJKLMNOPQRSTUVWXYZ", ",;:!?", "./§", "ALL_COMBINED"]
        }
        
        self.weeks_keys = list(self.curriculum.keys())
        self.current_week_idx = 0
        self.current_step_idx = 0
        self.repetition_count = 0
        self.in_random_phase = False
        self.random_count = 0
        self.random_phase_limit = 20
        
        self.week2_learning_flow = [
            {"mode": "random", "chars": "QSDFGHJKLM", "duration": 300},
            {"mode": "learn", "chars": "AZER"},
            {"mode": "random", "chars": "AZER", "count": 20},
            {"mode": "learn", "chars": "TYU"},
            {"mode": "random", "chars": "TYU", "count": 20},
            {"mode": "learn", "chars": "IOP"},
            {"mode": "random", "chars": "IOP", "count": 20},
            {"mode": "random", "chars": "AZERTYUIOP", "count": 40},
            {"mode": "random", "chars": "AZERTYUIOPQSDFGHJKLM", "count": 60},
        ]
        self.week2_learning_phase_idx = 0
        self.week2_phase_start = None
        
        self.mode = ""
        self.target = ""
        self.score = 0
        self.user_name = ""
        
        self.practice_minute_timer = QTimer()
        self.practice_minute_timer.timeout.connect(self.evaluate_practice_adaptivity)
        self.practice_phase_start = None
        self.practice_first_five_done = False
        self.practice_letter_weights = {}
        self.last_letter_accuracy = {}
        self.week2_words = getattr(w2words, 'words', [])
        
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
        """Extract and clean username for file naming."""
        return "".join(c for c in self.user_name if c.isalnum() or c in (' ', '_')).rstrip()

    def get_user_csv_path(self):
        """Generate the CSV file path for the current user and week."""
        clean_name = self.get_clean_username()
        return os.path.join(self.base_dir, f"{clean_name}_Week_{self.current_week_idx + 1}.csv")

    def clear_input_field(self, field):
        """Safely clear an input field without triggering signals."""
        field.blockSignals(True)
        field.clear()
        field.blockSignals(False)

    def is_week2(self):
        """Check if current week is Week 2 (index 1)."""
        return self.current_week_idx == 1

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
        except:
            pass

    def get_weak_chars(self):
        file_path = self.get_user_csv_path()
        if not os.path.isfile(file_path): return []
        stats = {}
        try:
            with open(file_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    char = row["Character"]
                    if char not in stats: stats[char] = {"correct": 0, "total": 0}
                    stats[char]["total"] += 1
                    if row["Status"] == "Correct": stats[char]["correct"] += 1
            return [c for c, s in stats.items() if s["total"] > 0 and (s["correct"]/s["total"]) < 0.7]
        except: return []

    def get_current_week_letters(self):
        steps = self.curriculum[self.weeks_keys[self.current_week_idx]]
        letters = set()
        for step in steps:
            for char in step:
                if char.isalpha():
                    letters.add(char.upper())
        return ''.join(sorted(letters))

    def setup_week_selection(self):
        page = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Choisissez votre semaine :"))
        for i, week_name in enumerate(self.weeks_keys):
            btn = QPushButton(week_name)
            btn.clicked.connect(lambda checked, idx=i: self.select_week(idx))
            layout.addWidget(btn)
        page.setLayout(layout)
        self.pages.addWidget(page)

    def select_week(self, idx):
        self.current_week_idx = idx
        self.pages.setCurrentIndex(1)

    def setup_identification_page(self):
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
        self.btn_ok.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        
        self.btn_stop = QPushButton("Quitter")
        self.btn_stop.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        
        layout.addWidget(self.result_output)
        layout.addWidget(self.learn_label)
        layout.addWidget(self.learn_input)
        layout.addWidget(self.btn_ok)
        layout.addWidget(self.btn_stop)
        page.setLayout(layout)
        self.pages.addWidget(page)

    def setup_practice_selection(self):
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

    def start_learning(self):
        self.user_name = self.name_input.text().strip()
        if self.user_name:
            self.current_step_idx = 0
            self.repetition_count = 0
            self.in_random_phase = False
            self.random_count = 0
            self.week2_learning_phase_idx = 0
            if self.is_week2():
                self.week2_phase_start = time.time()
            self.result_output.hide()
            self.btn_ok.hide()
            self.btn_stop.show()
            self.learn_input.show()
            self.pages.setCurrentIndex(2)
            self.update_learning_target()

    def start_practice(self):
        self.user_name = self.name_input.text().strip()
        if self.user_name:
            if self.mode == "LETTERS":
                self.initialize_practice_adaptivity()
            self.pages.setCurrentIndex(3)

    def update_learning_target(self):
        self.clear_input_field(self.learn_input)
        if self.is_week2() and self.week2_learning_phase_idx < len(self.week2_learning_flow):
            self.update_learning_target_week2()
            return
        steps = self.curriculum[self.weeks_keys[self.current_week_idx]]
        current_chars = steps[self.current_step_idx]
        if not self.in_random_phase:
            char_idx = self.repetition_count // 10
            if char_idx < len(current_chars):
                self.target = current_chars[char_idx]
            else:
                self.in_random_phase = True
                self.random_count = 0
                self.update_learning_target()
                return
        else:
            self.target = random.choice(current_chars)
        self.learn_label.setText("")
        self.learn_label.setText(self.target)
        self.learn_input.setAccessibleName(self.target)
        self.learn_input.setFocus()

    def update_learning_target_week2(self):
        phase = self.week2_learning_flow[self.week2_learning_phase_idx]
        mode = phase.get("mode")
        chars = phase.get("chars", "")
        self.learn_label.setText("")
        if mode == "random":
            if phase.get("duration"):
                elapsed = time.time() - self.week2_phase_start
                if elapsed >= phase["duration"]:
                    self.advance_week2_phase()
                    return
            self.target = random.choice(chars)
        elif mode == "learn":
            char_idx = self.repetition_count // 10
            if char_idx < len(chars):
                self.target = chars[char_idx]
            else:
                self.advance_week2_phase()
                return
        self.learn_label.setText(self.target)
        self.learn_input.setAccessibleName(self.target)
        self.learn_input.setFocus()

    def advance_week2_phase(self):
        self.week2_learning_phase_idx += 1
        self.repetition_count = 0
        self.random_count = 0
        self.week2_phase_start = time.time()
        if self.week2_learning_phase_idx >= len(self.week2_learning_flow):
            self.end_session()
            return
        self.update_learning_target_week2()

    def check_learn_input(self, text):
        if not text: return
        is_correct = (text[-1].upper() == self.target.upper()) if self.current_week_idx < 4 else (text == self.target)
        if is_correct:
            winsound.Beep(1500, 100)
            self.log_data(self.target, "Correct")
            if self.is_week2() and self.week2_learning_phase_idx < len(self.week2_learning_flow):
                phase = self.week2_learning_flow[self.week2_learning_phase_idx]
                if phase["mode"] == "learn":
                    self.repetition_count += 1
                    if self.repetition_count >= len(phase["chars"]) * 10:
                        self.advance_week2_phase()
                else:
                    self.random_count += 1
                    if self.random_count >= phase.get("count", self.random_phase_limit):
                        self.advance_week2_phase()
            else:
                if not self.in_random_phase:
                    self.repetition_count += 1
                else:
                    self.random_count += 1
                    if self.random_count >= self.random_phase_limit:
                        self.current_step_idx += 1
                        self.repetition_count = 0
                        self.in_random_phase = False
                        if self.current_step_idx >= len(self.curriculum[self.weeks_keys[self.current_week_idx]]):
                            self.end_session()
                            return
            self.update_learning_target()
        elif len(text) >= len(self.target):
            winsound.Beep(400, 200)
            self.log_data(self.target, "Error")
            self.clear_input_field(self.learn_input)

    def end_session(self):
        self.learn_input.hide()
        self.btn_stop.hide()
        self.learn_label.setText("FIN")
        
        file_path = self.get_user_csv_path()
        
        total = 0
        correct = 0
        try:
            with open(file_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    total += 1
                    if row["Status"] == "Correct": correct += 1
            accuracy = (correct / total * 100) if total > 0 else 0
            summary = f"Session terminee. Score: {correct}/{total} ({accuracy:.1f}%). Analyse enregistree."
        except:
            summary = "Session terminee. Analyse enregistree."

        self.result_output.setText(summary)
        self.result_output.show()
        self.btn_ok.show()
        self.btn_ok.setFocus()

    def initialize_practice_adaptivity(self):
        self.practice_phase_start = time.time()
        self.practice_first_five_done = False
        self.practice_letter_weights = {c: 1.0 for c in "AZERTYUIOPQSDFGHJKLM"}
        self.last_letter_accuracy = {}
        if not self.practice_minute_timer.isActive():
            self.practice_minute_timer.start(60000)

    def collect_practice_stats(self):
        file_path = self.get_user_csv_path()
        if not os.path.isfile(file_path):
            return {}
        stats = {}
        try:
            with open(file_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    char = row["Character"].upper()
                    if len(char) != 1:
                        continue
                    if char not in stats:
                        stats[char] = {"correct": 0, "total": 0}
                    stats[char]["total"] += 1
                    if row["Status"] == "Correct":
                        stats[char]["correct"] += 1
        except:
            return {}
        return stats

    def evaluate_practice_adaptivity(self):
        current_stats = self.collect_practice_stats()
        for letter, stats in current_stats.items():
            total = stats["total"]
            correct = stats["correct"]
            current_accuracy = (correct / total) if total > 0 else 0
            previous_accuracy = self.last_letter_accuracy.get(letter, current_accuracy)
            if current_accuracy > previous_accuracy + 0.05:
                self.practice_letter_weights[letter] = max(0.5, self.practice_letter_weights.get(letter, 1.0) * 0.8)
            elif current_accuracy < previous_accuracy - 0.05:
                self.practice_letter_weights[letter] = min(5.0, self.practice_letter_weights.get(letter, 1.0) * 1.3)
            self.last_letter_accuracy[letter] = current_accuracy
        if time.time() - self.practice_phase_start >= 300:
            self.practice_first_five_done = True

    def choose_weighted_letter(self, letters):
        weights = [self.practice_letter_weights.get(letter, 1.0) for letter in letters]
        total = sum(weights)
        if total <= 0:
            return random.choice(letters)
        pick = random.random() * total
        current = 0
        for letter, weight in zip(letters, weights):
            current += weight
            if pick <= current:
                return letter
        return letters[-1]

    def start_game(self, mode):
        self.mode = mode
        self.score = 0
        if self.mode == "LETTERS" and self.is_week2():
            self.initialize_practice_adaptivity()
        self.pages.setCurrentIndex(4)
        self.next_round()

    def next_round(self):
        self.timer.stop()
        self.clear_input_field(self.input_field)
        if self.mode == "LETTERS":
            if self.is_week2():
                if not self.practice_first_five_done:
                    self.target = self.choose_weighted_letter("AZERTYUIOP")
                else:
                    letters = "AZERTYUIOPQSDFGHJKLM"
                    self.target = self.choose_weighted_letter(letters)
            else:
                weaks = self.get_weak_chars()
                week_letters = self.get_current_week_letters()
                self.target = random.choice(weaks) if weaks and random.random() < 0.6 else random.choice(week_letters)
        else:
            if self.is_week2() and self.week2_words:
                self.target = random.choice(self.week2_words).upper()
            else:
                steps = self.curriculum[self.weeks_keys[self.current_week_idx]]
                self.target = random.choice(steps)
        self.target_label.setText("")
        self.target_label.setText(self.target)
        self.input_field.setAccessibleName(self.target)
        self.input_field.setFocus()
        self.timer.start(5000)

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
        self.log_data(self.target, "Error")
        self.next_round()

    def stop_game(self):
        self.timer.stop()
        if self.practice_minute_timer.isActive():
            self.practice_minute_timer.stop()
        self.pages.setCurrentIndex(3)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TypingApp()
    win.show()
    sys.exit(app.exec_())