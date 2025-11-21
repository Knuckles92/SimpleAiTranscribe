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

def test_particle_style_convergence():
    print("Testing ParticleStyle Convergence...")
    
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
        
        print("Testing draw_transcribing_state (convergence)...")
        # Run multiple frames to test convergence logic
        for i in range(10):
            style.draw_transcribing_state(painter, rect, "Test Transcribing")
            style.update_animation_time(0.033)
        
        painter.end()
        print("Convergence test passed.")
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_particle_style_convergence()
    sys.exit(0 if success else 1)
