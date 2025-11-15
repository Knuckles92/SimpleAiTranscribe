"""
Main application bootstrap for the Audio Recorder.
"""
import logging
import os
from pathlib import Path

from config import config
from ui.loading_screen import LoadingScreen
from ui.main_window import MainWindow


def setup_logging():
    """Setup application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_FILE),
            logging.StreamHandler()
        ]
    )


def main():
    """Main application entry point."""
    # Setup logging
    setup_logging()
    logging.info("Starting Audio Recorder application")

    loading_screen = None
    try:
        # Create and show loading screen
        loading_screen = LoadingScreen()
        loading_screen.show()

        # Update loading status
        loading_screen.update_status("Initializing components...")

        # Create main window (this will load Whisper model)
        loading_screen.update_status("Loading Whisper model...")
        main_window = MainWindow()

        # Hide loading screen and show main window
        loading_screen.destroy()

        # Run the main application
        logging.info("Application initialization complete")
        main_window.run()

    except Exception:
        logging.exception("Application startup failed")
        # Re-raise after logging the exception so callers see the error
        raise
    finally:
        # Ensure loading screen is destroyed if it was created
        try:
            if loading_screen is not None:
                loading_screen.destroy()
        except Exception:
            # Log but do not mask original exceptions
            logging.exception("Failed to destroy loading screen during cleanup")

        logging.info("Application shutdown complete")


if __name__ == "__main__":
    main() 