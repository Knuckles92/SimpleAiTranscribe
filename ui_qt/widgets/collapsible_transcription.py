"""
Collapsible transcription widget with animated expand/collapse.
Provides a streamlined UI by allowing the transcription area to be hidden.
"""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont


class TranscriptionEdgeTab(QPushButton):
    """Horizontal edge tab button to toggle transcription area - always visible."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("transcriptionEdgeTab")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(24)
        self.setMinimumWidth(80)
        self._is_expanded = True  # Start expanded
        self._update_icon()
        self._apply_style()
    
    def set_expanded(self, expanded: bool):
        """Update the tab state."""
        self._is_expanded = expanded
        self._update_icon()
    
    def _update_icon(self):
        """Update the icon based on expanded state."""
        # Use arrow characters to indicate direction (vertical collapse)
        if self._is_expanded:
            self.setText("▲  Transcription  ▲")  # Arrows pointing up (to collapse)
            self.setToolTip("Collapse Transcription")
        else:
            self.setText("▼  Transcription  ▼")  # Arrows pointing down (to expand)
            self.setToolTip("Expand Transcription")
    
    def _apply_style(self):
        """Apply custom styling."""
        self.setStyleSheet("""
            QPushButton#transcriptionEdgeTab {
                background-color: #2c2c2e;
                color: #8e8e93;
                border: 1px solid #3a3a3c;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
                font-size: 12px;
                font-weight: 600;
                padding: 4px 16px;
                letter-spacing: 0.5px;
            }
            QPushButton#transcriptionEdgeTab:hover {
                background-color: #3a3a3c;
                color: #f5f5f7;
            }
            QPushButton#transcriptionEdgeTab:pressed {
                background-color: #1c1c1e;
            }
        """)


class CollapsibleTranscriptionCard(QWidget):
    """Collapsible card containing the transcription text area."""
    
    # Signals
    toggled = pyqtSignal(bool)  # Emits True when expanded, False when collapsed
    
    COLLAPSED_HEIGHT = 0
    EXPANDED_HEIGHT = 280  # Default expanded height (including edge tab)
    EDGE_TAB_HEIGHT = 24
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self._is_expanded = True
        self._expanded_content_height = 250  # The text area height when expanded
        
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        """Setup the widget UI."""
        self.setObjectName("collapsibleTranscription")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Edge tab (always visible toggle button)
        self.edge_tab = TranscriptionEdgeTab()
        self.edge_tab.clicked.connect(self.toggle)
        main_layout.addWidget(self.edge_tab, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        # Content container (will be animated)
        self.content_widget = QWidget()
        self.content_widget.setObjectName("transcriptionContent")
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Card wrapper for styling
        self.card_frame = QFrame()
        self.card_frame.setObjectName("transcriptionCard")
        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setContentsMargins(16, 12, 16, 16)
        card_layout.setSpacing(8)
        
        # Transcription text area
        self.transcription_text = QTextEdit()
        self.transcription_text.setReadOnly(True)
        self.transcription_text.setMinimumHeight(self._expanded_content_height)
        self.transcription_text.setFont(QFont("Segoe UI", 13))
        self.transcription_text.setPlaceholderText(
            "Transcription will appear here...\n"
            "Start recording to begin."
        )
        self.transcription_text.setObjectName("transcriptionTextEdit")
        
        card_layout.addWidget(self.transcription_text)
        content_layout.addWidget(self.card_frame)
        
        main_layout.addWidget(self.content_widget)
        
        # Animation for expand/collapse
        self.animation = QPropertyAnimation(self.content_widget, b"maximumHeight")
        self.animation.setDuration(250)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Set initial state
        self.content_widget.setMaximumHeight(16777215)  # Qt's QWIDGETSIZE_MAX
    
    def _apply_style(self):
        """Apply custom styling."""
        self.setStyleSheet("""
            QWidget#collapsibleTranscription {
                background-color: transparent;
            }
            QWidget#transcriptionContent {
                background-color: transparent;
            }
            QFrame#transcriptionCard {
                background-color: rgba(45, 45, 68, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-top: none;
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }
            QTextEdit#transcriptionTextEdit {
                background-color: rgba(28, 28, 30, 0.6);
                color: #e5e5e7;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 10px;
                padding: 12px;
                selection-background-color: rgba(99, 102, 241, 0.4);
            }
            QTextEdit#transcriptionTextEdit:focus {
                border: 1px solid rgba(99, 102, 241, 0.5);
            }
        """)
    
    def expand(self):
        """Expand the transcription area."""
        if self._is_expanded:
            return
        
        self._is_expanded = True
        self.edge_tab.set_expanded(True)
        
        # Calculate the actual expanded height
        expanded_height = self._get_content_height()
        
        self.animation.stop()
        self.animation.setStartValue(0)
        self.animation.setEndValue(expanded_height)
        self.animation.start()
        
        self.toggled.emit(True)
        self.logger.debug("Transcription expanded")
    
    def collapse(self):
        """Collapse the transcription area."""
        if not self._is_expanded:
            return
        
        self._is_expanded = False
        self.edge_tab.set_expanded(False)
        
        self.animation.stop()
        self.animation.setStartValue(self.content_widget.height())
        self.animation.setEndValue(0)
        self.animation.start()
        
        self.toggled.emit(False)
        self.logger.debug("Transcription collapsed")
    
    def toggle(self):
        """Toggle transcription visibility."""
        if self._is_expanded:
            self.collapse()
        else:
            self.expand()
    
    def _get_content_height(self) -> int:
        """Get the height of the content when expanded."""
        # Return a reasonable default height for the content
        return self._expanded_content_height + 40  # Add padding/margins
    
    @property
    def is_expanded(self) -> bool:
        """Return whether transcription is expanded."""
        return self._is_expanded
    
    # Text manipulation methods (delegate to internal QTextEdit)
    def set_text(self, text: str):
        """Set the transcription text."""
        self.transcription_text.setText(text)
    
    def append_text(self, text: str):
        """Append text to the transcription."""
        cursor = self.transcription_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.transcription_text.setTextCursor(cursor)
        self.transcription_text.insertPlainText(text)
    
    def clear(self):
        """Clear the transcription text."""
        self.transcription_text.clear()
    
    def get_text(self) -> str:
        """Get the current transcription text."""
        return self.transcription_text.toPlainText()
    
    def set_placeholder_text(self, text: str):
        """Set placeholder text."""
        self.transcription_text.setPlaceholderText(text)

