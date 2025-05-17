import tkinter as tk
import threading
import pystray
from PIL import Image
import logging
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

console = Console()

class StatusOverlay:
    def __init__(self):
        """Initialize the status overlay window"""
        # Create status overlay window
        self.overlay = tk.Tk()
        self.overlay.title("")
        self.overlay.geometry("200x30")
        self.overlay.attributes('-topmost', True)
        self.overlay.overrideredirect(True)  # Remove window decorations
        self.overlay.withdraw()  # Hide initially
        
        # Create overlay label
        self.overlay_label = tk.Label(self.overlay, text="", bg='black', fg='white', pady=5)
        self.overlay_label.pack(fill=tk.BOTH, expand=True)
        
    def show_status(self, message, hide_after_ms=None):
        """Show status overlay with given message"""
        if message:
            # Position overlay near mouse cursor
            x = self.overlay.winfo_pointerx() + 10
            y = self.overlay.winfo_pointery() + 10
            self.overlay.geometry(f"+{x}+{y}")
            
            self.overlay_label.config(text=message)
            self.overlay.deiconify()
            self.overlay.update()
            
            # Also print to console for CLI mode
            console.print(Text(f"▶ {message}", style="bold blue"))
            
            # Auto-hide after specified milliseconds if requested
            if hide_after_ms:
                self.overlay.after(hide_after_ms, self.hide)
        else:
            self.hide()
            
    def hide(self):
        """Hide the overlay"""
        self.overlay.withdraw()
        
    def update_position(self):
        """Update the overlay position to follow mouse cursor"""
        if self.overlay.state() == 'normal':  # If overlay is visible
            x = self.overlay.winfo_pointerx() + 10
            y = self.overlay.winfo_pointery() + 10
            self.overlay.geometry(f"+{x}+{y}")
        self.overlay.after(100, self.update_position)  # Schedule next update
        
    def start(self):
        """Start the overlay position update loop and mainloop"""
        # Start the position update loop
        self.update_position()
        
    def destroy(self):
        """Destroy the overlay window"""
        try:
            self.overlay.destroy()
        except Exception as e:
            logging.error(f"Error destroying overlay: {e}")
            
    def run_mainloop(self):
        """Run the tkinter mainloop"""
        self.overlay.mainloop()


class SystemTray:
    def __init__(self, show_callback, quit_callback):
        """Initialize the system tray icon"""
        self.show_callback = show_callback
        self.quit_callback = quit_callback
        self.tray_icon = None
        self.tray_icon_thread = None
        
    def setup(self):
        """Set up the system tray icon"""
        icon_data = Image.new('RGB', (64, 64), color='red')
        menu = (
            pystray.MenuItem('Show', self.show_callback),
            pystray.MenuItem('Exit', self.quit_callback)
        )
        self.tray_icon = pystray.Icon("audio_recorder", icon_data, "Audio Recorder", menu)
        self.tray_icon_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self.tray_icon_thread.start()
        
    def stop(self):
        """Stop the system tray icon"""
        if self.tray_icon and self.tray_icon.visible:
            self.tray_icon.stop()


def print_welcome_message(model_choice, use_api):
    """Print welcome message and application info"""
    welcome_panel = Panel(
        Text(f"Audio Recorder", style="bold white on blue", justify="center"),
        subtitle=Text(f"Version 1.0", style="italic", justify="center"),
        border_style="blue"
    )
    console.print(welcome_panel)

    table = Table(show_header=True, header_style="bold cyan", border_style="blue")
    table.add_column("Setting", style="dim")
    table.add_column("Value", style="green")
    
    table.add_row("Model", model_choice)
    table.add_row("API Mode", "✅ Enabled" if use_api else "❌ Disabled")
    
    console.print(table)
    
    shortcuts = Table(show_header=True, header_style="bold magenta", title="Keyboard Shortcuts", border_style="magenta")
    shortcuts.add_column("Key", style="cyan")
    shortcuts.add_column("Action", style="yellow")
    
    shortcuts.add_row("*", "Start/Stop Recording")
    shortcuts.add_row("-", "Cancel/Stop Any Process")
    shortcuts.add_row("Ctrl+Alt+*", "Enable/Disable Program")
    
    console.print(shortcuts)
    console.print("", Text("▶ Ready", style="bold green"), "\n")
