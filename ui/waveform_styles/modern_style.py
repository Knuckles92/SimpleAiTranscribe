"""
Modern waveform style - clean bars with gradient colors and smooth animations.
This is the original/default style with enhancements.
"""
import math
from typing import Dict, Any
from .base_style import BaseWaveformStyle
from .style_factory import register_style


@register_style
class ModernStyle(BaseWaveformStyle):
    """Modern clean style with gradient bars and smooth animations."""
    
    def __init__(self, canvas, width: int, height: int, config: Dict[str, Any]):
        super().__init__(canvas, width, height, config)
        
        self._display_name = "Modern"
        self._description = "Clean gradient bars with smooth animations"
        
        # Style-specific settings
        self.bar_count = config.get('bar_count', 20)
        self.bar_width = config.get('bar_width', 8)
        self.bar_spacing = config.get('bar_spacing', 2)
        
        # Colors
        self.bg_color = config.get('bg_color', '#1a1a1a')
        self.accent_color = config.get('accent_color', '#00d4ff')
        self.secondary_color = config.get('secondary_color', '#0099cc')
        self.text_color = config.get('text_color', '#ffffff')
        self.danger_color = config.get('danger_color', '#ff4444')
        
        # Animation settings
        self.pulse_speed = config.get('pulse_speed', 2.0)
        self.pulse_amplitude = config.get('pulse_amplitude', 0.3)
        self.wave_speed = config.get('wave_speed', 3.0)
        self.smoothing_factor = config.get('smoothing_factor', 0.1)
        
    def draw_recording_state(self, message: str = "Recording..."):
        """Draw real-time audio waveform for recording state."""
        if not self.canvas:
            return
            
        self.clear_canvas()
        
        # Draw background
        self._draw_background()
        
        # Calculate bar positions
        total_bar_width = self.bar_count * (self.bar_width + self.bar_spacing) - self.bar_spacing
        start_x = (self.width - total_bar_width) // 2
        
        # Draw waveform bars
        for i in range(self.bar_count):
            x = start_x + i * (self.bar_width + self.bar_spacing)
            
            # Get audio level for this bar
            if i < len(self.audio_levels):
                level = self.audio_levels[i]
            else:
                level = 0.0
                
            # Add some smoothing and noise for visual appeal
            smooth_level = level + self.smoothing_factor * math.sin(self.animation_time * 10 + i * 0.5)
            smooth_level = max(0.0, min(1.0, smooth_level))
            
            # Calculate bar height (minimum height for aesthetics)
            min_height = 4
            max_bar_height = self.height - 30
            bar_height = min_height + smooth_level * max_bar_height
            
            # Center the bar vertically
            y1 = (self.height - bar_height) // 2
            y2 = y1 + bar_height
            
            # Color gradient based on level
            if smooth_level > 0.7:
                color = self.interpolate_color(self.secondary_color, self.danger_color, 
                                             (smooth_level - 0.7) / 0.3)
            else:
                color = self.interpolate_color(self.accent_color, self.secondary_color, smooth_level)
                
            # Draw bar with rounded edges
            self._draw_rounded_bar(x, y1, x + self.bar_width, y2, color)
            
        # Draw status text
        self.draw_text(message, self.width // 2, self.height - 12, self.text_color)
        
    def draw_processing_state(self, message: str = "Processing..."):
        """Draw pulsing animation for processing state."""
        if not self.canvas:
            return
            
        self.clear_canvas()
        self._draw_background()
        
        # Pulsing circle animation
        pulse_factor = 1.0 + self.pulse_amplitude * math.sin(self.animation_time * self.pulse_speed)
        
        center_x = self.width // 2
        center_y = self.height // 2 - 5
        base_radius = 15
        radius = base_radius * pulse_factor
        
        # Draw pulsing circle with gradient effect
        for i in range(5):
            alpha = 1.0 - (i / 5.0)
            color = self.interpolate_color(self.accent_color, self.bg_color, 1.0 - alpha)
            current_radius = radius - i * 2
            
            if current_radius > 0:
                self.canvas.create_oval(
                    center_x - current_radius, center_y - current_radius,
                    center_x + current_radius, center_y + current_radius,
                    fill=color, outline=""
                )
                
        # Draw status text
        self.draw_text(message, self.width // 2, self.height - 12, self.text_color)
        
    def draw_transcribing_state(self, message: str = "Transcribing..."):
        """Draw wave animation for transcribing state."""
        if not self.canvas:
            return
            
        self.clear_canvas()
        self._draw_background()
        
        # Flowing wave animation
        wave_count = 3
        center_y = self.height // 2 - 5
        
        for wave in range(wave_count):
            wave_offset = wave * (2 * math.pi / wave_count)
            
            # Calculate wave points
            points = []
            for x in range(0, self.width, 4):
                y_offset = 10 * math.sin((x / 20.0) + (self.animation_time * self.wave_speed) + wave_offset)
                y = center_y + y_offset
                points.extend([x, y])
                
            if len(points) >= 4:
                # Draw wave line
                alpha = 1.0 - (wave * 0.3)
                color = self.interpolate_color(self.accent_color, self.bg_color, 1.0 - alpha)
                
                self.canvas.create_line(
                    points,
                    fill=color,
                    width=2,
                    smooth=True
                )
                
        # Draw status text
        self.draw_text(message, self.width // 2, self.height - 12, self.text_color)
    
    def draw_canceling_state(self, message: str = "Cancelled"):
        """Draw shrinking bars animation for canceling state."""
        if not self.canvas:
            return
            
        self.clear_canvas()
        self._draw_background()
        
        # Get cancellation progress (0.0 to 1.0)
        progress = self.get_cancellation_progress()
        
        # Shrinking and fading animation
        shrink_factor = 1.0 - progress  # Bars shrink as animation progresses
        fade_factor = 1.0 - progress    # Bars fade as animation progresses
        
        # Calculate bar positions
        total_bar_width = self.bar_count * (self.bar_width + self.bar_spacing) - self.bar_spacing
        start_x = (self.width - total_bar_width) // 2
        
        # Draw shrinking bars
        for i in range(self.bar_count):
            x = start_x + i * (self.bar_width + self.bar_spacing)
            
            # Use last known audio levels or create a fake pattern
            if i < len(self.audio_levels) and len(self.audio_levels) > 0:
                level = self.audio_levels[i]
            else:
                # Create a fake decay pattern if no audio levels
                level = max(0.0, 0.5 - (i * 0.02))
            
            # Apply shrink factor to bar height
            min_height = 4
            max_bar_height = self.height - 30
            bar_height = (min_height + level * max_bar_height) * shrink_factor
            
            if bar_height <= 0:
                continue
                
            # Center the bar vertically
            y1 = (self.height - bar_height) // 2
            y2 = y1 + bar_height
            
            # Fade color toward background
            faded_color = self.interpolate_color(self.danger_color, self.bg_color, progress)
                
            # Draw shrinking bar
            self._draw_rounded_bar(x, y1, x + self.bar_width, y2, faded_color)
            
        # Draw fading status text
        text_color = self.interpolate_color(self.text_color, self.bg_color, progress * 0.7)
        self.draw_text(message, self.width // 2, self.height - 12, text_color)
    
    def draw_idle_state(self, message: str = ""):
        """Draw idle state with subtle background and message."""
        if not self.canvas:
            return
            
        self.clear_canvas()
        
        # Only draw if we have a message
        if message:
            self._draw_background()
            
            # Draw a subtle indicator - small static circle
            center_x = self.width // 2
            center_y = self.height // 2 - 5
            radius = 8
            
            # Use a muted version of secondary color for idle state
            idle_color = self.interpolate_color(self.secondary_color, self.bg_color, 0.7)
            
            self.canvas.create_oval(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                fill=idle_color, outline=""
            )
            
            # Draw status text
            self.draw_text(message, self.width // 2, self.height - 12, self.text_color)
    
    def _draw_background(self):
        """Draw the background with subtle border."""
        margin = 5
        self.canvas.create_rectangle(
            margin, margin, self.width - margin, self.height - margin,
            fill=self.bg_color, outline=self.secondary_color, width=1
        )
    
    def _draw_rounded_bar(self, x1: float, y1: float, x2: float, y2: float, color: str):
        """Draw a bar with rounded edges."""
        if not self.canvas:
            return
            
        # For small bars, just draw rectangles
        if y2 - y1 < 6:
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
        else:
            # Draw rectangle with rounded effect
            radius = min(2, (x2 - x1) // 2)
            self.canvas.create_rectangle(
                x1, y1 + radius, x2, y2 - radius,
                fill=color, outline=""
            )
            # Top and bottom caps
            self.canvas.create_oval(
                x1, y1, x2, y1 + radius * 2,
                fill=color, outline=""
            )
            self.canvas.create_oval(
                x1, y2 - radius * 2, x2, y2,
                fill=color, outline=""
            )
    
    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """Get default configuration for modern style."""
        return {
            'bar_count': 20,
            'bar_width': 8,
            'bar_spacing': 2,
            'bg_color': '#1a1a1a',
            'accent_color': '#00d4ff',
            'secondary_color': '#0099cc',
            'text_color': '#ffffff',
            'danger_color': '#ff4444',
            'pulse_speed': 2.0,
            'pulse_amplitude': 0.3,
            'wave_speed': 3.0,
            'smoothing_factor': 0.1
        }
    
    @classmethod
    def get_preview_config(cls) -> Dict[str, Any]:
        """Get configuration optimized for preview display."""
        config = cls.get_default_config()
        # Make preview more compact and faster
        config.update({
            'bar_count': 12,
            'bar_width': 6,
            'bar_spacing': 1,
            'pulse_speed': 3.0,
            'wave_speed': 4.0
        })
        return config