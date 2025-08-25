#!/usr/bin/env python3
"""
Test script to demonstrate the new cancellation animations across different waveform styles.
Run this to see how each style handles the canceling state.
"""

import tkinter as tk
from ui.waveform_overlay import WaveformOverlay
from config import config
import time
import threading


def test_style_cancellation(style_name):
    """Test the cancellation animation for a specific style."""
    print(f"\nTesting {style_name} cancellation animation...")
    
    # Create root window
    root = tk.Tk()
    root.title(f"Testing {style_name.title()} Cancellation")
    root.geometry("400x200")
    
    # Create overlay
    overlay = WaveformOverlay(root, initial_style=style_name)
    
    # Add some fake audio levels for better visualization
    fake_audio_levels = [0.1 + (i * 0.05) for i in range(20)]
    overlay.update_audio_level(0.6)  # Set a decent audio level
    overlay.current_style.update_audio_levels(fake_audio_levels, 0.6)
    
    # Instructions
    label = tk.Label(root, text=f"Testing {style_name.title()} Cancellation Animation\n\nClick 'Test Cancel' to see the animation", 
                     font=("Arial", 12), pady=20)
    label.pack()
    
    def show_cancellation():
        """Show the cancellation animation."""
        overlay.show_canceling("Recording Cancelled")
        
    def close_app():
        """Clean up and close."""
        overlay.cleanup()
        root.quit()
        root.destroy()
    
    # Buttons
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)
    
    test_btn = tk.Button(button_frame, text="Test Cancel Animation", 
                        command=show_cancellation, bg="#ff4444", fg="white")
    test_btn.pack(side=tk.LEFT, padx=5)
    
    close_btn = tk.Button(button_frame, text="Close", command=close_app)
    close_btn.pack(side=tk.LEFT, padx=5)
    
    root.protocol("WM_DELETE_WINDOW", close_app)
    root.mainloop()


def test_all_styles():
    """Test cancellation animations for all available styles."""
    overlay = WaveformOverlay(tk.Tk())
    styles = overlay.get_available_styles()
    overlay.cleanup()
    
    print("Available cancellation animation styles:")
    for i, style in enumerate(styles, 1):
        print(f"{i}. {style.title()}")
    
    print(f"\n{len(styles)} styles implement cancellation animations")
    print(f"Cancellation duration: {config.CANCELLATION_ANIMATION_DURATION_MS}ms")
    
    while True:
        try:
            choice = input(f"\nEnter style number (1-{len(styles)}) to test, or 'q' to quit: ").strip()
            
            if choice.lower() == 'q':
                break
                
            choice_num = int(choice)
            if 1 <= choice_num <= len(styles):
                style_name = styles[choice_num - 1]
                test_style_cancellation(style_name)
            else:
                print(f"Please enter a number between 1 and {len(styles)}")
                
        except ValueError:
            print("Please enter a valid number or 'q' to quit")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    print("=== Waveform Cancellation Animation Tester ===")
    print("This demonstrates the new cancellation animations for the audio recorder.")
    test_all_styles()