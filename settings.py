"""
Settings management for the Audio Recorder application.
"""
import json
import os
import logging
from typing import Dict, Any
from config import config


class SettingsManager:
    """Handles loading and saving application settings."""
    
    def __init__(self, settings_file: str = None):
        """Initialize the settings manager.
        
        Args:
            settings_file: Path to settings file. Uses config default if None.
        """
        self.settings_file = settings_file or config.SETTINGS_FILE
    
    def load_hotkey_settings(self) -> Dict[str, str]:
        """Load hotkey settings from file, return defaults if file doesn't exist.
        
        Returns:
            Dictionary of hotkey mappings.
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    return settings.get('hotkeys', config.DEFAULT_HOTKEYS)
        except Exception as e:
            logging.warning(f"Failed to load settings: {e}")
        
        return config.DEFAULT_HOTKEYS.copy()
    
    def save_hotkey_settings(self, hotkeys: Dict[str, str]) -> None:
        """Save hotkey settings to file.
        
        Args:
            hotkeys: Dictionary of hotkey mappings to save.
            
        Raises:
            Exception: If saving fails.
        """
        try:
            settings = {'hotkeys': hotkeys}
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            logging.info("Hotkey settings saved successfully")
        except Exception as e:
            logging.error(f"Failed to save settings: {e}")
            raise
    
    def load_all_settings(self) -> Dict[str, Any]:
        """Load all settings from file.
        
        Returns:
            Dictionary containing all settings.
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.warning(f"Failed to load all settings: {e}")
        
        return {}
    
    def save_all_settings(self, settings: Dict[str, Any]) -> None:
        """Save all settings to file.
        
        Args:
            settings: Dictionary of all settings to save.
            
        Raises:
            Exception: If saving fails.
        """
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            logging.info("All settings saved successfully")
        except Exception as e:
            logging.error(f"Failed to save all settings: {e}")
            raise


# Global settings manager instance
settings_manager = SettingsManager() 