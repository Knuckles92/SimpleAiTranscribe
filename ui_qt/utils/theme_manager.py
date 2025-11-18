"""
Theme management for PyQt6 UI.
Handles stylesheet loading and theme switching.
"""
from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal


class ThemeManager(QObject):
    """Manages application theme and stylesheet."""

    theme_changed = pyqtSignal(str)  # Emitted when theme changes

    def __init__(self):
        """Initialize theme manager."""
        super().__init__()
        self.current_theme = "dark"
        self._load_stylesheet()

    def _load_stylesheet(self) -> Optional[str]:
        """Load and cache the stylesheet."""
        try:
            theme_path = Path(__file__).parent.parent / "styles" / "theme.qss"
            if theme_path.exists():
                with open(theme_path, 'r') as f:
                    self._stylesheet = f.read()
                    return self._stylesheet
        except Exception as e:
            print(f"Error loading stylesheet: {e}")

        return None

    @property
    def stylesheet(self) -> str:
        """Get the current stylesheet."""
        return getattr(self, '_stylesheet', '')

    def set_theme(self, theme_name: str):
        """Set the application theme."""
        self.current_theme = theme_name
        self.theme_changed.emit(theme_name)

    def get_color(self, color_name: str) -> str:
        """Get a color value from the theme."""
        colors = {
            'primary': '#6366f1',
            'primary_hover': '#818cf8',
            'secondary': '#8b5cf6',
            'danger': '#ef4444',
            'success': '#10b981',
            'accent': '#00d4ff',
            'background': '#1e1e2e',
            'surface': '#2d2d44',
            'border': '#404060',
            'text': '#e0e0ff',
            'text_secondary': '#a0a0c0',
        }
        return colors.get(color_name, '#ffffff')
