from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
try:
    from app import AccessibleLabel
except ImportError:
    # Fallback definition 
    class AccessibleLabel(QLabel):
        def __init__(self, text="", accessible_desc=""):
            super().__init__(text)
            self.setFocusPolicy(Qt.StrongFocus)
            self.accessible_desc = accessible_desc
            if accessible_desc:
                self.setAccessibleDescription(accessible_desc)
            self.setWordWrap(True)   # important for long text


class LanguageSelector(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Home - Adapted Informatics Initiative Software")
        self.setModal(True)
        self.selected = None   # store user's language choice

        layout = QVBoxLayout()
        # Use AccessibleLabel instead of QLabel
        welcome_text = (
            "Welcome to the Adapted Informatics Initiative Software! "
            "An open-source software designed by Louay Cherif with collaboration of Aymen Ferchichi "
            "to assist visually impaired people mastering keyboard typing in an accessible environment "
            "designed specifically for them. Please select your preferred language to continue:"
        )
        welcome = AccessibleLabel(
            text=welcome_text,
            accessible_desc="Application welcome message. " + welcome_text
        )
        layout.addWidget(welcome)
        btn_en = QPushButton("English")
        btn_fr = QPushButton("Français")

        btn_en.clicked.connect(lambda: self.select_language('en'))
        btn_fr.clicked.connect(lambda: self.select_language('fr'))

        layout.addWidget(btn_en)
        layout.addWidget(btn_fr)
        self.setLayout(layout)

    def select_language(self, lang):
        self.selected = lang
        self.accept()   # close dialog with QDialog.Accepted           