"""
Hotkey configuration dialog for the Audio Recorder application.
"""
import tkinter as tk
from tkinter import messagebox
from typing import Dict, Optional
from config import config
from settings import settings_manager


class HotkeyDialog:
    """Dialog for configuring application hotkeys."""
    
    def __init__(self, parent, hotkey_manager):
        """Initialize the hotkey dialog.
        
        Args:
            parent: Parent window.
            hotkey_manager: HotkeyManager instance.
        """
        self.parent = parent
        self.hotkey_manager = hotkey_manager
        self.dialog: Optional[tk.Toplevel] = None
        self.hotkey_vars: Dict[str, tk.StringVar] = {}
        
        # Hotkey field configurations
        self.hotkey_fields = [
            ("record_toggle", "Record Toggle:", "Toggle recording on/off"),
            ("cancel", "Cancel:", "Cancel recording or transcription"),
            ("enable_disable", "Enable/Disable:", "Enable/disable the entire program")
        ]
    
    def show(self):
        """Show the hotkey configuration dialog."""
        self._create_dialog()
        self._setup_dialog_content()
        self.dialog.grab_set()
        self.dialog.transient(self.parent)
        self.dialog.focus_set()
    
    def _create_dialog(self):
        """Create the dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Configure Hotkeys")
        self.dialog.geometry(config.HOTKEY_DIALOG_SIZE)
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self._center_dialog()
    
    def _center_dialog(self):
        """Center the dialog relative to parent."""
        x = self.parent.winfo_rootx() + 50
        y = self.parent.winfo_rooty() + 50
        self.dialog.geometry(f"+{x}+{y}")
    
    def _setup_dialog_content(self):
        """Setup the dialog content."""
        # Main frame
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="Hotkey Configuration", 
                              font=('TkDefaultFont', 12, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Create hotkey entry fields dynamically
        self._create_hotkey_fields(main_frame)
        
        # Instructions
        self._create_instructions(main_frame)
        
        # Buttons
        self._create_buttons(main_frame)
    
    def _create_hotkey_fields(self, parent):
        """Create hotkey entry fields dynamically.
        
        Args:
            parent: Parent widget for the fields.
        """
        for key, label_text, tooltip in self.hotkey_fields:
            frame = tk.Frame(parent)
            frame.pack(fill=tk.X, pady=5)
            
            # Label
            label = tk.Label(frame, text=label_text, width=15, anchor='w')
            label.pack(side=tk.LEFT)
            
            # Entry field
            self.hotkey_vars[key] = tk.StringVar(value=self.hotkey_manager.hotkeys.get(key, ''))
            entry = tk.Entry(frame, textvariable=self.hotkey_vars[key], width=20)
            entry.pack(side=tk.LEFT, padx=(10, 0))
            
            # Add tooltip if available
            if tooltip:
                self._add_tooltip(entry, tooltip)
    
    def _add_tooltip(self, widget, text):
        """Add a simple tooltip to a widget.
        
        Args:
            widget: Widget to add tooltip to.
            text: Tooltip text.
        """
        def on_enter(event):
            # Simple tooltip implementation - could be enhanced
            pass
        
        def on_leave(event):
            pass
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def _create_instructions(self, parent):
        """Create instruction text.
        
        Args:
            parent: Parent widget for instructions.
        """
        instructions_text = (
            "Instructions:\n"
            "• Single keys: a, b, *, -, etc.\n"
            "• Combinations: ctrl+alt+*, shift+f1, etc.\n"
            "• Special keys: space, enter, esc, f1-f12\n"
            "• Current defaults: * (record), - (cancel), ctrl+alt+* (enable/disable)"
        )
        
        instructions = tk.Label(parent, text=instructions_text,
                               justify=tk.LEFT, wraplength=360, 
                               font=('TkDefaultFont', 9))
        instructions.pack(pady=20, fill=tk.X)
    
    def _create_buttons(self, parent):
        """Create dialog buttons.
        
        Args:
            parent: Parent widget for buttons.
        """
        button_frame = tk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Reset to defaults button
        reset_button = tk.Button(button_frame, text="Reset to Defaults", 
                                command=self._reset_to_defaults)
        reset_button.pack(side=tk.LEFT)
        
        # Cancel button
        cancel_button = tk.Button(button_frame, text="Cancel", 
                                 command=self._on_cancel)
        cancel_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Apply button
        apply_button = tk.Button(button_frame, text="Apply", 
                                command=self._on_apply)
        apply_button.pack(side=tk.RIGHT)
    
    def _reset_to_defaults(self):
        """Reset all hotkeys to default values."""
        for key, var in self.hotkey_vars.items():
            default_value = config.DEFAULT_HOTKEYS.get(key, '')
            var.set(default_value)
    
    def _on_apply(self):
        """Apply the hotkey changes."""
        try:
            # Validate and collect new hotkeys
            new_hotkeys = {}
            for key, var in self.hotkey_vars.items():
                value = var.get().strip()
                if value:
                    new_hotkeys[key] = value
                else:
                    messagebox.showerror("Error", f"Hotkey for {key} cannot be empty")
                    return
            
            # Update hotkey manager
            self.hotkey_manager.update_hotkeys(new_hotkeys)
            
            # Save to settings
            settings_manager.save_hotkey_settings(new_hotkeys)
            
            messagebox.showinfo("Success", "Hotkeys updated successfully!")
            self._on_cancel()  # Close dialog
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update hotkeys: {str(e)}")
    
    def _on_cancel(self):
        """Cancel and close the dialog."""
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None
    
    def _validate_hotkey(self, hotkey_string: str) -> bool:
        """Validate a hotkey string format.
        
        Args:
            hotkey_string: Hotkey string to validate.
            
        Returns:
            True if valid, False otherwise.
        """
        if not hotkey_string:
            return False
        
        # Basic validation - could be enhanced
        parts = hotkey_string.lower().split('+')
        if len(parts) == 0:
            return False
        
        # Check for valid modifiers
        valid_modifiers = {'ctrl', 'alt', 'shift', 'win'}
        for part in parts[:-1]:  # All but last should be modifiers
            if part not in valid_modifiers:
                return False
        
        # Last part should be the key
        main_key = parts[-1]
        if not main_key:
            return False
        
        return True 