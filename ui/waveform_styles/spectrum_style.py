"""
Spectrum Analyzer style - circular frequency display with rainbow colors.
"""
import math
from typing import Dict, Any, List
from .base_style import BaseWaveformStyle
from .style_factory import register_style


@register_style
class SpectrumStyle(BaseWaveformStyle):
    """Spectrum analyzer style with circular rainbow display."""
    
    def __init__(self, canvas, width: int, height: int, config: Dict[str, Any]):
        super().__init__(canvas, width, height, config)
        
        self._display_name = "Spectrum Analyzer"
        self._description = "Circular frequency spectrum with rainbow colors"
        
        # Style-specific settings
        self.spectrum_bars = config.get('spectrum_bars', 24)
        self.inner_radius = config.get('inner_radius', 25)
        self.outer_radius = config.get('outer_radius', 45)
        self.bar_width = config.get('bar_width', 4)
        
        # Colors and effects
        self.bg_color = config.get('bg_color', '#000000')
        self.center_color = config.get('center_color', '#ffffff')
        self.text_color = config.get('text_color', '#ffffff')
        self.use_rainbow = config.get('use_rainbow', True)
        self.rainbow_saturation = config.get('rainbow_saturation', 0.9)
        self.rainbow_brightness = config.get('rainbow_brightness', 1.0)
        
        # Animation settings
        self.rotation_speed = config.get('rotation_speed', 1.0)
        self.spiral_speed = config.get('spiral_speed', 2.0)
        self.pulse_speed = config.get('pulse_speed', 1.5)
        self.decay_rate = config.get('decay_rate', 0.95)
        
        # Spectrum processing
        self.spectrum_history: List[List[float]] = []
        self.max_history_length = 10
        
    def draw_recording_state(self, message: str = "Recording..."):
        """Draw circular spectrum analyzer."""
        if not self.canvas:
            return
            
        self.clear_canvas()
        self._draw_spectrum_background()
        
        center_x = self.width // 2
        center_y = self.height // 2 - 5
        
        # Update spectrum history for smooth transitions
        if len(self.audio_levels) > 0:
            # Resample audio levels to match spectrum bars
            resampled_levels = self._resample_levels(self.audio_levels, self.spectrum_bars)
            self.spectrum_history.append(resampled_levels)
        else:
            self.spectrum_history.append([0.0] * self.spectrum_bars)
        
        # Keep history length manageable
        if len(self.spectrum_history) > self.max_history_length:
            self.spectrum_history.pop(0)
        
        # Calculate average levels for smoothness
        current_levels = self._calculate_smooth_spectrum()
        
        # Draw circular spectrum bars
        for i in range(self.spectrum_bars):
            angle = (i / self.spectrum_bars) * 2 * math.pi
            angle += self.animation_time * self.rotation_speed  # Rotation effect
            
            level = current_levels[i] if i < len(current_levels) else 0.0
            
            # Calculate bar position
            inner_x = center_x + self.inner_radius * math.cos(angle)
            inner_y = center_y + self.inner_radius * math.sin(angle)
            
            # Bar length based on audio level
            bar_length = level * (self.outer_radius - self.inner_radius)
            outer_x = inner_x + bar_length * math.cos(angle)
            outer_y = inner_y + bar_length * math.sin(angle)
            
            # Color based on frequency (rainbow spectrum)
            if self.use_rainbow:
                hue = (i / self.spectrum_bars) * 360
                # Add some variation based on level
                hue += level * 30
                r, g, b = self.hsv_to_rgb(hue % 360, 
                                        self.rainbow_saturation, 
                                        self.rainbow_brightness * (0.5 + level * 0.5))
                color = self.rgb_to_hex(r, g, b)
            else:
                # Single color with intensity variation
                intensity = 0.3 + level * 0.7
                color = self.interpolate_color("#333333", "#ffffff", intensity)
            
            # Draw spectrum bar
            self.canvas.create_line(
                inner_x, inner_y, outer_x, outer_y,
                fill=color, width=self.bar_width, capstyle="round"
            )
            
            # Add glow effect for high levels
            if level > 0.7:
                glow_color = self.interpolate_color(color, "#ffffff", 0.3)
                self.canvas.create_line(
                    inner_x, inner_y, outer_x, outer_y,
                    fill=glow_color, width=1
                )
        
        # Draw center circle
        pulse_factor = 1.0 + 0.2 * math.sin(self.animation_time * self.pulse_speed)
        center_radius = 8 * pulse_factor
        
        self.canvas.create_oval(
            center_x - center_radius, center_y - center_radius,
            center_x + center_radius, center_y + center_radius,
            fill=self.center_color, outline=""
        )
        
        # Draw status text
        self.draw_text(message, self.width // 2, self.height - 15, self.text_color)
        
    def draw_processing_state(self, message: str = "Processing..."):
        """Draw rotating spectrum wheel."""
        if not self.canvas:
            return
            
        self.clear_canvas()
        self._draw_spectrum_background()
        
        center_x = self.width // 2
        center_y = self.height // 2 - 5
        
        # Rotating spectrum wheel
        wheel_segments = 16
        base_radius = 20
        
        for i in range(wheel_segments):
            angle = (i / wheel_segments) * 2 * math.pi
            angle += self.animation_time * self.spiral_speed
            
            # Create spiral effect
            radius = base_radius + 10 * math.sin(self.animation_time * 2 + i * 0.5)
            
            segment_x = center_x + radius * math.cos(angle)
            segment_y = center_y + radius * math.sin(angle)
            
            # Rainbow colors
            hue = (i / wheel_segments) * 360 + self.animation_time * 50
            r, g, b = self.hsv_to_rgb(hue % 360, 0.8, 1.0)
            color = self.rgb_to_hex(r, g, b)
            
            # Draw segment
            segment_size = 3 + 2 * math.sin(self.animation_time * 3 + i)
            self.canvas.create_oval(
                segment_x - segment_size, segment_y - segment_size,
                segment_x + segment_size, segment_y + segment_size,
                fill=color, outline=""
            )
        
        # Central pulsing core
        pulse = 1.0 + 0.3 * math.sin(self.animation_time * 4)
        core_radius = 6 * pulse
        
        self.canvas.create_oval(
            center_x - core_radius, center_y - core_radius,
            center_x + core_radius, center_y + core_radius,
            fill=self.center_color, outline=""
        )
        
        # Draw status text
        self.draw_text(message, self.width // 2, self.height - 15, self.text_color)
        
    def draw_transcribing_state(self, message: str = "Transcribing..."):
        """Draw spiraling spectrum animation."""
        if not self.canvas:
            return
            
        self.clear_canvas()
        self._draw_spectrum_background()
        
        center_x = self.width // 2
        center_y = self.height // 2 - 5
        
        # Spiraling spectrum animation
        spiral_arms = 3
        points_per_arm = 20
        
        for arm in range(spiral_arms):
            arm_offset = (arm / spiral_arms) * 2 * math.pi
            
            for point in range(points_per_arm):
                t = point / points_per_arm
                angle = arm_offset + t * 4 * math.pi + self.animation_time * self.spiral_speed
                radius = 10 + t * 30
                
                point_x = center_x + radius * math.cos(angle)
                point_y = center_y + radius * math.sin(angle)
                
                # Color based on position and time
                hue = (t * 360 + self.animation_time * 100 + arm * 120) % 360
                intensity = 1.0 - t * 0.3
                r, g, b = self.hsv_to_rgb(hue, 0.8, intensity)
                color = self.rgb_to_hex(r, g, b)
                
                # Size varies with position
                point_size = 2 + t * 3
                
                self.canvas.create_oval(
                    point_x - point_size, point_y - point_size,
                    point_x + point_size, point_y + point_size,
                    fill=color, outline=""
                )
        
        # Add frequency bands at bottom
        band_count = 8
        band_width = self.width // (band_count + 2)
        
        for i in range(band_count):
            x = (i + 1) * band_width
            
            # Simulate frequency activity
            freq_activity = abs(math.sin(self.animation_time * 3 + i * 0.8)) * 0.7 + 0.3
            band_height = freq_activity * 20
            
            # Rainbow color for frequency band
            hue = (i / band_count) * 360
            r, g, b = self.hsv_to_rgb(hue, 0.7, 1.0)
            color = self.rgb_to_hex(r, g, b)
            
            self.canvas.create_rectangle(
                x - 3, self.height - 25,
                x + 3, self.height - 25 - band_height,
                fill=color, outline=""
            )
        
        # Central core
        core_pulse = 1.0 + 0.2 * math.sin(self.animation_time * 5)
        core_radius = 4 * core_pulse
        
        self.canvas.create_oval(
            center_x - core_radius, center_y - core_radius,
            center_x + core_radius, center_y + core_radius,
            fill=self.center_color, outline=""
        )
        
        # Draw status text
        self.draw_text(message, self.width // 2, self.height - 15, self.text_color)
    
    def _draw_spectrum_background(self):
        """Draw spectrum analyzer background."""
        # Dark background
        self.canvas.create_rectangle(
            0, 0, self.width, self.height,
            fill=self.bg_color, outline=""
        )
        
        # Optional: Add radial grid
        center_x = self.width // 2
        center_y = self.height // 2 - 5
        
        # Concentric circles
        for radius in [15, 30, 45]:
            self.canvas.create_oval(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                fill="", outline="#222222", width=1
            )
        
        # Radial lines
        for i in range(8):
            angle = (i / 8) * 2 * math.pi
            end_x = center_x + 50 * math.cos(angle)
            end_y = center_y + 50 * math.sin(angle)
            
            self.canvas.create_line(
                center_x, center_y, end_x, end_y,
                fill="#222222", width=1
            )
    
    def _resample_levels(self, levels: List[float], target_count: int) -> List[float]:
        """Resample audio levels to match spectrum bar count."""
        if not levels:
            return [0.0] * target_count
        
        if len(levels) == target_count:
            return levels.copy()
        
        # Simple linear interpolation resampling
        resampled = []
        for i in range(target_count):
            # Calculate source position
            src_pos = (i / target_count) * len(levels)
            src_idx = int(src_pos)
            
            if src_idx >= len(levels) - 1:
                resampled.append(levels[-1])
            else:
                # Linear interpolation
                t = src_pos - src_idx
                value = levels[src_idx] * (1 - t) + levels[src_idx + 1] * t
                resampled.append(value)
        
        return resampled
    
    def _calculate_smooth_spectrum(self) -> List[float]:
        """Calculate smooth spectrum from history."""
        if not self.spectrum_history:
            return [0.0] * self.spectrum_bars
        
        # Average recent history for smoothness
        avg_spectrum = [0.0] * self.spectrum_bars
        
        for i, levels in enumerate(self.spectrum_history):
            weight = (i + 1) / len(self.spectrum_history)  # More weight to recent
            for j, level in enumerate(levels):
                if j < len(avg_spectrum):
                    avg_spectrum[j] += level * weight
        
        # Normalize
        total_weight = sum(range(1, len(self.spectrum_history) + 1))
        if total_weight > 0:
            for i in range(len(avg_spectrum)):
                avg_spectrum[i] /= total_weight
        
        return avg_spectrum
    
    def draw_idle_state(self, message: str = ""):
        """Draw minimal static spectrum for idle state."""
        if not self.canvas:
            return
            
        self.clear_canvas()
        
        # Only draw if we have a message
        if message:
            self._draw_spectrum_background()
            
            center_x = self.width // 2
            center_y = self.height // 2 - 5
            
            # Draw static spectrum bars with very low levels
            static_spectrum_count = 12  # Fewer bars for idle state
            
            for i in range(static_spectrum_count):
                angle = (i / static_spectrum_count) * 2 * math.pi
                
                # Static low level pattern
                level = 0.15 + 0.1 * math.sin(i * 0.8)  # Static pattern, no animation
                level = max(0.05, min(0.25, level))  # Keep levels very low
                
                # Calculate bar position
                inner_x = center_x + self.inner_radius * math.cos(angle)
                inner_y = center_y + self.inner_radius * math.sin(angle)
                
                # Bar length is much shorter for idle state
                bar_length = level * (self.outer_radius - self.inner_radius) * 0.6
                outer_x = inner_x + bar_length * math.cos(angle)
                outer_y = inner_y + bar_length * math.sin(angle)
                
                # Use very muted colors for idle
                if self.use_rainbow:
                    hue = (i / static_spectrum_count) * 360
                    r, g, b = self.hsv_to_rgb(hue % 360, 
                                            self.rainbow_saturation * 0.3,  # Much lower saturation
                                            self.rainbow_brightness * 0.4)  # Much lower brightness
                    color = self.rgb_to_hex(r, g, b)
                else:
                    # Very muted single color
                    intensity = 0.2
                    color = self.interpolate_color("#333333", "#666666", intensity)
                
                # Draw thin spectrum bar
                self.canvas.create_line(
                    inner_x, inner_y, outer_x, outer_y,
                    fill=color, width=self.bar_width // 2, capstyle="round"
                )
            
            # Draw center dot
            self.canvas.create_oval(
                center_x - 2, center_y - 2, center_x + 2, center_y + 2,
                fill=self.interpolate_color(self.center_color, self.bg_color, 0.5), 
                outline=""
            )
            
            # Draw status text
            self.draw_text(message, self.width // 2, self.height - 15, self.text_color)
    
    def draw_canceling_state(self, message: str = "Cancelled"):
        """Draw spectrum collapse animation for canceling state."""
        if not self.canvas:
            return
            
        self.clear_canvas()
        self._draw_background()
        
        # Get cancellation progress (0.0 to 1.0)
        progress = self.get_cancellation_progress()
        
        # Calculate center position
        center_x = self.width // 2
        center_y = (self.height // 2) - 5
        
        # Collapsing effect - spectrum bars shrink toward center
        collapse_factor = 1.0 - progress
        
        # Draw collapsing spectrum
        for i in range(self.spectrum_bars):
            # Use last known audio levels or create a pattern
            if i < len(self.audio_levels) and len(self.audio_levels) > 0:
                level = self.audio_levels[i]
            else:
                level = max(0.0, 0.5 - (abs(i - self.spectrum_bars//2) * 0.05))
            
            # Calculate angle for this bar
            angle = (i / self.spectrum_bars) * 2 * math.pi
            
            # Apply collapse effect to radius
            inner_radius = self.inner_radius * collapse_factor
            bar_length = level * (self.outer_radius - self.inner_radius) * collapse_factor
            outer_radius = inner_radius + bar_length
            
            if outer_radius <= inner_radius:
                continue
            
            # Calculate positions
            inner_x = center_x + math.cos(angle) * inner_radius
            inner_y = center_y + math.sin(angle) * inner_radius
            outer_x = center_x + math.cos(angle) * outer_radius
            outer_y = center_y + math.sin(angle) * outer_radius
            
            # Color that fades to dark red
            if self.use_rainbow:
                hue = (i / self.spectrum_bars) * 360
                r, g, b = self.hsv_to_rgb(hue, self.rainbow_saturation, self.rainbow_brightness)
                base_color = f"#{r:02x}{g:02x}{b:02x}"
            else:
                base_color = self.center_color
            
            # Fade toward dark red/black
            color = self.interpolate_color(base_color, "#330000", progress * 0.8)
            
            # Draw collapsing bar
            bar_thickness = max(1, int(self.bar_width * collapse_factor))
            self.canvas.create_line(
                inner_x, inner_y, outer_x, outer_y,
                fill=color, width=bar_thickness
            )
        
        # Draw central collapsing dot
        dot_radius = int(self.inner_radius * collapse_factor * 0.3)
        if dot_radius > 0:
            dot_color = self.interpolate_color(self.center_color, "#000000", progress)
            self.canvas.create_oval(
                center_x - dot_radius, center_y - dot_radius,
                center_x + dot_radius, center_y + dot_radius,
                fill=dot_color, outline=""
            )
        
        # Draw fading text
        text_color = self.interpolate_color(self.text_color, "#000000", progress * 0.7)
        self.draw_text(message, center_x, self.height - 12, text_color)
    
    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """Get default configuration for spectrum style."""
        return {
            'spectrum_bars': 24,
            'inner_radius': 25,
            'outer_radius': 45,
            'bar_width': 4,
            'bg_color': '#000000',
            'center_color': '#ffffff',
            'text_color': '#ffffff',
            'use_rainbow': True,
            'rainbow_saturation': 0.9,
            'rainbow_brightness': 1.0,
            'rotation_speed': 1.0,
            'spiral_speed': 2.0,
            'pulse_speed': 1.5,
            'decay_rate': 0.95
        }
    
    @classmethod
    def get_preview_config(cls) -> Dict[str, Any]:
        """Get configuration optimized for preview display."""
        config = cls.get_default_config()
        # Make preview more compact and faster
        config.update({
            'spectrum_bars': 16,
            'inner_radius': 20,
            'outer_radius': 35,
            'bar_width': 3,
            'rotation_speed': 1.5,
            'spiral_speed': 3.0,
            'pulse_speed': 2.0
        })
        return config