"""
FFmpeg configuration dialog.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import os
from settings import settings_manager


class FFmpegConfigDialog:
    """Dialog for configuring FFmpeg path."""
    
    def __init__(self, parent=None):
        """Initialize the FFmpeg configuration dialog.
        
        Args:
            parent: Parent window.
        """
        self.parent = parent
        self.result = None
        self.dialog = None
    
    def show_config_dialog(self) -> bool:
        """Show the FFmpeg configuration dialog.
        
        Returns:
            True if configuration was successful, False otherwise.
        """
        self.dialog = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        self.dialog.title("FFmpeg Configuration")
        self.dialog.geometry("500x300")
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        
        # Wait for dialog to close
        if self.parent:
            self.dialog.wait_window()
        else:
            self.dialog.mainloop()
        
        return self.result is not None
    
    def _create_widgets(self):
        """Create dialog widgets."""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="FFmpeg Configuration", 
                               font=('TkDefaultFont', 12, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Description
        desc_text = """FFmpeg is required for local Whisper transcription.

Current status: FFmpeg not found in system PATH.

Please either:
1. Install FFmpeg to your system PATH, or
2. Specify the path to your FFmpeg executable below.

Common FFmpeg locations on Windows:
• C:\\ffmpeg\\bin\\ffmpeg.exe
• C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe"""
        
        desc_label = ttk.Label(main_frame, text=desc_text, justify=tk.LEFT)
        desc_label.grid(row=1, column=0, columnspan=2, pady=(0, 15), sticky=tk.W)
        
        # Current saved path
        settings = settings_manager.load_all_settings()
        current_path = settings.get('ffmpeg_path', 'Not configured')
        
        ttk.Label(main_frame, text="Current FFmpeg path:").grid(row=2, column=0, sticky=tk.W)
        path_label = ttk.Label(main_frame, text=current_path, foreground='blue')
        path_label.grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(20, 0))
        
        ttk.Button(button_frame, text="Browse for FFmpeg...", 
                  command=self._browse_ffmpeg).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Test Current Path", 
                  command=self._test_current_path).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Skip for Now", 
                  command=self._skip).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Close", 
                  command=self._close).pack(side=tk.LEFT)
    
    def _browse_ffmpeg(self):
        """Browse for FFmpeg executable."""
        from transcriber.local_backend import FFmpegManager
        
        ffmpeg_path = FFmpegManager.prompt_for_ffmpeg_path()
        if ffmpeg_path:
            # Save the path
            settings = settings_manager.load_all_settings()
            settings['ffmpeg_path'] = ffmpeg_path
            settings_manager.save_all_settings(settings)
            
            messagebox.showinfo("Success", f"FFmpeg path saved: {ffmpeg_path}")
            self.result = ffmpeg_path
            self.dialog.destroy()
    
    def _test_current_path(self):
        """Test the current FFmpeg path."""
        settings = settings_manager.load_all_settings()
        ffmpeg_path = settings.get('ffmpeg_path')
        
        if not ffmpeg_path:
            messagebox.showwarning("No Path", "No FFmpeg path is currently configured.")
            return
        
        if not os.path.exists(ffmpeg_path):
            messagebox.showerror("Invalid Path", f"FFmpeg not found at: {ffmpeg_path}")
            return
        
        # Test the executable
        import subprocess
        try:
            result = subprocess.run([ffmpeg_path, '-version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                messagebox.showinfo("Success", "FFmpeg is working correctly!")
            else:
                messagebox.showerror("Error", "FFmpeg test failed.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to test FFmpeg: {e}")
    
    def _skip(self):
        """Skip FFmpeg configuration."""
        self.result = "skip"
        self.dialog.destroy()
    
    def _close(self):
        """Close dialog without changes."""
        self.dialog.destroy()


if __name__ == "__main__":
    # Test the dialog
    dialog = FFmpegConfigDialog()
    dialog.show_config_dialog() 