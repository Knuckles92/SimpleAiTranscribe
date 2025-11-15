"""
Retro Synthwave style - 80s aesthetic with neon colors, scanlines, and VHS effects.
"""
import math
import random
from typing import Dict, Any
from .base_style import BaseWaveformStyle
from .style_factory import register_style


@register_style
class RetroStyle(BaseWaveformStyle):
    """Retro synthwave style with neon effects and scanlines."""
    
    def __init__(self, canvas, width: int, height: int, config: Dict[str, Any]):
        super().__init__(canvas, width, height, config)
        
        self._display_name = "Retro Synthwave"
        self._description = "80s aesthetic with neon colors and VHS effects"
        
        # Style-specific settings
        self.bar_count = config.get('bar_count', 16)
        self.bar_width = config.get('bar_width', 10)
        self.bar_spacing = config.get('bar_spacing', 3)
        
        # Neon colors
        self.bg_color = config.get('bg_color', '#0a0a0a')
        self.neon_pink = config.get('neon_pink', '#ff00ff')
        self.neon_cyan = config.get('neon_cyan', '#00ffff')
        self.neon_purple = config.get('neon_purple', '#8000ff')
        self.neon_green = config.get('neon_green', '#00ff00')
        self.text_color = config.get('text_color', '#ffffff')
        
        # Animation settings
        self.grid_speed = config.get('grid_speed', 1.5)
        self.scanline_speed = config.get('scanline_speed', 8.0)
        self.glitch_intensity = config.get('glitch_intensity', 0.05)
        self.glow_intensity = config.get('glow_intensity', 1.5)
        
        # VHS effects
        self.chromatic_aberration = config.get('chromatic_aberration', True)
        self.scanlines_enabled = config.get('scanlines_enabled', True)
        self.vhs_noise = config.get('vhs_noise', True)
        
    def draw_recording_state(self, message: str = "RECORDING..."):
        """Draw neon equalizer bars with VHS effects."""
        if not self.canvas:
            return
            
        self.clear_canvas()
        self._draw_retro_background()
        
        # Calculate bar positions
        total_bar_width = self.bar_count * (self.bar_width + self.bar_spacing) - self.bar_spacing
        start_x = (self.width - total_bar_width) // 2
        
        # Draw neon equalizer bars
        for i in range(self.bar_count):
            x = start_x + i * (self.bar_width + self.bar_spacing)
            
            # Get audio level with retro-style processing
            if i < len(self.audio_levels):
                level = self.audio_levels[i]
            else:
                level = 0.0
            
            # Add retro-style modulation
            retro_wave = math.sin(self.animation_time * 6 + i * 0.8) * 0.2
            level_with_wave = max(0.0, min(1.0, level + retro_wave))
            
            # Calculate bar height with minimum for retro look
            min_height = 8
            max_bar_height = self.height - 35
            bar_height = min_height + level_with_wave * max_bar_height
            
            # Create stacked bar effect (retro EQ style)
            segments = int(bar_height / 6) + 1
            segment_height = 4
            segment_spacing = 2
            
            for seg in range(segments):
                seg_y = self.height - 25 - (seg * (segment_height + segment_spacing))
                seg_x1 = x
                seg_x2 = x + self.bar_width
                seg_y1 = seg_y - segment_height
                seg_y2 = seg_y
                
                # Color based on segment height (low to high frequency colors)
                if seg < segments * 0.3:
                    color = self.neon_green
                elif seg < segments * 0.7:
                    color = self.neon_cyan
                else:
                    color = self.neon_pink
                
                # Add intensity variation
                intensity = level_with_wave + (seg / segments) * 0.5
                if intensity > random.uniform(0.3, 1.0):
                    # Draw segment with glow effect
                    self._draw_neon_rect(seg_x1, seg_y1, seg_x2, seg_y2, color)
        
        # Draw scanlines
        if self.scanlines_enabled:
            self._draw_scanlines()
            
        # Draw retro text
        self._draw_retro_text(message, self.width // 2, self.height - 12)
        
    def draw_processing_state(self, message: str = "PROCESSING..."):
        """Draw rotating neon grid with pulsing center."""
        if not self.canvas:
            return
            
        self.clear_canvas()
        self._draw_retro_background()
        
        center_x = self.width // 2
        center_y = self.height // 2 - 5
        
        # Rotating neon grid
        grid_rotation = self.animation_time * self.grid_speed
        grid_size = 30
        
        for i in range(-2, 3):
            for j in range(-2, 3):
                if i == 0 and j == 0:
                    continue  # Skip center
                    
                # Calculate grid point position
                x_offset = i * grid_size
                y_offset = j * grid_size
                
                # Rotate around center
                cos_rot = math.cos(grid_rotation)
                sin_rot = math.sin(grid_rotation)
                
                rotated_x = x_offset * cos_rot - y_offset * sin_rot
                rotated_y = x_offset * sin_rot + y_offset * cos_rot
                
                grid_x = center_x + rotated_x
                grid_y = center_y + rotated_y
                
                # Draw grid intersection
                if 0 <= grid_x < self.width and 0 <= grid_y < self.height:
                    intensity = 1.0 - (abs(i) + abs(j)) * 0.2
                    color = self.neon_cyan if (i + j) % 2 == 0 else self.neon_purple
                    
                    self.canvas.create_oval(
                        grid_x - 2, grid_y - 2, grid_x + 2, grid_y + 2,
                        fill=color, outline=""
                    )
        
        # Pulsing center core
        pulse = 1.0 + 0.4 * math.sin(self.animation_time * 4)
        core_radius = 8 * pulse
        
        # Multi-layer glow effect
        for i in range(4):
            radius = core_radius + i * 3
            alpha_factor = 1.0 - (i * 0.25)
            color = self.neon_pink
            
            self.canvas.create_oval(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                fill=color, outline=""
            )
        
        # Draw scanlines
        if self.scanlines_enabled:
            self._draw_scanlines()
            
        # Draw retro text
        self._draw_retro_text(message, self.width // 2, self.height - 12)
        
    def draw_transcribing_state(self, message: str = "TRANSCRIBING..."):
        """Draw synthwave equalizer with flowing neon waves."""
        if not self.canvas:
            return
            
        self.clear_canvas()
        self._draw_retro_background()
        
        center_y = self.height // 2 - 5
        
        # Draw multiple neon wave layers
        wave_colors = [self.neon_pink, self.neon_cyan, self.neon_purple]
        
        for wave_idx, color in enumerate(wave_colors):
            wave_offset = wave_idx * (2 * math.pi / len(wave_colors))
            
            # Create wave points
            points = []
            for x in range(0, self.width, 3):
                # Multiple sine waves for complex pattern
                wave1 = math.sin((x / 15.0) + (self.animation_time * 4) + wave_offset)
                wave2 = math.sin((x / 8.0) + (self.animation_time * 2.5) + wave_offset) * 0.5
                wave3 = math.sin((x / 25.0) + (self.animation_time * 1.5) + wave_offset) * 0.3
                
                combined_wave = wave1 + wave2 + wave3
                y_offset = combined_wave * 12
                y = center_y + y_offset + wave_idx * 8
                
                points.extend([x, y])
            
            if len(points) >= 4:
                # Draw wave with glow effect
                self.canvas.create_line(
                    points,
                    fill=color,
                    width=3,
                    smooth=True
                )
                
                # Add glow effect
                if self.glow_intensity > 1.0:
                    self.canvas.create_line(
                        points,
                        fill=color,
                        width=1,
                        smooth=True
                    )
        
        # Add frequency spectrum bars at bottom
        bar_count = 8
        bar_width = self.width // (bar_count + 1)
        
        for i in range(bar_count):
            x = i * bar_width + bar_width // 2
            
            # Simulate frequency response
            freq_response = abs(math.sin(self.animation_time * 3 + i * 0.5)) * 0.8 + 0.2
            bar_height = freq_response * 15
            
            color = wave_colors[i % len(wave_colors)]
            
            self.canvas.create_rectangle(
                x - 2, self.height - 25,
                x + 2, self.height - 25 - bar_height,
                fill=color, outline=""
            )
        
        # Draw scanlines
        if self.scanlines_enabled:
            self._draw_scanlines()
            
        # Draw retro text
        self._draw_retro_text(message, self.width // 2, self.height - 12)
    
    def draw_canceling_state(self, message: str = "CANCELLED"):
        """Draw glitch-out effect for canceling state."""
        if not self.canvas:
            return
            
        self.clear_canvas()
        self._draw_retro_background()
        
        # Get cancellation progress (0.0 to 1.0)
        progress = self.get_cancellation_progress()
        
        # Glitch effect that intensifies over time
        glitch_intensity = progress * 0.5
        
        # Calculate bar positions
        total_bar_width = self.bar_count * (self.bar_width + self.bar_spacing) - self.bar_spacing
        start_x = (self.width - total_bar_width) // 2
        
        # Draw glitching bars that progressively disappear
        for i in range(self.bar_count):
            x = start_x + i * (self.bar_width + self.bar_spacing)
            
            # Bars randomly disappear based on progress
            if random.random() < progress:
                continue
                
            # Use last known audio levels or create a decaying pattern
            if i < len(self.audio_levels) and len(self.audio_levels) > 0:
                level = self.audio_levels[i]
            else:
                level = max(0.0, 0.6 - (i * 0.03))
            
            # Add glitch displacement
            glitch_x_offset = int((random.random() - 0.5) * glitch_intensity * 20)
            glitch_y_offset = int((random.random() - 0.5) * glitch_intensity * 10)
            
            # Calculate bar height with decay
            decay_factor = 1.0 - (progress * 0.8)
            min_height = 8
            max_bar_height = self.height - 35
            bar_height = (min_height + level * max_bar_height) * decay_factor
            
            if bar_height <= 0:
                continue
            
            # Create stacked bar effect with glitching
            segments = int(bar_height / 6) + 1
            segment_height = 4
            segment_spacing = 2
            
            for seg in range(segments):
                # Some segments randomly disappear
                if random.random() < progress * 0.3:
                    continue
                    
                seg_y = self.height - 25 - (seg * (segment_height + segment_spacing)) + glitch_y_offset
                seg_x1 = x + glitch_x_offset
                seg_x2 = x + self.bar_width + glitch_x_offset
                seg_y1 = seg_y - segment_height
                seg_y2 = seg_y
                
                # Color shifts to red/pink as canceling progresses
                if seg < segments * 0.3:
                    base_color = self.neon_green
                elif seg < segments * 0.7:
                    base_color = self.neon_cyan
                else:
                    base_color = self.neon_pink
                
                # Fade toward red to indicate cancellation
                color = self.interpolate_color(base_color, "#ff0000", progress * 0.7)
                
                # Draw segment with flickering
                if random.random() > progress * 0.2:
                    self._draw_neon_rect(seg_x1, seg_y1, seg_x2, seg_y2, color)
        
        # Draw heavily scanlined overlay
        if self.scanlines_enabled:
            self._draw_scanlines()
            
            # Additional glitch scanlines
            for _ in range(int(progress * 10)):
                glitch_y = random.randint(0, self.height)
                glitch_color = random.choice([self.neon_pink, "#ff0000", "#ffffff"])
                self.canvas.create_line(
                    0, glitch_y, self.width, glitch_y,
                    fill=glitch_color, width=2
                )
        
        # Draw glitching text
        text_y = self.height - 12
        if random.random() > progress * 0.3:
            # Main text with increasing red tint
            text_color = self.interpolate_color(self.text_color, "#ff0000", progress)
            self._draw_retro_text(message, self.width // 2, text_y)
            
            # Additional glitch text copies
            if progress > 0.3:
                for _ in range(int(progress * 3)):
                    glitch_x = self.width // 2 + random.randint(-10, 10)
                    glitch_y = text_y + random.randint(-3, 3)
                    self.draw_text(message, glitch_x, glitch_y, "#ff0000", ("Courier", 8, "bold"))
    
    def draw_idle_state(self, message: str = ""):
        """Draw idle state with muted retro aesthetics."""
        if not self.canvas:
            return
            
        self.clear_canvas()
        
        # Only draw if we have a message
        if message:
            self._draw_retro_background()
            
            # Draw a subtle static neon indicator
            center_x = self.width // 2
            center_y = self.height // 2 - 5
            
            # Create a small static "terminal cursor" style indicator
            cursor_width = 8
            cursor_height = 12
            
            # Use muted neon color (darker version of neon_cyan)
            idle_color = self.interpolate_color(self.neon_cyan, self.bg_color, 0.6)
            
            # Draw static cursor rectangle
            self.canvas.create_rectangle(
                center_x - cursor_width // 2, center_y - cursor_height // 2,
                center_x + cursor_width // 2, center_y + cursor_height // 2,
                fill=idle_color, outline=""
            )
            
            # Add very subtle glow effect
            glow_color = self.interpolate_color(idle_color, self.bg_color, 0.5)
            self.canvas.create_rectangle(
                center_x - cursor_width // 2 - 1, center_y - cursor_height // 2 - 1,
                center_x + cursor_width // 2 + 1, center_y + cursor_height // 2 + 1,
                fill="", outline=glow_color, width=1
            )
            
            # Draw a few minimal static equalizer bars to maintain theme
            bar_count = 5
            bar_width = 4
            bar_spacing = 6
            bar_start_x = center_x - ((bar_count * (bar_width + bar_spacing)) // 2)
            
            for i in range(bar_count):
                x = bar_start_x + i * (bar_width + bar_spacing)
                # Static heights, no animation
                bar_height = 8 + (i % 3) * 4  # Vary heights slightly
                
                y1 = center_y + 15
                y2 = y1 + bar_height
                
                # Use even more muted colors
                muted_color = self.interpolate_color(self.neon_green, self.bg_color, 0.7)
                
                self.canvas.create_rectangle(
                    x, y1, x + bar_width, y2,
                    fill=muted_color, outline=""
                )
            
            # Draw subtle scanlines for retro feel
            if self.scanlines_enabled:
                self._draw_scanlines()
            
            # Draw retro text with muted styling
            self._draw_retro_text(message, self.width // 2, self.height - 12)
    
    def _draw_retro_background(self):
        """Draw retro-style background with gradient."""
        # Dark gradient background
        gradient_steps = 5
        for i in range(gradient_steps):
            y_start = (self.height * i) // gradient_steps
            y_end = (self.height * (i + 1)) // gradient_steps
            
            # Create gradient from dark to darker
            color_intensity = int(10 + (5 - i) * 3)
            bg_shade = f"#{color_intensity:02x}{color_intensity:02x}{color_intensity:02x}"
            
            self.canvas.create_rectangle(
                0, y_start, self.width, y_end,
                fill=bg_shade, outline=""
            )
        
        # Add subtle grid pattern
        grid_spacing = 20
        grid_color = "#222222"
        
        # Vertical grid lines
        for x in range(grid_spacing, self.width, grid_spacing):
            self.canvas.create_line(x, 0, x, self.height, fill=grid_color, width=1)
        
        # Horizontal grid lines
        for y in range(grid_spacing, self.height, grid_spacing):
            self.canvas.create_line(0, y, self.width, y, fill=grid_color, width=1)
    
    def _draw_scanlines(self):
        """Draw VHS-style scanlines."""
        scanline_spacing = 3
        scanline_offset = int(self.animation_time * self.scanline_speed) % (scanline_spacing * 2)
        
        for y in range(-scanline_offset, self.height + scanline_spacing, scanline_spacing):
            if 0 <= y < self.height:
                # Alternating scanline opacity
                opacity = 0.1 if (y // scanline_spacing) % 2 == 0 else 0.05
                scanline_color = "#ffffff" if opacity > 0.07 else "#888888"
                
                self.canvas.create_line(
                    0, y, self.width, y,
                    fill=scanline_color, width=1
                )
    
    def _draw_neon_rect(self, x1: int, y1: int, x2: int, y2: int, color: str):
        """Draw a rectangle with neon glow effect."""
        # Main rectangle
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
        
        # Glow effect
        if self.glow_intensity > 1.0:
            glow_color = self.interpolate_color(color, "#ffffff", 0.3)
            self.canvas.create_rectangle(
                x1 - 1, y1 - 1, x2 + 1, y2 + 1,
                fill="", outline=glow_color, width=1
            )
    
    def _draw_retro_text(self, text: str, x: int, y: int):
        """Draw text with retro styling and chromatic aberration."""
        # Main text
        self.draw_text(text, x, y, self.text_color, ("Courier", 8, "bold"))
        
        # Chromatic aberration effect
        if self.chromatic_aberration:
            # Red channel offset
            self.draw_text(text, x - 1, y, "#ff0080", ("Courier", 8, "bold"))
            # Cyan channel offset
            self.draw_text(text, x + 1, y, "#00ffff", ("Courier", 8, "bold"))
    
    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """Get default configuration for retro style."""
        return {
            'bar_count': 16,
            'bar_width': 10,
            'bar_spacing': 3,
            'bg_color': '#0a0a0a',
            'neon_pink': '#ff00ff',
            'neon_cyan': '#00ffff',
            'neon_purple': '#8000ff',
            'neon_green': '#00ff00',
            'text_color': '#ffffff',
            'grid_speed': 1.5,
            'scanline_speed': 8.0,
            'glitch_intensity': 0.05,
            'glow_intensity': 1.5,
            'chromatic_aberration': True,
            'scanlines_enabled': True,
            'vhs_noise': True
        }
    
    @classmethod
    def get_preview_config(cls) -> Dict[str, Any]:
        """Get configuration optimized for preview display."""
        config = cls.get_default_config()
        # Make preview more compact and faster
        config.update({
            'bar_count': 12,
            'bar_width': 8,
            'bar_spacing': 2,
            'grid_speed': 2.0,
            'scanline_speed': 10.0,
            'glow_intensity': 1.2
        })
        return config