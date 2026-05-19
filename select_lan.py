
# Blind Keyboard Master - keyboard learning app accessible for visually impaired people
# Copyright (C) 2026 Louay Cherif
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                             QLabel)

from w6challenge import AccessibleLabel, AccessibleBrowser
from static.accessible_widgets import AccessiblePushButton

# Path to the developer picture relative to this file
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_PICTURE_PATH = os.path.join(_BASE_DIR, "static", "developer_picture.jpeg")


def _make_picture_label(size: int) -> QLabel:
    """
    Return a QLabel containing the developer picture scaled to `size` x `size`.
    Falls back to a plain-text placeholder if the file is not found.
    """
    lbl = QLabel()
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setFocusPolicy(Qt.NoFocus)
    if os.path.isfile(_PICTURE_PATH):
        pix = QPixmap(_PICTURE_PATH).scaled(
            size, size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        lbl.setPixmap(pix)
    else:
        # Graceful fallback: show initials if picture is missing
        lbl.setText("LC")
        lbl.setStyleSheet(
            f"font-size: {size // 3}px; font-weight: bold; color: #0fecb0;"
            "background-color: #16213e; border-radius: 8px;"
            f"min-width: {size}px; min-height: {size}px;"
        )
    return lbl


class LanguageSelector(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Home - Adapted Informatics Initiative Software")
        self.setModal(True)
        self.selected = None

        self.setWindowState(Qt.WindowMaximized)

        self.setStyleSheet("""
            QDialog {
                background-color: #0a0a12;
                color: #ffffff;
                font-family: Arial;
                font-size: 24px;
            }
            QPushButton {
                background-color: #16213e;
                border-radius: 12px;
                padding: 18px;
                color: white;
                border: 2px solid #e94560;
                margin: 8px;
                font-size: 28px;
            }
            QPushButton:hover { background-color: #e94560; }
        """)

        outer = QVBoxLayout()
        outer.setSpacing(16)
        outer.setContentsMargins(40, 30, 40, 30)

        # ---- Developer credit section ----
        credit_layout = QVBoxLayout()
        credit_layout.setSpacing(6)
        credit_layout.setAlignment(Qt.AlignCenter)

        # Developer picture - 180 px on the home page
        pic_lbl = _make_picture_label(180)
        credit_layout.addWidget(pic_lbl, alignment=Qt.AlignCenter)

        # Developer name
        name_lbl = QLabel("LOUAY CHERIF")
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setFocusPolicy(Qt.TabFocus)
        name_lbl.setAccessibleName("Developer name: Louay Cherif")
        name_lbl.setStyleSheet(
            "font-size: 26px; font-weight: bold; color: #f9d342;"
            "background: transparent; border: none; padding: 2px;"
        )
        credit_layout.addWidget(name_lbl)

        # Title
        title_lbl = QLabel("Program Developer and Owner")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setFocusPolicy(Qt.TabFocus)
        title_lbl.setAccessibleName("Program Developer and Owner")
        title_lbl.setStyleSheet(
            "font-size: 20px; color: #0fecb0;"
            "background: transparent; border: none; padding: 2px;"
        )
        credit_layout.addWidget(title_lbl)

        # Collaborator
        collab_lbl = QLabel("Assisted by: Aymen Ferchichi")
        collab_lbl.setAlignment(Qt.AlignCenter)
        collab_lbl.setFocusPolicy(Qt.TabFocus)
        collab_lbl.setAccessibleName("Assisted by Aymen Ferchichi")
        collab_lbl.setStyleSheet(
            "font-size: 18px; color: #aaaaaa;"
            "background: transparent; border: none; padding: 2px;"
        )
        credit_layout.addWidget(collab_lbl)

        outer.addLayout(credit_layout)

        # ---- Welcome / description ----
        welcome_text = (
            "Welcome to the Adapted Informatics Initiative Software!\n\n"
            "Developed and owned by Louay Cherif as part of his initiative "
            "TechBloom Academy - an open-source project designed to assist "
            "visually impaired people in mastering keyboard typing within an "
            "accessible environment built specifically for them.\n\n"
            "Please select your preferred language to continue:"
        )
        welcome_browser = AccessibleBrowser(
            text=welcome_text,
            accessible_text="Application welcome message. " + welcome_text,
        )
        welcome_browser.setMinimumHeight(180)
        outer.addWidget(welcome_browser)

        # ---- Language buttons ----
        btn_en = AccessiblePushButton("English")
        btn_fr = AccessiblePushButton("Français")
        btn_en.clicked.connect(lambda: self.select_language('en'))
        btn_fr.clicked.connect(lambda: self.select_language('fr'))
        outer.addWidget(btn_en)
        outer.addWidget(btn_fr)

        outer.addStretch()
        self.setLayout(outer)

    def select_language(self, lang):
        self.selected = lang
        self.accept()
