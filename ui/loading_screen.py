"""
Loading screen UI component for the Audio Recorder application.
Simple, fast static loading screen with no animations.
"""
import tkinter as tk
from tkinter import ttk
from config import config
import logging


class LoadingScreen:
    """Simple static loading screen for fast, reliable display."""
    
    def __init__(self):
        """Initialize the loading screen."""
        self.root = None
        self.status_label = None
        self._ui_created = False
        
        # Colors from config
        self._bg_color = config.WAVEFORM_BG_COLOR
        self._accent_color = config.WAVEFORM_ACCENT_COLOR
        self._text_secondary = "#b0b0b0"
    
    def _create_loading_screen(self):
        """Create and display a simple static loading screen."""
        try:
            self.root = tk.Tk()
            self.root.title("B.L.A.D.E.")
            self.root.geometry("400x240")
            self.root.resizable(False, False)
            self.root.attributes('-topmost', True)
            self.root.configure(bg=self._bg_color)
            
            # Center the loading screen
            self.root.eval('tk::PlaceWindow . center')
            
            # Create main frame
            main_frame = tk.Frame(self.root, bg=self._bg_color)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)
            
            # App title
            title_label = tk.Label(
                main_frame,
                text="B.L.A.D.E.",
                font=("Segoe UI", 24, "bold"),
                bg=self._bg_color,
                fg=self._accent_color,
            )
            title_label.pack(pady=(0, 5))

            # Subtitle
            subtitle_label = tk.Label(
                main_frame,
                text="Brister's Linguistic Audio Dictation Engine",
                font=("Segoe UI", 9),
                bg=self._bg_color,
                fg=self._text_secondary,
            )
            subtitle_label.pack(pady=(0, 25))
            
            # Simple loading indicator using text
            loading_frame = tk.Frame(main_frame, bg=self._bg_color)
            loading_frame.pack(pady=(0, 20))
            
            # Static "loading" indicator
            loading_indicator = tk.Label(
                loading_frame,
                text="●  ●  ●",
                font=("Segoe UI", 14),
                bg=self._bg_color,
                fg=self._accent_color,
            )
            loading_indicator.pack()
            
            # Loading status label
            self.status_label = tk.Label(
                main_frame,
                text="Initializing application...",
                font=("Segoe UI", 10),
                bg=self._bg_color,
                fg=self._text_secondary,
            )
            self.status_label.pack(pady=(15, 0))
            
            # Additional info
            info_label = tk.Label(
                main_frame,
                text="Please wait while components load",
                font=("Segoe UI", 8),
                bg=self._bg_color,
                fg=self._text_secondary,
            )
            info_label.pack(pady=(5, 0))
            
            # Force window to appear immediately
            self.root.update_idletasks()
            self.root.deiconify()
            self.root.lift()
            self.root.update()
            
            logging.info("Static loading screen created successfully")
            
        except Exception as e:
            logging.error(f"Failed to create loading screen: {e}")
            self.root = None
    
    def update_status(self, status_text: str):
        """Update the loading screen status text.
        
        Args:
            status_text: New status text to display.
        """
        try:
            if self.status_label and self.root:
                self.status_label.config(text=status_text)
                self.root.update()
        except Exception as e:
            logging.debug(f"Status update failed: {e}")
    
    def show(self):
        """Show the loading screen."""
        try:
            if not self._ui_created:
                self._create_loading_screen()
                self._ui_created = True
            
            if self.root:
                self.root.deiconify()
                self.root.lift()
                self.root.attributes('-topmost', True)
                self.root.update()
                    
        except Exception as e:
            logging.error(f"Show loading screen failed: {e}")
    
    def hide(self):
        """Hide the loading screen."""
        try:
            if self.root:
                self.root.withdraw()
        except Exception as e:
            logging.debug(f"Hide loading screen failed: {e}")
    
    def destroy(self):
        """Destroy the loading screen."""
        try:
            if self.root:
                self.root.destroy()
                self.root = None
                self.status_label = None
                
        except Exception as e:
            logging.debug(f"Loading screen cleanup failed: {e}")
    
    def is_visible(self) -> bool:
        """Check if the loading screen is visible.
        
        Returns:
            True if visible, False otherwise.
        """
        try:
            return self.root is not None and self._ui_created and self.root.winfo_viewable()
        except:
            return False