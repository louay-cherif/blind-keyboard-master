# Blind Keyboard Master - Accessible Widgets
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

from PyQt5.QtWidgets import QPushButton, QLabel, QTextBrowser
from PyQt5.QtCore import Qt


class AccessiblePushButton(QPushButton):
    """
    Custom push button that responds to both Space and Enter/Return keys when focused.
    Emits clicked signal on both Space and Return key presses for full keyboard accessibility.
    """

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            self.clicked.emit()
            return
        super().keyPressEvent(event)


class AccessibleLabel(QLabel):
    """
    A keyboard-focusable QLabel with separate visual and accessible text.

    visual_text      -  compact text shown on screen  (e.g. "50/1500").
    accessible_text  -  verbose text read by screen reader on focus
                      (e.g. "50 out of 1500 XP balance").

    Tab-focusable so blind users can navigate with the keyboard.
    """

    def __init__(self, visual_text="", accessible_text="", parent=None):
        super().__init__(visual_text, parent)
        self.setFocusPolicy(Qt.TabFocus)
        self.setAccessibleName(accessible_text if accessible_text else visual_text)
        self.setStyleSheet(
            "padding: 12px;"
            "background-color: #1a1a2e;"
            "color: #f9d342;"
            "border: 2px solid #f9d342;"
            "border-radius: 10px;"
            "font-size: 22px;"
        )
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)

    def update_text(self, visual_text, accessible_text=None):
        """Update both displayed and screen-reader text in one call."""
        self.setText(visual_text)
        self.setAccessibleName(
            accessible_text if accessible_text is not None else visual_text
        )


class AccessibleBrowser(QTextBrowser):
    """
    Read-only word-wrapped text area for long multiline content.
    Replaces readonly QLineEdit for paragraphs and descriptions.
    Tab-focusable; screen reader announces full content on focus.
    """

    def __init__(self, text="", accessible_text="", parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setOpenExternalLinks(False)
        self.setPlainText(text)
        self.setFocusPolicy(Qt.TabFocus)
        self.setAccessibleName(accessible_text if accessible_text else text)
        self.setStyleSheet(
            "padding: 14px;"
            "background-color: #1a1a2e;"
            "color: #f9d342;"
            "border: 2px solid #f9d342;"
            "border-radius: 10px;"
            "font-size: 20px;"
        )

    def update_text(self, text, accessible_text=None):
        """Update both displayed and screen-reader text in one call."""
        self.setPlainText(text)
        self.setAccessibleName(accessible_text if accessible_text is not None else text)

