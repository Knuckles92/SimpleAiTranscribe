"""
Base class for all waveform overlay styles.
Defines the interface that all styles must implement.
"""
from abc import ABC, abstractmethod
from tkinter import Canvas
from typing import List, Dict, Any, Optional, Tuple
import math
import time


class BaseWaveformStyle(ABC):
    """Abstract base class for waveform overlay styles."""
    
    def __init__(self, canvas: Canvas, width: int, height: int, config: Dict[str, Any]):
        """Initialize the style.
        
        Args:
            canvas: The tkinter Canvas to draw on
            width: Canvas width in pixels
            height: Canvas height in pixels
            config: Style-specific configuration dictionary
        """
        self.canvas = canvas
        self.width = width
        self.height = height
        self.config = config
        
        # Animation state
        self.animation_time = 0.0
        self.last_frame_time = time.time()
        
        # Audio data
        self.audio_levels: List[float] = []
        self.current_level = 0.0
        self.max_level = 0.0
        
        # Style metadata
        self._name = self.__class__.__name__.replace('Style', '').lower()
        self._display_name = self._name.title()
        self._description = "Custom waveform visualization style"
        
    @property
    def name(self) -> str:
        """Get the internal name of this style."""
        return self._name
        
    @property
    def display_name(self) -> str:
        """Get the display name of this style."""
        return self._display_name
        
    @property
    def description(self) -> str:
        """Get the description of this style."""
        return self._description
    
    def update_audio_levels(self, levels: List[float], current_level: float = 0.0):
        """Update audio levels for visualization.
        
        Args:
            levels: List of audio levels for each frequency band/bar
            current_level: Current overall audio level (0.0 to 1.0)
        """
        self.audio_levels = levels.copy()
        self.current_level = max(0.0, min(1.0, current_level))
        self.max_level = max(self.max_level * 0.99, self.current_level)
    
    def update_animation_time(self, delta_time: float):
        """Update the animation time.
        
        Args:
            delta_time: Time elapsed since last frame in seconds
        """
        self.animation_time += delta_time
    
    def clear_canvas(self):
        """Clear the canvas for drawing."""
        if self.canvas:
            self.canvas.delete("all")
    
    @abstractmethod
    def draw_recording_state(self, message: str = "Recording..."):
        """Draw the recording state visualization.
        
        Args:
            message: Status message to display
        """
        pass
    
    @abstractmethod
    def draw_processing_state(self, message: str = "Processing..."):
        """Draw the processing state visualization.
        
        Args:
            message: Status message to display
        """
        pass
    
    @abstractmethod
    def draw_transcribing_state(self, message: str = "Transcribing..."):
        """Draw the transcribing state visualization.
        
        Args:
            message: Status message to display
        """
        pass
    
    def draw_idle_state(self, message: str = ""):
        """Draw the idle state (default: clear canvas).
        
        Args:
            message: Status message to display
        """
        self.clear_canvas()
    
    # Utility methods for common drawing operations
    def interpolate_color(self, color1: str, color2: str, factor: float) -> str:
        """Interpolate between two hex colors.
        
        Args:
            color1: First color in hex format (#RRGGBB)
            color2: Second color in hex format (#RRGGBB)
            factor: Interpolation factor (0.0 to 1.0)
            
        Returns:
            Interpolated color in hex format
        """
        factor = max(0.0, min(1.0, factor))
        
        # Parse colors
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        
        # Interpolate
        r = int(r1 + (r2 - r1) * factor)
        g = int(g1 + (g2 - g1) * factor)
        b = int(b1 + (b2 - b1) * factor)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        """Convert HSV color to RGB.
        
        Args:
            h: Hue (0.0 to 360.0)
            s: Saturation (0.0 to 1.0)
            v: Value/Brightness (0.0 to 1.0)
            
        Returns:
            RGB tuple (r, g, b) with values 0-255
        """
        h = h / 60.0
        c = v * s
        x = c * (1 - abs(h % 2 - 1))
        m = v - c
        
        if 0 <= h < 1:
            r, g, b = c, x, 0
        elif 1 <= h < 2:
            r, g, b = x, c, 0
        elif 2 <= h < 3:
            r, g, b = 0, c, x
        elif 3 <= h < 4:
            r, g, b = 0, x, c
        elif 4 <= h < 5:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
            
        r, g, b = int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)
        return r, g, b
    
    def rgb_to_hex(self, r: int, g: int, b: int) -> str:
        """Convert RGB values to hex color string.
        
        Args:
            r: Red value (0-255)
            g: Green value (0-255)
            b: Blue value (0-255)
            
        Returns:
            Hex color string (#RRGGBB)
        """
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def draw_text(self, text: str, x: int, y: int, color: str = "#ffffff", 
                  font: Tuple[str, int, str] = ("Arial", 8, "bold")):
        """Draw text on the canvas.
        
        Args:
            text: Text to draw
            x: X coordinate
            y: Y coordinate
            color: Text color in hex format
            font: Font tuple (family, size, style)
        """
        if self.canvas:
            self.canvas.create_text(x, y, text=text, fill=color, font=font)
    
    def draw_rounded_rect(self, x1: int, y1: int, x2: int, y2: int, 
                         radius: int, fill: str = "", outline: str = "", width: int = 1):
        """Draw a rounded rectangle.
        
        Args:
            x1, y1: Top-left corner
            x2, y2: Bottom-right corner
            radius: Corner radius
            fill: Fill color
            outline: Outline color
            width: Outline width
        """
        if not self.canvas:
            return
            
        # Clamp radius to reasonable values
        radius = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
        
        # Create rounded rectangle using multiple shapes
        points = []
        
        # Top edge
        points.extend([x1 + radius, y1, x2 - radius, y1])
        # Top-right arc
        for angle in range(0, 91, 10):
            rad = math.radians(angle)
            x = x2 - radius + radius * math.cos(rad)
            y = y1 + radius - radius * math.sin(rad)
            points.extend([x, y])
        
        # Right edge
        points.extend([x2, y1 + radius, x2, y2 - radius])
        
        # Bottom-right arc
        for angle in range(90, 181, 10):
            rad = math.radians(angle)
            x = x2 - radius + radius * math.cos(rad)
            y = y2 - radius - radius * math.sin(rad)
            points.extend([x, y])
        
        # Bottom edge
        points.extend([x2 - radius, y2, x1 + radius, y2])
        
        # Bottom-left arc
        for angle in range(180, 271, 10):
            rad = math.radians(angle)
            x = x1 + radius + radius * math.cos(rad)
            y = y2 - radius - radius * math.sin(rad)
            points.extend([x, y])
        
        # Left edge
        points.extend([x1, y2 - radius, x1, y1 + radius])
        
        # Top-left arc
        for angle in range(270, 361, 10):
            rad = math.radians(angle)
            x = x1 + radius + radius * math.cos(rad)
            y = y1 + radius - radius * math.sin(rad)
            points.extend([x, y])
        
        # Draw the polygon
        self.canvas.create_polygon(points, fill=fill, outline=outline, width=width, smooth=True)
    
    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """Get default configuration for this style.
        
        Returns:
            Dictionary of default configuration values
        """
        return {}
    
    @classmethod
    def get_preview_config(cls) -> Dict[str, Any]:
        """Get configuration optimized for preview display.
        
        Returns:
            Dictionary of preview configuration values
        """
        return cls.get_default_config()