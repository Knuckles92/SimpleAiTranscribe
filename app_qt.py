"""
Main application bootstrap for Audio Recorder using modern PyQt6 UI.
This is the new entry point for the refactored application.
"""
import logging
import os
import sys
from pathlib import Path

from config import config
from ui_qt.app import QtApplication
from ui_qt.loading_screen_qt import ModernLoadingScreen
from ui_qt.ui_controller import UIController


def setup_logging():
    """Setup application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_FILE),
            logging.StreamHandler()
        ]
    )


def main():
    """Main application entry point with modern PyQt6 UI."""
    # Setup logging
    setup_logging()
    logging.info("=" * 60)
    logging.info("Starting Audio Recorder with Modern PyQt6 UI")
    logging.info("=" * 60)

    # Create Qt application
    qt_app = QtApplication()

    loading_screen = None
    ui_controller = None

    try:
        # Show loading screen
        loading_screen = ModernLoadingScreen()
        loading_screen.show()

        # Simulate initialization steps
        loading_screen.update_status("Initializing components...")
        loading_screen.update_progress("Loading theme...")
        loading_screen.repaint()

        # Give Qt time to render
        from PyQt6.QtCore import QCoreApplication
        QCoreApplication.processEvents()

        # Create UI controller
        loading_screen.update_status("Creating interface...")
        loading_screen.update_progress("Setting up windows...")
        QCoreApplication.processEvents()

        ui_controller = UIController()

        # Hide loading screen and show main window
        loading_screen.destroy()
        loading_screen = None

        # Show main window
        ui_controller.show_main_window()

        logging.info("Application initialization complete")
        logging.info("Starting event loop")

        # Run the application
        return qt_app.run(ui_controller.main_window)

    except Exception as e:
        logging.exception("Application startup failed")
        # Re-raise after logging
        raise

    finally:
        # Cleanup
        try:
            if loading_screen is not None:
                loading_screen.destroy()
        except Exception as e:
            logging.exception("Failed to cleanup loading screen")

        try:
            if ui_controller is not None:
                ui_controller.cleanup()
        except Exception as e:
            logging.exception("Failed to cleanup UI controller")

        logging.info("=" * 60)
        logging.info("Application shutdown complete")
        logging.info("=" * 60)


if __name__ == "__main__":
    sys.exit(main())
