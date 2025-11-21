"""
Modern button components for PyQt6 UI.
"""
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QFont


class ModernButton(QPushButton):
    """Modern button with smooth hover and click animations."""

    clicked_smooth = pyqtSignal()

    def __init__(self, text: str = "", parent=None):
        """Initialize modern button."""
        super().__init__(text, parent)
        self.setMinimumHeight(44) # Increased height
        self.setFont(QFont("Segoe UI", 12)) # Increased font size
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Remove default focus outline


class PrimaryButton(ModernButton):
    """Primary action button with gradient."""

    def __init__(self, text: str = "", parent=None):
        """Initialize primary button."""
        super().__init__(text, parent)
        self.setObjectName("primaryButton")
        self.setMinimumHeight(48)
        self.setMinimumWidth(140)


class DangerButton(ModernButton):
    """Danger button for destructive actions."""

    def __init__(self, text: str = "", parent=None):
        """Initialize danger button."""
        super().__init__(text, parent)
        self.setObjectName("dangerButton")
        self.setMinimumHeight(48)
        self.setMinimumWidth(140)


class SuccessButton(ModernButton):
    """Success button for positive actions."""

    def __init__(self, text: str = "", parent=None):
        """Initialize success button."""
        super().__init__(text, parent)
        self.setObjectName("successButton")
        self.setMinimumHeight(48)
        self.setMinimumWidth(140)


class IconButton(ModernButton):
    """Small button, typically used for icons."""

    def __init__(self, icon=None, parent=None):
        """Initialize icon button."""
        super().__init__(parent=parent)
        if icon:
            self.setIcon(icon)
        self.setMinimumSize(44, 44)
        self.setMaximumSize(44, 44)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
