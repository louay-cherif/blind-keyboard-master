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

from PyQt5.QtWidgets import QPushButton
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
