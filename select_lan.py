from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton

# Always import from w6challenge  -  that is the single source of truth
# for AccessibleLabel and AccessibleBrowser across the whole project.
from w6challenge import AccessibleLabel, AccessibleBrowser


class LanguageSelector(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Home - Adapted Informatics Initiative Software")
        self.setModal(True)
        self.selected = None

        self.setWindowState(Qt.WindowMaximized)

        # Dark theme consistent with the rest of the app, slightly larger base font
        self.setStyleSheet("""
            QDialog     { background-color: #0a0a12; color: #ffffff;
                          font-family: Arial; font-size: 26px; }
            QPushButton { background-color: #16213e; border-radius: 12px;
                          padding: 18px; color: white;
                          border: 2px solid #e94560; margin: 8px;
                          font-size: 28px; }
            QPushButton:hover { background-color: #e94560; }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(20)

        # Welcome text  -  long and multi-line, so AccessibleBrowser is the right choice
        welcome_text = (
            "Welcome to the Adapted Informatics Initiative Software!\n\n"
            "An open-source software designed by Louay Cherif with collaboration of "
            "Aymen Ferchichi to assist visually impaired people mastering keyboard typing "
            "in an accessible environment designed specifically for them.\n\n"
            "Please select your preferred language to continue:"
        )
        welcome_label = AccessibleBrowser(
            text=welcome_text,
            accessible_text="Application welcome message. " + welcome_text,
        )
        welcome_label.setMinimumHeight(220)
        layout.addWidget(welcome_label)

        btn_en = QPushButton("English")
        btn_fr = QPushButton("Français")

        btn_en.clicked.connect(lambda: self.select_language('en'))
        btn_fr.clicked.connect(lambda: self.select_language('fr'))

        layout.addWidget(btn_en)
        layout.addWidget(btn_fr)
        layout.addStretch()
        self.setLayout(layout)

    def select_language(self, lang):
        self.selected = lang
        self.accept()
