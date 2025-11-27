"""
PyQt6 custom widgets package.
"""
from ui_qt.widgets.buttons import (
    ModernButton,
    PrimaryButton,
    DangerButton,
    SuccessButton,
    IconButton,
)
from ui_qt.widgets.cards import (
    Card,
    ControlPanel,
    HeaderCard,
    StatCard,
)
from ui_qt.widgets.hotkey_display import HotkeyDisplay
from ui_qt.widgets.history_sidebar import (
    HistorySidebar,
    HistoryToggleButton,
    HistoryEdgeTab,
    HistoryItemWidget,
    RecordingItemWidget,
)
from ui_qt.widgets.collapsible_transcription import (
    CollapsibleTranscriptionCard,
    TranscriptionEdgeTab,
)

__all__ = [
    "ModernButton",
    "PrimaryButton",
    "DangerButton",
    "SuccessButton",
    "IconButton",
    "Card",
    "ControlPanel",
    "HeaderCard",
    "StatCard",
    "HotkeyDisplay",
    "HistorySidebar",
    "HistoryToggleButton",
    "HistoryEdgeTab",
    "HistoryItemWidget",
    "RecordingItemWidget",
    "CollapsibleTranscriptionCard",
    "TranscriptionEdgeTab",
]
