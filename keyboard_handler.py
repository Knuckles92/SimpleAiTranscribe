import keyboard
import logging
import time

class KeyboardHandler:
    def __init__(self, toggle_recording_callback, cancel_callback, toggle_program_callback):
        """
        Initialize the keyboard handler
        
        Args:
            toggle_recording_callback: Callback for starting/stopping recording
            cancel_callback: Callback for canceling operations
            toggle_program_callback: Callback for enabling/disabling the program
        """
        self.toggle_recording_callback = toggle_recording_callback
        self.cancel_callback = cancel_callback
        self.toggle_program_callback = toggle_program_callback
        self.program_enabled = True
        self._last_trigger_time = 0
        
    def setup(self):
        """Set up keyboard hooks"""
        keyboard.hook(self._handle_keyboard_event, suppress=True)
        keyboard.add_hotkey('f9', lambda: None, suppress=True)
        
    def _handle_keyboard_event(self, event):
        """Handle keyboard events"""
        if event.event_type == keyboard.KEY_DOWN:
            logging.info(f"Keyboard event: {event.name}, event_type: {event.event_type}, scan_code: {event.scan_code}")
            
            # Toggle program enabled state (Ctrl+Alt+*)
            if (event.name == '*' and
                keyboard.is_pressed('ctrl') and
                keyboard.is_pressed('alt')):
                self.program_enabled = not self.program_enabled
                self.toggle_program_callback(self.program_enabled)
                return False
                
            # If program is disabled, only allow the enable hotkey
            if not self.program_enabled:
                if not (event.name == '*' and
                       keyboard.is_pressed('ctrl') and
                       keyboard.is_pressed('alt')):
                    return True
                    
            # Start/stop recording (*)
            elif event.name == '*':
                current_time = time.time()
                if current_time - self._last_trigger_time > 0.3:
                    self._last_trigger_time = current_time
                    self.toggle_recording_callback()
                return False
                
            # Cancel operation (-)
            elif event.name == '-':
                self.cancel_callback()
                return False
                
        return True
        
    def cleanup(self):
        """Clean up keyboard hooks"""
        try:
            keyboard.unhook_all()
        except Exception as e:
            logging.error(f"Error cleaning up keyboard hooks: {e}")
