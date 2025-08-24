"""
Loading screen UI component for the Audio Recorder application.
Features a simple, reliable animation using built-in tkinter components.
"""
import tkinter as tk
from tkinter import ttk
from config import config
import logging
import time


class LoadingScreen:
    """Manages the loading screen display during application startup with reliable animation."""
    
    def __init__(self):
        """Initialize the loading screen."""
        self.root = None
        self.status_label = None
        self.progress_bar = None
        self.spinner_label = None
        self._spinner_job = None
        self._spinner_chars = ["|", "/", "-", "\\"]
        self._spinner_index = 0
        self._ui_created = False
        
        # Colors from config
        self._bg_color = config.WAVEFORM_BG_COLOR
        self._accent_color = config.WAVEFORM_ACCENT_COLOR
        self._text_primary = "#e6e6e6"
        self._text_secondary = "#b0b0b0"
    
    def _create_loading_screen(self):
        """Create and display the loading screen with reliable animation."""
        try:
            self.root = tk.Tk()
            self.root.title("Audio Recorder")
            self.root.geometry("350x200")
            self.root.resizable(False, False)
            self.root.attributes('-topmost', True)
            self.root.configure(bg=self._bg_color)
            
            # Center the loading screen
            self.root.eval('tk::PlaceWindow . center')
            
            # Force window to appear
            self.root.update_idletasks()
            self.root.deiconify()
            self.root.lift()
            
            # Create main frame
            main_frame = tk.Frame(self.root, bg=self._bg_color)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
            
            # App title
            title_label = tk.Label(
                main_frame,
                text="Audio Recorder",
                font=("Segoe UI", 18, "bold"),
                bg=self._bg_color,
                fg=self._accent_color,
            )
            title_label.pack(pady=(0, 25))
            
            # Spinner and progress container
            progress_frame = tk.Frame(main_frame, bg=self._bg_color)
            progress_frame.pack(fill=tk.X, pady=(0, 20))
            
            # Text spinner
            self.spinner_label = tk.Label(
                progress_frame,
                text="|",
                font=("Consolas", 16, "bold"),
                bg=self._bg_color,
                fg=self._accent_color,
                width=2
            )
            self.spinner_label.pack(side=tk.LEFT, padx=(0, 10))
            
            # Progress bar - guaranteed to animate
            self.progress_bar = ttk.Progressbar(
                progress_frame,
                mode='indeterminate',
                length=250,
                style='Custom.Horizontal.TProgressbar'
            )
            self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Loading status label
            self.status_label = tk.Label(
                main_frame,
                text="Initializing application...",
                font=("Segoe UI", 11),
                bg=self._bg_color,
                fg=self._text_secondary,
            )
            self.status_label.pack(pady=(15, 0))
            
            # Additional info
            info_label = tk.Label(
                main_frame,
                text="Please wait while components load...",
                font=("Segoe UI", 9),
                bg=self._bg_color,
                fg=self._text_secondary,
            )
            info_label.pack(pady=(5, 0))
            
            # Style the progress bar
            self._setup_progress_bar_style()
            
            # Final update and start animations
            self.root.update()
            self._start_animations()
            
            logging.info("Loading screen created successfully with animation")
            
        except Exception as e:
            logging.error(f"Failed to create loading screen: {e}")
            # Create fallback minimal window
            self._create_fallback_loading_screen()
    
    def _setup_progress_bar_style(self):
        """Setup custom style for the progress bar."""
        try:
            style = ttk.Style()
            
            # Create custom progress bar style
            style.theme_use('clam')  # Use clam theme as base
            
            # Configure the custom style with accent colors
            style.configure(
                'Custom.Horizontal.TProgressbar',
                troughcolor=self._bg_color,
                background=self._accent_color,
                lightcolor=self._accent_color,
                darkcolor=self._accent_color,
                borderwidth=1,
                focuscolor='none'
            )
            
        except Exception as e:
            logging.debug(f"Progress bar styling failed, using default: {e}")
    
    def _create_fallback_loading_screen(self):
        """Create a simple fallback loading screen if main creation fails."""
        try:
            self.root = tk.Tk()
            self.root.title("Audio Recorder")
            self.root.geometry("300x150")
            self.root.resizable(False, False)
            self.root.configure(bg='white')
            
            # Simple centered text
            main_frame = tk.Frame(self.root, bg='white')
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            title = tk.Label(main_frame, text="Audio Recorder", font=("Arial", 16, "bold"), bg='white')
            title.pack(pady=(0, 20))
            
            self.status_label = tk.Label(main_frame, text="Loading...", font=("Arial", 10), bg='white')
            self.status_label.pack()
            
            # Basic progress bar
            self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate', length=200)
            self.progress_bar.pack(pady=15)
            
            self.root.update()
            
            # Start only the progress bar
            if self.progress_bar:
                self.progress_bar.start(10)
            
            logging.info("Fallback loading screen created")
            
        except Exception as e:
            logging.error(f"Even fallback loading screen failed: {e}")
            self.root = None
    
    def _start_animations(self):
        """Start both progress bar and text spinner animations."""
        try:
            # Start progress bar animation - guaranteed to work
            if self.progress_bar:
                self.progress_bar.start(8)  # Moderate speed
            
            # Start text spinner
            self._start_text_spinner()
            
        except Exception as e:
            logging.debug(f"Animation start failed: {e}")
    
    def _start_text_spinner(self):
        """Start the simple text spinner animation."""
        try:
            if self.spinner_label and self.root:
                self._update_spinner()
        except Exception as e:
            logging.debug(f"Text spinner failed: {e}")
    
    def _update_spinner(self):
        """Update the text spinner character."""
        try:
            if not self.spinner_label or not self.root:
                self._spinner_job = None
                return
            
            # Update spinner character
            self.spinner_label.config(text=self._spinner_chars[self._spinner_index])
            self._spinner_index = (self._spinner_index + 1) % len(self._spinner_chars)
            
            # Schedule next update (200ms for smooth but not frantic spinning)
            self._spinner_job = self.root.after(200, self._update_spinner)
            
        except Exception as e:
            logging.debug(f"Spinner update failed: {e}")
            self._spinner_job = None
    
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
                
                # Ensure animations are running
                if self.progress_bar and not self.progress_bar.instate(['active']):
                    self.progress_bar.start(8)
                
                if not self._spinner_job:
                    self._start_text_spinner()
                    
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
        """Destroy the loading screen and clean up animations."""
        try:
            # Stop animations
            if self._spinner_job and self.root:
                try:
                    self.root.after_cancel(self._spinner_job)
                except:
                    pass
            self._spinner_job = None
            
            if self.progress_bar:
                try:
                    self.progress_bar.stop()
                except:
                    pass
            
            # Destroy window
            if self.root:
                self.root.destroy()
                self.root = None
                self.status_label = None
                self.progress_bar = None
                self.spinner_label = None
                
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