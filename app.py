# the imports
import sys
import random
import winsound
import csv
import os
import time
import w1words
import w2words
import w3words
from PyQt5.QtWidgets import QApplication

try:
    from accessible_output2.outputs import auto
    HAS_ACCESSIBLE = True
except ImportError:
    HAS_ACCESSIBLE = False


class AppBackend:
    def __init__(self):
        self.speaker = auto.Auto() if HAS_ACCESSIBLE else None
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.base_dir, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # I am thinking about figuring out how to to get rid of this variable and instead call the week data from the week file, that will make the code easier to maintain. Now I'll leave it as it is and see it later
        self.weeks = [
            {
                "name": "Semaine 1: Ligne de Base",
                "steps": ["QSDF", "GHJ", "KLM", "QSDFGHJKLM"],
                "practice_letters": ["QSDFGHJKLM"],
                "words": getattr(w1words, "words", []),
                "learning_flow": [
                    {"mode": "learn", "chars": "QSDF"},
                    {"mode": "random", "chars": "QSDF", "duration": 300},
                    {"mode": "learn", "chars": "GHJ"},
                    {"mode": "random", "chars": "GHJ", "count": 40},
                    {"mode": "random", "chars": "QSDFGHJ", "duration": 300},
                    {"mode": "learn", "chars": "KLM"},
                    {"mode": "random", "chars": "KLM", "count": 40},
                    {"mode": "random", "chars": "QSDFGHJKLM", "count": 250},
                ],
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
        self.practice_letter_weights = {}
        self.last_letter_accuracy = {}

    # returns a cleaned version of the username for log file naming
    def get_clean_username(self):
        return "".join(c for c in self.user_name if c.isalnum() or c in (' ', '_')).rstrip()

    # returns a log file path with the file named using the cleaned username and current week index
    def get_user_csv_path(self):
        clean_name = self.get_clean_username()
        return os.path.join(self.data_dir, f"{clean_name}_Week_{self.current_week_idx + 1}.csv")

    # returns the current week data dictionary
    def current_week(self):
        return self.weeks[self.current_week_idx]

    # returns the steps for the current week, or an empty list if not defined
    def get_current_week_steps(self):
        return self.current_week().get("steps", [])

    # returns the defined letters for the current week, or extracts them from steps if not explicitly defined
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

    # This function calculates the accuracy for each letter in the current week's practice set based on the user's logged data, and returns a dictionary mapping each letter to its accuracy from 0 to 1 (or None if no data is available for the letter or the entire file is missing).
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


    # This function computes a practice weight for a given letter based on its accuracy and the previous accuracy. The weight is higher for letters with lower accuracy, and it adjusts based on whether the accuracy has improved or worsened compared to the previous accuracy. The weight is constrained to be between 1 and 20.
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


    # This function initializes the practice letter weights by calculating the accuracy for each letter using the get_current_week_letter_stats function and then computing the practice weight for each letter using the compute_practice_weight function. The resulting weights are stored in the practice_letter_weights dictionary, and the last_letter_accuracy is updated to keep track of the current accuracies for future comparisons.
    def initialize_practice_weights(self):
        accuracies = self.get_current_week_letter_stats()
        self.practice_letter_weights = {}
        for letter, accuracy in accuracies.items():
            self.practice_letter_weights[letter] = self.compute_practice_weight(accuracy)
        self.last_letter_accuracy = accuracies


    # This function updates the practice letter weights by recalculating the accuracies for each letter and comparing them to the previous accuracies stored in last_letter_accuracy. The compute_practice_weight function is used to adjust the weights based on the new accuracies and whether they have improved or worsened compared to the previous values. The updated weights are stored in practice_letter_weights, and last_letter_accuracy is updated with the new accuracies for future comparisons.
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


    # This function logs the user's input for a given character and its correctness status to a CSV file. If the user_name is not set, it does nothing. It constructs the file path using the get_user_csv_path function, checks if the file already exists to determine if headers need to be written, and then appends a new row with the character and its status ("Correct" or "Incorrect"). If any error occurs during file operations, it silently fails without crashing the application.
    def log_data(self, char, status):
        if not self.user_name: 
            return
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


            # this function works for the learning section only
    def generate_learning_target(self):
        """Generate the next target character for learning phase."""
        if self.has_current_week_learning_flow() and self.week_learning_phase_idx < len(self.get_current_week_learning_flow()):
            phase = self.get_current_week_learning_flow()[self.week_learning_phase_idx]
            mode = phase.get("mode")
            chars = phase.get("chars", "")
            
            if mode == "random":
                if phase.get("duration"):
                    elapsed = time.time() - self.week_phase_start
                    if elapsed >= phase["duration"]:
                        return None  # Signal to advance phase
                if phase.get("count") and self.repetition_count >= phase["count"]:
                    return None  # Signal to advance phase
                self.target = random.choice(chars)
            elif mode == "learn":
                char_idx = self.repetition_count // 10
                if char_idx < len(chars):
                    self.target = chars[char_idx]
                else:
                    return None  # Signal to advance phase
            return self.target
        
        # Standard step-based learning
        steps = self.get_current_week_steps()
        current_chars = steps[self.current_step_idx]
        if not self.in_random_phase:
            char_idx = self.repetition_count // 10
            if char_idx < len(current_chars):
                self.target = current_chars[char_idx]
            else:
                self.in_random_phase = True
                return self.generate_learning_target()
        else:
            self.target = random.choice(current_chars)
        return self.target


    def advance_week_learning_phase(self):
        self.week_learning_phase_idx += 1
        self.repetition_count = 0
        self.week_phase_start = time.time()


    def check_learning_input(self, text, target):
        """Validate learning input and return result."""
        if not text:
            return None
        
        is_correct = (text[-1].upper() == target.upper()) if self.current_week_idx < 4 else (text == target)
        
        should_log = True
        if self.has_current_week_learning_flow() and self.week_learning_phase_idx < len(self.get_current_week_learning_flow()):
            phase = self.get_current_week_learning_flow()[self.week_learning_phase_idx]
            if phase.get("mode") == "learn":
                should_log = False
        
        return {
            "correct": is_correct,
            "should_log": should_log,
            "should_clear": len(text) >= len(target)
        }

    def check_game_input(self, text, target):
        """Validate game input and return result."""
        if not text:
            return None
        
        is_correct = text.upper() == target.upper()
        should_clear = len(text) >= len(target)
        
        return {
            "correct": is_correct,
            "should_clear": should_clear
        }

    def generate_game_target(self):
        """Generate next target for game/practice."""
        if self.mode == "LETTERS":
            letters = self.get_current_week_practice_letters()
            if self.practice_letter_weights and self.practice_round_counter >= 100:
                weights = [self.practice_letter_weights.get(letter, 1) for letter in letters]
                self.target = random.choices(letters, weights=weights, k=1)[0]
            else:
                self.target = random.choice(letters)
        else:  # WORDS mode
            week_words = self.get_current_week_words()
            if week_words:
                self.target = random.choice(week_words).upper()
            else:
                steps = self.get_current_week_steps()
                self.target = random.choice(steps)
        
        return self.target

    def get_word_pronunciation(self):
        """Get the pronunciation details for current word target."""
        target = self.target
        spelling = ", ".join(list(target))
        
        spelling_delay = len(target) * 150 + 400
        word_audio_delay = len(target) * 100 + 300
        total_delay = spelling_delay + word_audio_delay
        wait_time = len(target) * 2000
        
        return {
            "spelling": spelling,
            "spelling_delay": spelling_delay,
            "word_audio_delay": word_audio_delay,
            "total_delay": total_delay,
            "wait_time": wait_time
        }

    def should_end_week_learning(self):
        """Check if learning flow is complete."""
        return self.week_learning_phase_idx >= len(self.get_current_week_learning_flow())



# Entry Point
if __name__ == "__main__":
    from french import AppFrontend
    
    app = QApplication(sys.argv)
    logic = AppBackend()
    win = AppFrontend(logic)
    win.show()
    sys.exit(app.exec_())