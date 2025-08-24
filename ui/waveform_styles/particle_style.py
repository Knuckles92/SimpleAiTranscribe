"""
Particle Storm style - physics-based particles that respond to audio levels.
"""
import math
import random
from typing import Dict, Any, List, Tuple
from .base_style import BaseWaveformStyle
from .style_factory import register_style


class Particle:
    """Individual particle with physics properties."""
    
    def __init__(self, x: float, y: float, vx: float = 0, vy: float = 0):
        self.x = x
        self.y = y
        self.vx = vx  # velocity x
        self.vy = vy  # velocity y
        self.life = 1.0  # life from 1.0 to 0.0
        self.max_life = 1.0
        self.size = random.uniform(1.5, 4.0)
        self.color_hue = random.uniform(0, 360)
        self.birth_time = 0
        
    def update(self, dt: float, gravity: float = 0, damping: float = 0.99):
        """Update particle physics."""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += gravity * dt
        
        # Apply damping
        self.vx *= damping
        self.vy *= damping
        
        # Reduce life
        self.life -= dt * 0.5
        return self.life > 0
    
    def get_color(self, base_hue: float = None) -> Tuple[int, int, int]:
        """Get particle color based on life and properties."""
        hue = base_hue if base_hue is not None else self.color_hue
        saturation = 0.8
        brightness = self.life * 0.9 + 0.1
        
        # Convert HSV to RGB
        h = hue / 60.0
        c = brightness * saturation
        x = c * (1 - abs(h % 2 - 1))
        m = brightness - c
        
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


@register_style
class ParticleStyle(BaseWaveformStyle):
    """Particle storm style with physics-based particles."""
    
    def __init__(self, canvas, width: int, height: int, config: Dict[str, Any]):
        super().__init__(canvas, width, height, config)
        
        self._display_name = "Particle Storm"
        self._description = "Physics-based particles responding to audio"
        
        # Particle system settings
        self.max_particles = config.get('max_particles', 150)
        self.emission_rate = config.get('emission_rate', 30)  # particles per second
        self.particle_life = config.get('particle_life', 2.0)
        
        # Physics settings
        self.gravity = config.get('gravity', 20)
        self.damping = config.get('damping', 0.98)
        self.wind_strength = config.get('wind_strength', 5)
        self.audio_response = config.get('audio_response', 1.5)
        
        # Visual settings
        self.bg_color = config.get('bg_color', '#0a0a0a')
        self.text_color = config.get('text_color', '#ffffff')
        self.particle_trail = config.get('particle_trail', True)
        self.glow_effect = config.get('glow_effect', True)
        
        # Animation settings
        self.turbulence_strength = config.get('turbulence_strength', 10)
        self.color_shift_speed = config.get('color_shift_speed', 50)
        
        # Particle system state
        self.particles: List[Particle] = []
        self.emission_timer = 0.0
        self.last_frame_time = 0
        
    def draw_recording_state(self, message: str = "Recording..."):
        """Draw particles responding to audio levels."""
        if not self.canvas:
            return
            
        current_time = self.animation_time
        dt = current_time - self.last_frame_time if self.last_frame_time > 0 else 1/30
        self.last_frame_time = current_time
        
        self.clear_canvas()
        self._draw_particle_background()
        
        # Calculate audio energy for particle emission
        audio_energy = sum(self.audio_levels) / len(self.audio_levels) if self.audio_levels else 0.0
        
        # Emit new particles based on audio
        emission_multiplier = 1.0 + audio_energy * self.audio_response
        particles_to_emit = int(self.emission_rate * emission_multiplier * dt)
        
        self._emit_audio_particles(particles_to_emit, audio_energy)
        
        # Update and draw particles
        self._update_particles(dt, audio_energy)
        self._draw_particles()
        
        # Draw audio level indicators
        self._draw_audio_indicators(message)
        
    def draw_processing_state(self, message: str = "Processing..."):
        """Draw swirling particle vortex."""
        if not self.canvas:
            return
            
        current_time = self.animation_time
        dt = current_time - self.last_frame_time if self.last_frame_time > 0 else 1/30
        self.last_frame_time = current_time
        
        self.clear_canvas()
        self._draw_particle_background()
        
        # Emit particles in a vortex pattern
        center_x = self.width // 2
        center_y = self.height // 2 - 5
        
        vortex_particles = 5
        for i in range(vortex_particles):
            angle = (i / vortex_particles) * 2 * math.pi + self.animation_time * 2
            radius = 30 + 10 * math.sin(self.animation_time * 3)
            
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            
            # Velocity tangent to circle (vortex motion)
            vx = -math.sin(angle) * 50
            vy = math.cos(angle) * 50
            
            particle = Particle(x, y, vx, vy)
            particle.color_hue = (angle * 180 / math.pi + self.animation_time * 50) % 360
            self.particles.append(particle)
        
        # Update and draw particles
        self._update_particles(dt, 0.5, vortex_mode=True)
        self._draw_particles()
        
        # Draw central core
        pulse = 1.0 + 0.3 * math.sin(self.animation_time * 4)
        core_radius = 6 * pulse
        
        self.canvas.create_oval(
            center_x - core_radius, center_y - core_radius,
            center_x + core_radius, center_y + core_radius,
            fill="#4444ff", outline=""
        )
        
        self.draw_text(message, self.width // 2, self.height - 15, self.text_color)
        
    def draw_transcribing_state(self, message: str = "Transcribing..."):
        """Draw particle streams flowing across screen."""
        if not self.canvas:
            return
            
        current_time = self.animation_time
        dt = current_time - self.last_frame_time if self.last_frame_time > 0 else 1/30
        self.last_frame_time = current_time
        
        self.clear_canvas()
        self._draw_particle_background()
        
        # Emit particles in streams
        stream_count = 3
        for stream in range(stream_count):
            stream_y = (self.height / (stream_count + 1)) * (stream + 1) - 10
            
            # Emit particles from left side
            if random.random() < 0.8:  # 80% chance per frame
                x = -5
                y = stream_y + random.uniform(-10, 10)
                vx = random.uniform(80, 120)
                vy = random.uniform(-20, 20)
                
                particle = Particle(x, y, vx, vy)
                particle.color_hue = (stream * 120 + self.animation_time * 30) % 360
                self.particles.append(particle)
        
        # Add occasional burst particles
        if random.random() < 0.1:  # 10% chance for burst
            center_x = self.width // 2
            center_y = self.height // 2
            
            burst_particles = 10
            for i in range(burst_particles):
                angle = (i / burst_particles) * 2 * math.pi
                speed = random.uniform(30, 60)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                
                particle = Particle(center_x, center_y, vx, vy)
                particle.color_hue = random.uniform(200, 300)  # Blue-purple range
                self.particles.append(particle)
        
        # Update and draw particles
        self._update_particles(dt, 0.3, stream_mode=True)
        self._draw_particles()
        
        self.draw_text(message, self.width // 2, self.height - 15, self.text_color)
    
    def _emit_audio_particles(self, count: int, audio_energy: float):
        """Emit particles based on audio energy."""
        for _ in range(min(count, self.max_particles - len(self.particles))):
            # Emit from bottom with upward velocity
            x = random.uniform(20, self.width - 20)
            y = self.height - 30
            
            # Velocity based on audio energy
            vx = random.uniform(-30, 30) * (1 + audio_energy)
            vy = random.uniform(-80, -40) * (1 + audio_energy * 0.5)
            
            particle = Particle(x, y, vx, vy)
            particle.color_hue = (self.animation_time * self.color_shift_speed + 
                                random.uniform(0, 60)) % 360
            self.particles.append(particle)
    
    def _update_particles(self, dt: float, audio_energy: float = 0.0, 
                         vortex_mode: bool = False, stream_mode: bool = False):
        """Update all particles with physics."""
        center_x = self.width // 2
        center_y = self.height // 2
        
        # Remove dead particles and update living ones
        alive_particles = []
        
        for particle in self.particles:
            # Apply different forces based on mode
            if vortex_mode:
                # Vortex forces
                dx = particle.x - center_x
                dy = particle.y - center_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance > 0:
                    # Radial force (toward center)
                    radial_force = -50 / (distance + 1)
                    particle.vx += (dx / distance) * radial_force * dt
                    particle.vy += (dy / distance) * radial_force * dt
                    
                    # Tangential force (swirling)
                    tangent_force = 100
                    particle.vx += (-dy / distance) * tangent_force * dt
                    particle.vy += (dx / distance) * tangent_force * dt
                
                if particle.update(dt, 0, 0.95):
                    alive_particles.append(particle)
                    
            elif stream_mode:
                # Stream mode - particles flow horizontally with slight turbulence
                turbulence_x = math.sin(self.animation_time * 2 + particle.y * 0.1) * self.turbulence_strength
                turbulence_y = math.cos(self.animation_time * 1.5 + particle.x * 0.1) * self.turbulence_strength * 0.5
                
                particle.vx += turbulence_x * dt
                particle.vy += turbulence_y * dt
                
                # Remove particles that go off screen
                if (particle.x < -10 or particle.x > self.width + 10 or 
                    particle.y < -10 or particle.y > self.height + 10):
                    continue
                    
                if particle.update(dt, self.gravity * 0.3, self.damping):
                    alive_particles.append(particle)
                    
            else:
                # Normal audio-responsive mode
                # Add turbulence based on audio energy
                turbulence_multiplier = 1.0 + audio_energy * 2
                turbulence_x = (math.sin(self.animation_time * 3 + particle.x * 0.1) * 
                              self.turbulence_strength * turbulence_multiplier)
                turbulence_y = (math.cos(self.animation_time * 2.5 + particle.y * 0.1) * 
                              self.turbulence_strength * turbulence_multiplier * 0.7)
                
                particle.vx += turbulence_x * dt
                particle.vy += turbulence_y * dt
                
                # Wind effect
                wind_x = math.sin(self.animation_time) * self.wind_strength
                particle.vx += wind_x * dt
                
                # Boundary collision (bounce)
                if particle.x <= 0 or particle.x >= self.width:
                    particle.vx *= -0.8
                    particle.x = max(0, min(self.width, particle.x))
                
                if particle.y >= self.height - 25:
                    particle.vy *= -0.6
                    particle.y = self.height - 25
                
                if particle.update(dt, self.gravity, self.damping):
                    alive_particles.append(particle)
        
        self.particles = alive_particles
        
        # Limit particle count
        if len(self.particles) > self.max_particles:
            self.particles = self.particles[-self.max_particles:]
    
    def _draw_particles(self):
        """Draw all particles with effects."""
        for particle in self.particles:
            # Get particle color
            r, g, b = particle.get_color()
            color = self.rgb_to_hex(r, g, b)
            
            # Calculate particle size based on life
            size = particle.size * particle.life
            
            # Draw particle
            self.canvas.create_oval(
                particle.x - size, particle.y - size,
                particle.x + size, particle.y + size,
                fill=color, outline=""
            )
            
            # Add glow effect for bright particles
            if self.glow_effect and particle.life > 0.5:
                glow_size = size + 1
                glow_color = self.interpolate_color(color, "#ffffff", 0.3)
                self.canvas.create_oval(
                    particle.x - glow_size, particle.y - glow_size,
                    particle.x + glow_size, particle.y + glow_size,
                    fill="", outline=glow_color, width=1
                )
    
    def _draw_particle_background(self):
        """Draw background for particle system."""
        # Dark gradient background
        gradient_steps = 3
        for i in range(gradient_steps):
            y_start = (self.height * i) // gradient_steps
            y_end = (self.height * (i + 1)) // gradient_steps
            
            darkness = int(10 + i * 5)
            bg_shade = f"#{darkness:02x}{darkness:02x}{darkness:02x}"
            
            self.canvas.create_rectangle(
                0, y_start, self.width, y_end,
                fill=bg_shade, outline=""
            )
    
    def _draw_audio_indicators(self, message: str):
        """Draw audio level indicators."""
        if self.audio_levels:
            # Draw mini spectrum at bottom
            indicator_count = min(len(self.audio_levels), 10)
            indicator_width = self.width // (indicator_count + 2)
            
            for i in range(indicator_count):
                x = (i + 1) * indicator_width
                level = self.audio_levels[i * len(self.audio_levels) // indicator_count]
                
                indicator_height = level * 15
                hue = (i / indicator_count) * 240  # Blue to red range
                r, g, b = self.hsv_to_rgb(hue, 0.8, 1.0)
                color = self.rgb_to_hex(r, g, b)
                
                self.canvas.create_rectangle(
                    x - 2, self.height - 25,
                    x + 2, self.height - 25 - indicator_height,
                    fill=color, outline=""
                )
        
        self.draw_text(message, self.width // 2, self.height - 15, self.text_color)
    
    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """Get default configuration for particle style."""
        return {
            'max_particles': 150,
            'emission_rate': 30,
            'particle_life': 2.0,
            'gravity': 20,
            'damping': 0.98,
            'wind_strength': 5,
            'audio_response': 1.5,
            'bg_color': '#0a0a0a',
            'text_color': '#ffffff',
            'particle_trail': True,
            'glow_effect': True,
            'turbulence_strength': 10,
            'color_shift_speed': 50
        }
    
    @classmethod
    def get_preview_config(cls) -> Dict[str, Any]:
        """Get configuration optimized for preview display."""
        config = cls.get_default_config()
        # Make preview less intensive
        config.update({
            'max_particles': 80,
            'emission_rate': 20,
            'particle_life': 1.5,
            'gravity': 15,
            'turbulence_strength': 8,
            'color_shift_speed': 70
        })
        return config