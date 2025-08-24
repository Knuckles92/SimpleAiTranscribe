"""
Minimalist Zen style - clean, subtle design with gentle animations and muted colors.
"""
import math
from typing import Dict, Any
from .base_style import BaseWaveformStyle
from .style_factory import register_style


@register_style
class MinimalistStyle(BaseWaveformStyle):
    """Minimalist zen style with subtle animations and clean aesthetics."""
    
    def __init__(self, canvas, width: int, height: int, config: Dict[str, Any]):
        super().__init__(canvas, width, height, config)
        
        self._display_name = "Minimalist Zen"
        self._description = "Clean, subtle design with gentle animations"
        
        # Style-specific settings
        self.line_count = config.get('line_count', 18)
        self.line_width = config.get('line_width', 2)
        self.line_spacing = config.get('line_spacing', 8)
        
        # Subtle color palette
        self.bg_color = config.get('bg_color', '#f8f8f8')
        self.primary_color = config.get('primary_color', '#4a4a4a')
        self.accent_color = config.get('accent_color', '#6b9bd2')
        self.subtle_color = config.get('subtle_color', '#c0c0c0')
        self.text_color = config.get('text_color', '#333333')
        
        # Gentle animation settings
        self.breathing_speed = config.get('breathing_speed', 0.8)
        self.ripple_speed = config.get('ripple_speed', 1.2)
        self.fade_speed = config.get('fade_speed', 0.6)
        self.smoothing = config.get('smoothing', 0.05)
        
    def draw_recording_state(self, message: str = "Recording..."):
        """Draw subtle breathing waveform lines."""
        if not self.canvas:
            return
            
        self.clear_canvas()
        self._draw_zen_background()
        
        # Calculate line positions
        total_width = self.line_count * self.line_spacing
        start_x = (self.width - total_width) // 2
        
        # Draw gentle waveform lines
        for i in range(self.line_count):
            x = start_x + i * self.line_spacing
            
            # Get audio level with gentle processing
            if i < len(self.audio_levels):
                level = self.audio_levels[i]
            else:
                level = 0.0
            
            # Add breathing animation
            breathing_factor = math.sin(self.animation_time * self.breathing_speed + i * 0.3) * 0.1
            smooth_level = level + breathing_factor
            smooth_level = max(0.0, min(1.0, smooth_level))
            
            # Calculate line height (very subtle)
            min_height = 2
            max_height = 25
            line_height = min_height + smooth_level * max_height
            
            # Center the line vertically
            center_y = self.height // 2
            y1 = center_y - line_height // 2
            y2 = center_y + line_height // 2
            
            # Color based on level (subtle gradient)
            if smooth_level > 0.6:
                color = self.accent_color
            elif smooth_level > 0.3:
                color = self.interpolate_color(self.subtle_color, self.accent_color, 
                                             (smooth_level - 0.3) / 0.3)
            else:
                color = self.interpolate_color(self.primary_color, self.subtle_color, 
                                             smooth_level / 0.3)
            
            # Draw thin line
            self.canvas.create_line(
                x, y1, x, y2,
                fill=color, width=self.line_width, capstyle="round"
            )
        
        # Draw subtle status text
        self.draw_text(message, self.width // 2, self.height - 15, 
                      self.text_color, ("Arial", 7, "normal"))
        
    def draw_processing_state(self, message: str = "Processing..."):
        """Draw gentle expanding circle with fade."""
        if not self.canvas:
            return
            
        self.clear_canvas()
        self._draw_zen_background()
        
        center_x = self.width // 2
        center_y = self.height // 2 - 5
        
        # Gentle breathing circle
        breath_factor = 1.0 + 0.15 * math.sin(self.animation_time * self.fade_speed)
        base_radius = 12
        radius = base_radius * breath_factor
        
        # Draw concentric circles with fading opacity
        circle_count = 4
        for i in range(circle_count):
            current_radius = radius - i * 3
            if current_radius > 0:
                # Calculate fade intensity
                fade_intensity = 1.0 - (i / circle_count)
                color_intensity = int(fade_intensity * 255)
                
                # Create faded color
                if i == 0:
                    color = self.accent_color
                else:
                    # Fade to background
                    fade_factor = fade_intensity * 0.7
                    color = self.interpolate_color(self.bg_color, self.accent_color, fade_factor)
                
                self.canvas.create_oval(
                    center_x - current_radius, center_y - current_radius,
                    center_x + current_radius, center_y + current_radius,
                    outline=color, width=1, fill=""
                )
        
        # Central dot
        self.canvas.create_oval(
            center_x - 2, center_y - 2, center_x + 2, center_y + 2,
            fill=self.primary_color, outline=""
        )
        
        # Draw subtle status text
        self.draw_text(message, self.width // 2, self.height - 15, 
                      self.text_color, ("Arial", 7, "normal"))
        
    def draw_transcribing_state(self, message: str = "Transcribing..."):
        """Draw gentle ripple waves."""
        if not self.canvas:
            return
            
        self.clear_canvas()
        self._draw_zen_background()
        
        center_y = self.height // 2 - 5
        
        # Draw gentle ripple waves
        wave_count = 2
        for wave_idx in range(wave_count):
            wave_offset = wave_idx * math.pi
            
            # Create subtle wave points
            points = []
            for x in range(0, self.width, 6):
                # Gentle sine wave
                wave_amplitude = 8
                wave_length = 40
                wave = math.sin((x / wave_length) + (self.animation_time * self.ripple_speed) + wave_offset)
                y = center_y + wave * wave_amplitude + wave_idx * 6
                points.extend([x, y])
            
            if len(points) >= 4:
                # Draw wave with subtle color
                wave_color = self.accent_color if wave_idx == 0 else self.subtle_color
                
                self.canvas.create_line(
                    points,
                    fill=wave_color,
                    width=1,
                    smooth=True
                )
        
        # Add subtle dots for zen-like meditation feel
        dot_count = 5
        for i in range(dot_count):
            dot_x = (self.width / (dot_count + 1)) * (i + 1)
            dot_y = self.height - 30
            
            # Gentle pulsing
            pulse = 0.8 + 0.2 * math.sin(self.animation_time * 2 + i * 1.2)
            dot_size = 2 * pulse
            
            self.canvas.create_oval(
                dot_x - dot_size, dot_y - dot_size,
                dot_x + dot_size, dot_y + dot_size,
                fill=self.subtle_color, outline=""
            )
        
        # Draw subtle status text
        self.draw_text(message, self.width // 2, self.height - 15, 
                      self.text_color, ("Arial", 7, "normal"))
    
    def _draw_zen_background(self):
        """Draw clean background with subtle border."""
        # Clean background
        self.canvas.create_rectangle(
            0, 0, self.width, self.height,
            fill=self.bg_color, outline=""
        )
        
        # Very subtle border
        self.canvas.create_rectangle(
            2, 2, self.width - 2, self.height - 2,
            fill="", outline=self.subtle_color, width=1
        )
        
        # Optional: Add very subtle texture with dots
        texture_spacing = 25
        for x in range(texture_spacing, self.width, texture_spacing):
            for y in range(texture_spacing, self.height, texture_spacing):
                if (x + y) % 50 == 0:  # Very sparse pattern
                    self.canvas.create_oval(
                        x - 0.5, y - 0.5, x + 0.5, y + 0.5,
                        fill=self.subtle_color, outline=""
                    )
    
    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """Get default configuration for minimalist style."""
        return {
            'line_count': 18,
            'line_width': 2,
            'line_spacing': 8,
            'bg_color': '#f8f8f8',
            'primary_color': '#4a4a4a',
            'accent_color': '#6b9bd2',
            'subtle_color': '#c0c0c0',
            'text_color': '#333333',
            'breathing_speed': 0.8,
            'ripple_speed': 1.2,
            'fade_speed': 0.6,
            'smoothing': 0.05
        }
    
    @classmethod
    def get_preview_config(cls) -> Dict[str, Any]:
        """Get configuration optimized for preview display."""
        config = cls.get_default_config()
        # Make preview more responsive
        config.update({
            'line_count': 14,
            'line_spacing': 6,
            'breathing_speed': 1.2,
            'ripple_speed': 1.8,
            'fade_speed': 0.9
        })
        return config