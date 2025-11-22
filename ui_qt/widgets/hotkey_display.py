"""
Modern hotkey display widget with keyboard key styling.
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class HotkeyKey(QLabel):
    """A single hotkey key styled like a keyboard key."""
    
    def __init__(self, text: str):
        super().__init__(text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(28)
        self.setMinimumWidth(32)
        
        # Modern keyboard key styling
        self.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a3a3c, stop:1 #2c2c2e);
                color: #f5f5f7;
                border: 1px solid #48484a;
                border-radius: 6px;
                padding: 4px 10px;
                font-family: "Segoe UI", "SF Pro Display", sans-serif;
                font-size: 13px;
                font-weight: 600;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            }
        """)


class HotkeyLabel(QLabel):
    """Label describing what the hotkey does."""
    
    def __init__(self, text: str):
        super().__init__(text)
        self.setStyleSheet("""
            QLabel {
                color: #98989d;
                font-size: 11px;
                font-weight: 500;
                padding: 0 4px;
                background: transparent;
            }
        """)


class HotkeyDisplay(QWidget):
    """Modern hotkey display widget with keyboard key styling."""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI with styled hotkey buttons."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Hotkeys label (subtle)
        hotkeys_text = QLabel("Hotkeys:")
        hotkeys_text.setStyleSheet("""
            QLabel {
                color: #636366;
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                padding-right: 4px;
                background: transparent;
            }
        """)
        layout.addWidget(hotkeys_text)
        
        # Record hotkey
        record_key = HotkeyKey("*")
        layout.addWidget(record_key)
        
        record_label = HotkeyLabel("rec")
        layout.addWidget(record_label)
        
        # Spacer
        spacer1 = QLabel("•")
        spacer1.setStyleSheet("color: #48484a; font-size: 10px; padding: 0 2px; background: transparent;")
        layout.addWidget(spacer1)
        
        # Cancel hotkey
        cancel_key = HotkeyKey("-")
        layout.addWidget(cancel_key)
        
        cancel_label = HotkeyLabel("cancel")
        layout.addWidget(cancel_label)
        
        # Spacer
        spacer2 = QLabel("•")
        spacer2.setStyleSheet("color: #48484a; font-size: 10px; padding: 0 2px; background: transparent;")
        layout.addWidget(spacer2)
        
        # Enable/Disable hotkey
        enable_key = HotkeyKey("Ctrl+Alt+*")
        layout.addWidget(enable_key)
        
        enable_label = HotkeyLabel("toggle")
        layout.addWidget(enable_label)
        
        # Set transparent background for the widget itself
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("QWidget { background: transparent; }")
    
    def update_hotkeys(self, record_key: str, cancel_key: str, enable_disable_key: str = "Ctrl+Alt+*"):
        """
        Update the hotkey display with new keys.
        
        Args:
            record_key: The key for recording
            cancel_key: The key for canceling
            enable_disable_key: The key for enabling/disabling STT
        """
        # Get the key widgets (indices 1, 4, and 7 in the layout)
        layout = self.layout()
        if layout.count() >= 8:
            record_widget = layout.itemAt(1).widget()
            cancel_widget = layout.itemAt(4).widget()
            enable_widget = layout.itemAt(7).widget()
            
            if isinstance(record_widget, HotkeyKey):
                record_widget.setText(record_key)
            if isinstance(cancel_widget, HotkeyKey):
                cancel_widget.setText(cancel_key)
            if isinstance(enable_widget, HotkeyKey):
                # Format the enable/disable key nicely
                formatted_key = enable_disable_key.replace('ctrl', 'Ctrl').replace('alt', 'Alt').replace('shift', 'Shift')
                enable_widget.setText(formatted_key)
