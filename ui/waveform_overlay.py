"""
Modern waveform overlay for the Audio Recorder application.
Provides real-time audio visualization and stylized status animations.
Refactored to use the pluggable style system.
"""
import tkinter as tk
from tkinter import Canvas
import numpy as np
import threading
import time
import math
from typing import List, Optional, Tuple, Dict, Any
import logging
from config import config

# Import style system (this automatically registers all styles)
from .waveform_styles import WaveformStyleFactory, BaseWaveformStyle


class WaveformOverlay:
    """Modern waveform overlay with real-time audio visualization."""
    
    def __init__(self, parent: tk.Tk, initial_style: str = "modern"):
        """Initialize the waveform overlay.
        
        Args:
            parent: Parent tkinter window.
            initial_style: Initial style name to use (default: "modern")
        """
        self.parent = parent
        self.overlay: Optional[tk.Toplevel] = None
        self.canvas: Optional[Canvas] = None
        
        # Animation state
        self.is_visible = False
        self.current_state = "idle"  # idle, recording, processing, transcribing, canceling
        self.animation_thread: Optional[threading.Thread] = None
        self.should_animate = False
        self.current_message = ""
        self.canceling_start_time = 0.0
        
        # Audio data
        self.audio_levels: List[float] = [0.0] * config.WAVEFORM_BAR_COUNT  # Rolling buffer of audio levels
        self.current_level = 0.0
        self.max_level = 0.0
        
        # Animation parameters from config
        self.frame_rate = config.WAVEFORM_FRAME_RATE
        self.frame_delay = 1.0 / self.frame_rate
        self.animation_time = 0.0
        self.last_frame_time = time.time()
        
        # Visual settings from config
        self.width = config.WAVEFORM_OVERLAY_WIDTH
        self.height = config.WAVEFORM_OVERLAY_HEIGHT
        
        # Style system
        self.current_style: Optional[BaseWaveformStyle] = None
        self.default_style = initial_style
        self.fallback_style = "modern"
        
        self._setup_overlay()
        self._initialize_style(initial_style)
        
    def _setup_overlay(self):
        """Create and configure the overlay window."""
        self.overlay = tk.Toplevel(self.parent)
        self.overlay.title("")
        self.overlay.geometry(f"{self.width}x{self.height}")
        self.overlay.attributes('-topmost', True)
        self.overlay.overrideredirect(True)
        self.overlay.withdraw()
        
        # Configure transparency and styling - use default dark background
        bg_color = config.WAVEFORM_BG_COLOR
        self.overlay.configure(bg=bg_color)
        self.overlay.attributes('-alpha', 0.9)
        
        # Create canvas for drawing
        self.canvas = Canvas(
            self.overlay,
            width=self.width,
            height=self.height,
            bg=bg_color,
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
    def _initialize_style(self, style_name: str):
        """Initialize the waveform style.
        
        Args:
            style_name: Name of the style to initialize
        """
        try:
            # Get default config for the style
            style_config = WaveformStyleFactory.get_default_config(style_name)
            
            # Create style instance
            self.current_style = WaveformStyleFactory.create_style(
                style_name, self.canvas, self.width, self.height, style_config
            )
            
            logging.info(f"Initialized waveform style: {self.current_style.display_name}")
            
        except Exception as e:
            logging.error(f"Failed to initialize style '{style_name}': {e}")
            if style_name != self.fallback_style:
                logging.info(f"Falling back to '{self.fallback_style}' style")
                self._initialize_style(self.fallback_style)
            else:
                logging.error("Failed to initialize fallback style - overlay may not work correctly")
                
    def set_style(self, style_name: str, config: Optional[Dict[str, Any]] = None):
        """Set the current waveform style.
        
        Args:
            style_name: Name of the style to set
            config: Optional configuration dictionary for the style
        """
        try:
            # Clean up old style if it exists
            old_style = self.current_style
            
            # Get config for the new style
            if config is None:
                config = WaveformStyleFactory.get_default_config(style_name)
            
            # Create new style instance
            new_style = WaveformStyleFactory.create_style(
                style_name, self.canvas, self.width, self.height, config
            )
            
            # Update current style
            self.current_style = new_style
            
            # Clear canvas to avoid residual artifacts
            if self.canvas:
                self.canvas.delete("all")
                
            logging.info(f"Changed waveform style to: {self.current_style.display_name}")
            
        except Exception as e:
            logging.error(f"Failed to set style '{style_name}': {e}")
            # Keep the old style if new one fails
            if self.current_style is None and style_name != self.fallback_style:
                logging.info(f"Falling back to '{self.fallback_style}' style")
                self.set_style(self.fallback_style)
                
    def get_available_styles(self) -> List[str]:
        """Get list of available style names.
        
        Returns:
            List of available style names
        """
        return WaveformStyleFactory.get_available_styles()
        
    def get_current_style_info(self) -> Dict[str, str]:
        """Get information about the current style.
        
        Returns:
            Dictionary with current style information
        """
        if self.current_style:
            return {
                'name': self.current_style.name,
                'display_name': self.current_style.display_name,
                'description': self.current_style.description
            }
        else:
            return {'name': 'none', 'display_name': 'None', 'description': 'No style loaded'}
        
    def show(self, state: str, message: str = ""):
        """Show the overlay with specified state.
        
        Args:
            state: State of the overlay ('recording', 'processing', 'transcribing')
            message: Optional message to display
        """
        if not self.overlay or not self.current_style:
            return
            
        self.current_state = state
        self.current_message = message
        self.is_visible = True
        
        # Position near mouse cursor
        x = self.parent.winfo_pointerx() + 10
        y = self.parent.winfo_pointery() + 10
        self.overlay.geometry(f"{self.width}x{self.height}+{x}+{y}")
        
        self.overlay.deiconify()
        
        # Start animation
        self._start_animation()
        
    def show_canceling(self, message: str = "Cancelled"):
        """Show the overlay with canceling state and animation.
        
        Args:
            message: Optional message to display during cancellation
        """
        if not self.overlay or not self.current_style:
            return
            
        self.current_state = "canceling"
        self.current_message = message
        self.is_visible = True
        self.canceling_start_time = time.time()
        
        # Pass canceling start time to the current style
        if self.current_style:
            self.current_style.set_canceling_start_time(self.canceling_start_time)
        
        # Position near mouse cursor
        x = self.parent.winfo_pointerx() + 10
        y = self.parent.winfo_pointery() + 10
        self.overlay.geometry(f"{self.width}x{self.height}+{x}+{y}")
        
        self.overlay.deiconify()
        
        # Start animation
        self._start_animation()
        
    def hide(self):
        """Hide the overlay."""
        self.is_visible = False
        self._stop_animation()
        
        if self.overlay:
            self.overlay.withdraw()
            
    def update_audio_level(self, level: float):
        """Update the current audio level for waveform display.
        
        Args:
            level: Audio level (0.0 to 1.0)
        """
        self.current_level = max(0.0, min(1.0, level))
        self.max_level = max(self.max_level * 0.99, self.current_level)  # Decay max level
        
        # Update rolling buffer
        self.audio_levels.append(self.current_level)
        # Use configurable bar count
        bar_count = config.WAVEFORM_BAR_COUNT
        if len(self.audio_levels) > bar_count:
            self.audio_levels.pop(0)
            
        # Update the current style with audio levels
        if self.current_style:
            self.current_style.update_audio_levels(self.audio_levels, self.current_level)
            
    def _start_animation(self):
        """Start the animation thread."""
        if self.animation_thread and self.animation_thread.is_alive():
            return
            
        self.should_animate = True
        self.animation_time = 0.0
        self.animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self.animation_thread.start()
        
    def _stop_animation(self):
        """Stop the animation thread."""
        self.should_animate = False
        if self.animation_thread:
            self.animation_thread.join(timeout=0.1)
            
    def _animation_loop(self):
        """Main animation loop running in separate thread."""
        last_time = time.time()
        
        while self.should_animate and self.is_visible:
            current_time = time.time()
            delta_time = current_time - last_time
            last_time = current_time
            
            self.animation_time += delta_time
            
            # Update style animation time
            if self.current_style:
                self.current_style.update_animation_time(delta_time)
            
            # Schedule canvas update on main thread
            if self.canvas and self.overlay:
                try:
                    self.parent.after_idle(self._draw_frame)
                except (tk.TclError, RuntimeError):
                    # Window was destroyed or main thread is not in main loop
                    self.should_animate = False
                    break
                    
            time.sleep(self.frame_delay)
            
    def _draw_frame(self):
        """Draw a single animation frame using the current style."""
        if not self.canvas or not self.is_visible or not self.current_style:
            return
            
        try:
            # Clear canvas
            self.current_style.clear_canvas()
            
            # Get default message if none provided
            message = self.current_message
            
            # Draw based on current state using the style system
            if self.current_state == "recording":
                if not message:
                    message = "Recording..."
                self.current_style.draw_recording_state(message)
            elif self.current_state == "processing":
                if not message:
                    message = "Processing..."
                self.current_style.draw_processing_state(message)
            elif self.current_state == "transcribing":
                if not message:
                    message = "Transcribing..."
                self.current_style.draw_transcribing_state(message)
            elif self.current_state == "canceling":
                if not message:
                    message = "Cancelled"
                # Check if cancellation animation should end
                cancellation_duration = config.CANCELLATION_ANIMATION_DURATION_MS / 1000.0
                if (time.time() - self.canceling_start_time) > cancellation_duration:
                    self.hide()
                    return
                self.current_style.draw_canceling_state(message)
            elif self.current_state == "stt_disable":
                if not message:
                    message = "STT Disabled"
                self.current_style.draw_stt_disable_state(message)
            else:
                # Idle or unknown state
                self.current_style.draw_idle_state(message)
                
        except tk.TclError:
            # Canvas was destroyed
            pass
        except Exception as e:
            logging.error(f"Error drawing waveform frame: {e}")
            # Fallback to basic drawing if style fails
            if self.canvas:
                try:
                    self.canvas.delete("all")
                    self.canvas.create_text(
                        self.width // 2, self.height // 2,
                        text=self.current_message or self.current_state.title(),
                        fill="white", font=("Arial", 10)
                    )
                except tk.TclError:
                    pass
        
    def cleanup(self):
        """Clean up resources."""
        self.hide()
        
        # Clean up style resources
        self.current_style = None
        
        if self.overlay:
            try:
                self.overlay.destroy()
            except tk.TclError:
                pass
            self.overlay = None
            
        self.canvas = None