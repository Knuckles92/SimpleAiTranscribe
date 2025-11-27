"""
PyQt6 UI package for OpenWhisper.
Modern, professional interface with clean design.
"""
from ui_qt.app import QtApplication
from ui_qt.main_window_qt import ModernMainWindow
from ui_qt.loading_screen_qt import ModernLoadingScreen
from ui_qt.overlay_qt import ModernWaveformOverlay

__all__ = [
    "QtApplication",
    "ModernMainWindow",
    "ModernLoadingScreen",
    "ModernWaveformOverlay",
]
