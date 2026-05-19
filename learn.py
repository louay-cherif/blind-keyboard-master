import sys, wikipedia, re
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QSpinBox)
from PyQt5.QtCore import Qt, QTimer
from accessible_output2.outputs import auto
from static.accessible_widgets import AccessiblePushButton

class FlexibleTypingTutor(QWidget):
    def __init__(self):
        super().__init__()
        self.speaker = auto.Auto()
        self.segments = []
        self.current_idx = 0
        self.errors = 0
        
        self.setWindowTitle("Tuteur")
        layout = QVBoxLayout()

        self.topic_input = QLineEdit(placeholderText="Sujet...")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["fr", "en", "de", "ar"])
        self.sentence_count = QSpinBox(minimum=1, value=5)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Lettres", "Mots"])
        self.btn_start = AccessiblePushButton("Démarrer")
        self.status_label = QLabel("Cible")
        self.type_input = QLineEdit(enabled=False)

        layout.addWidget(QLabel("Sujet:"))
        layout.addWidget(self.topic_input)
        layout.addWidget(QLabel("Langue:"))
        layout.addWidget(self.lang_combo)
        layout.addWidget(QLabel("Phrases:"))
        layout.addWidget(self.sentence_count)
        layout.addWidget(QLabel("Mode:"))
        layout.addWidget(self.mode_combo)
        layout.addWidget(self.btn_start)
        layout.addWidget(QLabel("Taper:"))
        layout.addWidget(self.status_label)
        layout.addWidget(self.type_input)

        self.btn_start.clicked.connect(self.start_exercise)
        self.type_input.installEventFilter(self)
        self.setLayout(layout)

    def eventFilter(self, obj, event):
        if obj is self.type_input and event.type() == event.KeyPress and event.key() == Qt.Key_Space:
            self.check_input()
            return True
        return super().eventFilter(obj, event)

    def start_exercise(self):
        try:
            wikipedia.set_lang(self.lang_combo.currentText())
            summary = wikipedia.summary(self.topic_input.text(), sentences=self.sentence_count.value())
            clean_text = re.sub(r"[^\w\s]", "", summary)
            
            self.segments = clean_text.split()
            self.current_idx = 0
            self.errors = 0
            self.type_input.setEnabled(True)
            self.type_input.setFocus()
            self.next_round()
        except:
            self.speaker.output("Erreur")

    def next_round(self):
        if self.current_idx < len(self.segments):
            target = self.segments[self.current_idx]
            self.status_label.setText(target)
            self.type_input.clear()
            self.errors = 0
            
            if self.mode_combo.currentText() == "Lettres":
                spelling = " ".join(list(target))
                self.speaker.output(spelling)
                delay = len(spelling) * 150 + 300
                QTimer.singleShot(delay, lambda: self.speaker.output(target))
            else:
                self.speaker.output(target)
        else:
            self.speaker.output("Fin")
            self.type_input.setEnabled(False)

    def check_input(self):
        user_val = self.type_input.text().strip().lower()
        target = self.segments[self.current_idx].lower()

        if user_val == target:
            self.current_idx += 1
            self.next_round()
        else:
            self.errors += 1
            if self.errors >= 5:
                self.speaker.output("Suivant")
                self.current_idx += 1
                self.next_round()
            else:
                self.speaker.output("Faux")
                self.type_input.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FlexibleTypingTutor()
    window.show()
    sys.exit(app.exec_())