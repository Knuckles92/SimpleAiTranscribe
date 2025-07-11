"""
Loading screen UI component for the Audio Recorder application.
"""
import tkinter as tk
from tkinter import ttk
from config import config


class LoadingScreen:
    """Manages the loading screen display during application startup."""
    
    def __init__(self):
        """Initialize the loading screen."""
        self.root = None
        self.status_label = None
        self.progress_bar = None
        self._create_loading_screen()
    
    def _create_loading_screen(self):
        """Create and display the loading screen."""
        self.root = tk.Tk()
        self.root.title("Audio Recorder")
        self.root.geometry(config.LOADING_WINDOW_SIZE)
        self.root.resizable(False, False)
        
        # Center the loading screen
        self.root.eval('tk::PlaceWindow . center')
        
        # Create main frame
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # App title
        title_label = tk.Label(main_frame, text="Audio Recorder", 
                              font=('TkDefaultFont', 16, 'bold'), 
                              bg='#f0f0f0', fg='#333333')
        title_label.pack(pady=(0, 20))
        
        # Loading status label
        self.status_label = tk.Label(main_frame, text="Initializing application...", 
                                   font=('TkDefaultFont', 10), 
                                   bg='#f0f0f0', fg='#666666')
        self.status_label.pack(pady=(0, 10))
        
        # Progress bar (indeterminate)
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate', length=200)
        self.progress_bar.pack(pady=(0, 10))
        self.progress_bar.start(config.PROGRESS_BAR_INTERVAL_MS)
        
        # Version or additional info
        info_label = tk.Label(main_frame, text="Please wait while components load...", 
                             font=('TkDefaultFont', 8), 
                             bg='#f0f0f0', fg='#888888')
        info_label.pack()
        
        self.root.update()
    
    def update_status(self, status_text: str):
        """Update the loading screen status text.
        
        Args:
            status_text: New status text to display.
        """
        if self.status_label:
            self.status_label.config(text=status_text)
            self.root.update()
    
    def show(self):
        """Show the loading screen."""
        if self.root:
            self.root.deiconify()
            self.root.update()
    
    def hide(self):
        """Hide the loading screen."""
        if self.root:
            self.root.withdraw()
    
    def destroy(self):
        """Destroy the loading screen."""
        if self.root:
            if self.progress_bar:
                self.progress_bar.stop()
            self.root.destroy()
            self.root = None
            self.status_label = None
            self.progress_bar = None
    
    def is_visible(self) -> bool:
        """Check if the loading screen is visible.
        
        Returns:
            True if visible, False otherwise.
        """
        return self.root is not None and self.root.winfo_viewable() 