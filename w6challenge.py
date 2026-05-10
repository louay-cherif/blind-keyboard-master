"""
Week 6: Ultimate Challenge - Final comprehensive keyboard mastery mode
Separated UI and Logic classes for maintainability and accessibility
"""

import time
import os
import csv
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, 
                             QLabel, QStackedWidget, QDialog, QApplication, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
import winsound

# ============= WEEK 6 LOGIC =============

class Week6Logic:
    """
    Logic layer for Week 6 challenge.
    Manages state, XP, boss health, rank calculations, and mode progression.
    Inherits from main logic to maintain connection with base app logic.
    """
    
    def __init__(self, base_logic, user_name=""):
        """
        Initialize Week6Logic
        Args:
            base_logic: Reference to AppBackend instance for inheritance
            user_name: Username passed from main app
        """
        self.base_logic = base_logic
        self.user_name = user_name
        
        # Challenge state variables
        self.xp_balance = 50
        self.xp_max = 1500
        self.boss_health = 100  # Percentage
        self.current_rank = "Beginner"
        
        # Mode tracking
        self.modes = {
            "warmup": {"name": "Warmup Gate", "status": "open", "completed": False},
            "combo": {"name": "Combo Rush", "status": "locked", "completed": False},
            "precision": {"name": "Precision Arena", "status": "locked", "completed": False},
            "sentence": {"name": "Sentence Mode", "status": "locked", "completed": False},
            "survival": {"name": "Survival Gate", "status": "locked", "completed": False},
            "crazy_party": {"name": "Crazy Keyboard Party", "status": "locked", "completed": False},
        }
        
        # Track completion order
        self.completed_modes_count = 0
        
        # Challenge timing
        self.challenge_start_time = None
        self.csv_file_path = None
    
    def get_rank_from_xp(self):
        """Calculate rank based on current XP"""
        if self.xp_balance < 300:
            return "Beginner"
        elif self.xp_balance < 600:
            return "Challenger"
        elif self.xp_balance < 900:
            return "Elite Typer"
        elif self.xp_balance < 1200:
            return "Warrior"
        else:
            return "Master"
    
    def mark_mode_complete(self, mode_key):
        """
        Mark a mode as completed and handle state changes
        Args:
            mode_key: Key of the mode being completed
        """
        if self.modes[mode_key]["status"] != "done" and not self.modes[mode_key]["completed"]:
            self.modes[mode_key]["status"] = "done"
            self.modes[mode_key]["completed"] = True
            self.completed_modes_count += 1
            
            # Decrease boss health by 20% for each completed mode
            health_decrease = 20
            self.boss_health = max(0, self.boss_health - health_decrease)
            
            # Increase XP
            xp_increase = 225  # So 50 + (225*6) = 50 + 1350 = 1400, need some bonus
            self.add_xp(xp_increase)
            
            # Unlock other modes (except crazy party)
            if self.completed_modes_count == 1:  # First mode just completed
                for mode, data in self.modes.items():
                    if mode != "crazy_party" and mode != mode_key:
                        if data["status"] == "locked":
                            data["status"] = "unlocked"
            
            # Unlock crazy party only after all 5 modes are done
            if self.completed_modes_count == 5:
                self.modes["crazy_party"]["status"] = "unlocked"
    
    def add_xp(self, amount):
        """
        Add XP to balance
        Args:
            amount: Amount of XP to add
        """
        if self.xp_balance < self.xp_max:
            self.xp_balance = min(self.xp_balance + amount, self.xp_max)
    
    def is_challenge_complete(self):
        """Check if challenge is complete (1500 XP reached and crazy party done)"""
        return self.xp_balance >= self.xp_max and self.modes["crazy_party"]["completed"]
    
    def get_mode_status_text(self, mode_key):
        """Get display text for mode status with helper text"""
        mode = self.modes[mode_key]
        if mode["completed"]:
            return "[completed] - Press to replay"
        elif mode["status"] == "locked":
            if mode_key == "crazy_party":
                return "[locked] - Finish all modes above to unlock"
            else:
                return "[locked] - Warmup Gate required to unlock this"
        else:  # open or unlocked
            return "[open] - Press Space to start"
    
    def init_challenge_progress_file(self):
        """Initialize CSV file for tracking challenge progress"""
        if not self.user_name:
            return
        
        clean_name = self.base_logic.get_clean_username()
        user_dir = os.path.join(self.base_logic.data_dir, clean_name)
        os.makedirs(user_dir, exist_ok=True)
        
        self.csv_file_path = os.path.join(user_dir, f"{clean_name}_Week6_Challenge.csv")
        
        # Create or append to CSV file
        file_exists = os.path.exists(self.csv_file_path)
        
        try:
            with open(self.csv_file_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    # Write header
                    writer.writerow(["Timestamp", "XP Balance", "Boss Health", "Completed Modes", "Modes Status"])
                # Write initial entry
                completed_modes = [k for k, v in self.modes.items() if v["completed"]]
                writer.writerow([
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    self.xp_balance,
                    self.boss_health,
                    ",".join(completed_modes) if completed_modes else "none",
                    str(self.modes)
                ])
        except Exception as e:
            if self.base_logic.speaker:
                self.base_logic.speaker.output(f"Error creating progress file: {str(e)}")
    
    def save_progress(self):
        """Save current progress to CSV file"""
        if not self.csv_file_path:
            return
        
        try:
            with open(self.csv_file_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                completed_modes = [k for k, v in self.modes.items() if v["completed"]]
                writer.writerow([
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    self.xp_balance,
                    self.boss_health,
                    ",".join(completed_modes) if completed_modes else "none",
                    str(self.modes)
                ])
        except Exception as e:
            if self.base_logic.speaker:
                self.base_logic.speaker.output(f"Error saving progress: {str(e)}")


# ============= WEEK 6 UI =============

class Week6UI(QWidget):
    """
    UI layer for Week 6 challenge.
    Handles all user interface elements and user interactions.
    Separate from logic for clean architecture.
    """
    
    def __init__(self, base_logic, user_name="", is_english=True):
        """
        Initialize Week6UI
        Args:
            base_logic: Reference to AppBackend instance
            user_name: Username passed from main app
            is_english: True for English, False for French
        """
        super().__init__()
        self.base_logic = base_logic
        self.base_logic.user_name = user_name  # Store username in base logic
        self.logic = Week6Logic(base_logic, user_name)
        self.is_english = is_english
        self.is_shown = False
        
        self.setWindowTitle("Week 6 Challenge")
        self.resize(800, 600)
        
        # Apply dark theme
        self.setStyleSheet("""
            QWidget { background-color: #0a0a12; color: #ffffff; font-family: Arial; font-size: 24px; }
            QPushButton { background-color: #16213e; border-radius: 12px; padding: 15px; color: white; border: 2px solid #e94560; margin: 5px; }
            QPushButton:hover { background-color: #e94560; }
            QPushButton:disabled { background-color: #444444; color: #888888; border-color: #666666; }
            QLineEdit { padding: 18px; background-color: #1a1a2e; color: #0fecb0; border: 2px solid #0fecb0; border-radius: 10px; text-align: center; }
            QLineEdit[readOnly="true"] { color: #f9d342; border-color: #f9d342; }
        """)
        
        # Setup pages
        self.pages = QStackedWidget()
        self.setup_identification_page()
        self.setup_challenge_page()
        self.setup_victory_page()
        
        layout = QVBoxLayout()
        layout.addWidget(self.pages)
        self.setLayout(layout)
        
        # Timer for various operations
        self.timer = QTimer()
    
    def set_lang_strings(self):
        """Set language-specific strings"""
        if self.is_english:
            self.strings = {
                "id_title": "WEEK 6: ULTIMATE CHALLENGE",
                "id_label_name": "Enter your name:",
                "id_welcome": "Welcome to Week 6 Challenge",
                "id_instructions": "Welcome to Week 6 Challenge",
                "id_button_start": "Move to Challenge Battle",
                "id_button_back": "Back",
                
                "challenge_title": "CHALLENGE BATTLE",
                "xp_label": "XP Balance: ",
                "boss_health_label": "Boss Health: ",
                "rank_label": "Rank: ",
                "button_exit": "Exit",
                
                "victory_title": "VICTORY!",
                "victory_message": "Congratulations! You defeated the boss!",
                "victory_button": "Okay",
            }
        else:
            self.strings = {
                "id_title": "SEMAINE 6: DÉFI ULTIME",
                "id_label_name": "Entrez votre nom :",
                "id_welcome": "Bienvenue au défi de la Semaine 6",
                "id_instructions": "Bienvenue au défi de la Semaine 6",
                "id_button_start": "Aller au Combat de Défi",
                "id_button_back": "Retour",
                
                "challenge_title": "COMBAT DE DÉFI",
                "xp_label": "Solde XP : ",
                "boss_health_label": "Santé du Boss : ",
                "rank_label": "Rang : ",
                "button_exit": "Quitter",
                
                "victory_title": "VICTOIRE !",
                "victory_message": "Félicitations ! Vous avez vaincu le boss !",
                "victory_button": "Okay",
            }
    
    def setup_identification_page(self):
        """Page 0: Instructions page (username already entered in main app)"""
        self.set_lang_strings()
        
        page = QWidget()
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(self.strings["id_title"])
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #e94560;")
        layout.addWidget(title_label)
        
        # Welcome/Instructions readonly field
        self.id_instructions = QLineEdit()
        self.id_instructions.setReadOnly(True)
        self.id_instructions.setText(self.strings["id_instructions"])
        self.id_instructions.setMinimumHeight(150)
        layout.addWidget(self.id_instructions)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        btn_start = QPushButton(self.strings["id_button_start"])
        btn_start.clicked.connect(self.start_challenge)
        button_layout.addWidget(btn_start)
        
        btn_back = QPushButton(self.strings["id_button_back"])
        btn_back.clicked.connect(self.go_back)
        button_layout.addWidget(btn_back)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        page.setLayout(layout)
        self.pages.addWidget(page)
    
    def setup_challenge_page(self):
        """Page 1: Main challenge battle page"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(self.strings["challenge_title"])
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #0fecb0;")
        layout.addWidget(title_label)
        
        # Stats section
        stats_layout = QHBoxLayout()
        
        # XP Balance
        xp_layout = QVBoxLayout()
        self.xp_display = QLineEdit()
        self.xp_display.setReadOnly(True)
        self.xp_display.setText("50/1500 - XP Balance")
        xp_layout.addWidget(self.xp_display)
        stats_layout.addLayout(xp_layout)
        
        # Boss Health
        health_layout = QVBoxLayout()
        self.health_display = QLineEdit()
        self.health_display.setReadOnly(True)
        self.health_display.setText("100% - Boss Health")
        health_layout.addWidget(self.health_display)
        stats_layout.addLayout(health_layout)
        
        # Rank
        rank_layout = QVBoxLayout()
        self.rank_display = QLineEdit()
        self.rank_display.setReadOnly(True)
        self.rank_display.setText("Beginner - Rank")
        rank_layout.addWidget(self.rank_display)
        stats_layout.addLayout(rank_layout)
        
        layout.addLayout(stats_layout)
        
        # Separator
        separator = QLabel("_" * 50)
        layout.addWidget(separator)
        
        # Modes section - Store button references for later updates
        self.mode_buttons = {}
        modes_label = QLabel("MODES" if self.is_english else "MODES")
        modes_label.setAlignment(Qt.AlignCenter)
        modes_label.setStyleSheet("font-weight: bold; color: #f9d342;")
        layout.addWidget(modes_label)
        
        modes_layout = QVBoxLayout()
        mode_order = ["warmup", "combo", "precision", "sentence", "survival", "crazy_party"]
        for mode_key in mode_order:
            mode_data = self.logic.modes[mode_key]
            status_text = self.logic.get_mode_status_text(mode_key)
            btn = QPushButton(f"{mode_data['name']} {status_text}")
            btn.clicked.connect(lambda checked, mk=mode_key: self.on_mode_clicked(mk))
            
            # Keep button enabled even if locked - so user can see status and hint
            self.mode_buttons[mode_key] = btn
            modes_layout.addWidget(btn)
        
        layout.addLayout(modes_layout)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        btn_exit = QPushButton(self.strings["button_exit"])
        btn_exit.clicked.connect(self.exit_challenge)
        button_layout.addWidget(btn_exit)
        
        layout.addLayout(button_layout)
        
        page.setLayout(layout)
        self.pages.addWidget(page)
    
    def setup_victory_page(self):
        """Page 2: Victory page"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(self.strings["victory_title"])
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 40px; font-weight: bold; color: #0fecb0;")
        layout.addWidget(title_label)
        
        # Message
        message = QLineEdit()
        message.setReadOnly(True)
        message.setText(self.strings["victory_message"])
        message.setMinimumHeight(100)
        layout.addWidget(message)
        
        # Okay button
        btn_ok = QPushButton(self.strings["victory_button"])
        btn_ok.clicked.connect(self.on_victory_complete)
        layout.addWidget(btn_ok)
        
        layout.addStretch()
        page.setLayout(layout)
        self.pages.addWidget(page)
    
    def start_challenge(self):
        """Start the challenge"""
        self.logic.challenge_start_time = time.time()
        self.logic.init_challenge_progress_file()
        self.pages.setCurrentIndex(1)
        
        if self.base_logic.speaker:
            msg = f"Started challenge for {self.logic.user_name}" if self.is_english else f"Défi lancé pour {self.logic.user_name}"
            self.base_logic.speaker.output(msg)
    
    def on_mode_clicked(self, mode_key):
        """Handle mode button click"""
        mode = self.logic.modes[mode_key]
        
        # If locked, announce unlock requirement
        if mode["status"] == "locked":
            if self.base_logic.speaker:
                if mode_key == "crazy_party":
                    msg = "Finish all modes above to unlock" if self.is_english else "Terminez tous les modes ci-dessus pour déverrouiller"
                else:
                    msg = "Warmup Gate required to unlock this" if self.is_english else "Warmup Gate requis pour déverrouiller"
                self.base_logic.speaker.output(msg)
            return
        
        # Mark mode as complete (placeholder for actual mode logic)
        if not mode["completed"]:
            self.logic.mark_mode_complete(mode_key)
            self.logic.save_progress()
            self.update_display()
            
            # Announce mode completion
            if self.base_logic.speaker:
                mode_name = self.logic.modes[mode_key]["name"]
                msg = f"{mode_name} completed" if self.is_english else f"{mode_name} complété"
                self.base_logic.speaker.output(msg)
            
            # Check if challenge is complete
            if self.logic.is_challenge_complete():
                self.logic.save_progress()
                self.pages.setCurrentIndex(2)
                if self.base_logic.speaker:
                    msg = "You have defeated the boss" if self.is_english else "Vous avez vaincu le boss"
                    self.base_logic.speaker.output(msg)
                winsound.Beep(2000, 200)
                return
        else:
            # Mode already completed - offer replay
            if self.base_logic.speaker:
                mode_name = self.logic.modes[mode_key]["name"]
                msg = f"Replaying {mode_name}" if self.is_english else f"Relancer {mode_name}"
                self.base_logic.speaker.output(msg)
        
        # TODO: Launch actual mode gameplay here
        if self.base_logic.speaker:
            mode_name = self.logic.modes[mode_key]["name"]
            msg = f"Starting {mode_name}" if self.is_english else f"Lancement de {mode_name}"
            self.base_logic.speaker.output(msg)
    
    def update_display(self):
        """Update all display elements"""
        # Update XP
        self.xp_display.setText(f"{self.logic.xp_balance}/{self.logic.xp_max} - XP Balance")
        
        # Update Boss Health
        self.health_display.setText(f"{self.logic.boss_health}% - Boss Health")
        
        # Update Rank
        new_rank = self.logic.get_rank_from_xp()
        self.rank_display.setText(f"{new_rank} - Rank")
        
        # Update mode buttons
        for mode_key, btn in self.mode_buttons.items():
            mode_data = self.logic.modes[mode_key]
            status_text = self.logic.get_mode_status_text(mode_key)
            
            btn.setText(f"{mode_data['name']} {status_text}")
            # All buttons remain enabled - locked ones just show status and hint
    
    def exit_challenge(self):
        """Exit the challenge and save progress"""
        self.logic.save_progress()
        self.base_logic.reset()
        self.close()
    
    def go_back(self):
        """Go back from challenge page"""
        self.logic.save_progress()
        self.base_logic.reset()
        self.close()
    
    def on_victory_complete(self):
        """Handle victory completion"""
        self.logic.save_progress()
        self.base_logic.reset()
        self.close()
    
    def show_challenge(self):
        """Show the challenge UI"""
        if not self.is_shown:
            self.set_lang_strings()
            self.pages.setCurrentIndex(0)
            self.is_shown = True

