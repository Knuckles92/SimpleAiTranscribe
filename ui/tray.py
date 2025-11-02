"""
System tray management for the Audio Recorder application.
"""
import pystray
import threading
import logging
from PIL import Image
from typing import Callable, Optional


class TrayManager:
    """Manages the system tray icon and menu."""
    
    def __init__(self):
        """Initialize the tray manager."""
        self.tray_icon: Optional[pystray.Icon] = None
        self.tray_thread: Optional[threading.Thread] = None
        self.on_show_callback: Optional[Callable] = None
        self.on_quit_callback: Optional[Callable] = None
        self._setup_tray_icon()
    
    def _setup_tray_icon(self):
        """Setup the system tray icon and menu."""
        # Load icon from ui/icon.png
        try:
            import os
            icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
            icon_data = Image.open(icon_path)
        except Exception as e:
            logging.error(f"Failed to load icon from ui/icon.png: {e}")
            # Fallback to simple icon
            icon_data = Image.new('RGB', (64, 64), color='red')
        
        menu = (
            pystray.MenuItem('Show', self._on_show_clicked),
            pystray.MenuItem('Exit', self._on_quit_clicked)
        )
        
        self.tray_icon = pystray.Icon("blade", icon_data, "B.L.A.D.E.", menu)
    
    def _on_show_clicked(self, *_):
        """Handle show menu item click."""
        if self.on_show_callback:
            self.on_show_callback()
    
    def _on_quit_clicked(self, *_):
        """Handle quit menu item click."""
        if self.on_quit_callback:
            self.on_quit_callback()
    
    def show_tray(self):
        """Show the system tray icon."""
        if self.tray_icon and not self.tray_icon.visible:
            self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            self.tray_thread.start()
            logging.info("System tray icon shown")
    
    def hide_tray(self):
        """Hide the system tray icon."""
        if self.tray_icon and self.tray_icon.visible:
            self.tray_icon.stop()
            logging.info("System tray icon hidden")
    
    def set_callbacks(self, on_show: Callable = None, on_quit: Callable = None):
        """Set callback functions for tray menu actions.
        
        Args:
            on_show: Called when show menu item is clicked.
            on_quit: Called when quit menu item is clicked.
        """
        self.on_show_callback = on_show
        self.on_quit_callback = on_quit
    
    def update_icon(self, icon_path: str = None, icon_image: Image.Image = None):
        """Update the tray icon image.
        
        Args:
            icon_path: Path to icon file.
            icon_image: PIL Image object.
        """
        if icon_path:
            try:
                icon_image = Image.open(icon_path)
            except Exception as e:
                logging.error(f"Failed to load icon from {icon_path}: {e}")
                return
        
        if icon_image and self.tray_icon:
            self.tray_icon.icon = icon_image
            logging.info("Tray icon updated")
    
    def update_tooltip(self, tooltip: str):
        """Update the tray icon tooltip.
        
        Args:
            tooltip: New tooltip text.
        """
        if self.tray_icon:
            self.tray_icon.title = tooltip
    
    def cleanup(self):
        """Clean up tray resources."""
        try:
            if self.tray_icon and self.tray_icon.visible:
                self.tray_icon.stop()
            
            if self.tray_thread and self.tray_thread.is_alive():
                self.tray_thread.join(timeout=1.0)
                
            logging.info("Tray manager cleaned up")
            
        except Exception as e:
            logging.error(f"Error during tray cleanup: {e}")
    
    @property
    def is_visible(self) -> bool:
        """Check if the tray icon is visible.
        
        Returns:
            True if visible, False otherwise.
        """
        return self.tray_icon is not None and self.tray_icon.visible 