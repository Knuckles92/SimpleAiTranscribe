import sys
import os
import logging

# Add project root to path
sys.path.append(os.getcwd())

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QRect
from PyQt6.QtGui import QPainter, QImage

from ui_qt.waveform_styles.style_factory import create_style
from config import config

def test_particle_style():
    print("Testing ParticleStyle...")
    
    # Create dummy app
    app = QApplication(sys.argv)
    
    try:
        # Create style
        style = create_style('particle', 300, 80)
        print(f"Style created: {style._display_name}")
        
        # Test drawing methods
        image = QImage(300, 80, QImage.Format.Format_ARGB32)
        painter = QPainter(image)
        
        rect = QRect(0, 0, 300, 80)
        
        print("Testing draw_recording_state...")
        style.draw_recording_state(painter, rect, "Test Recording")
        
        print("Testing draw_processing_state...")
        style.draw_processing_state(painter, rect, "Test Processing")
        
        print("Testing draw_transcribing_state...")
        style.draw_transcribing_state(painter, rect, "Test Transcribing")
        
        painter.end()
        print("All draw methods passed.")
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_particle_style()
    sys.exit(0 if success else 1)
