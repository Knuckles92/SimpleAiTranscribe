"""
Loading screen UI component for the Audio Recorder application.
Now features a modern animated loader for a more delightful startup experience.
"""
import tkinter as tk
from tkinter import ttk
from config import config
import math
import time


class LoadingScreen:
    """Manages the loading screen display during application startup."""
    
    def __init__(self):
        """Initialize the loading screen."""
        self.root = None
        self.status_label = None
        self.canvas = None
        self._anim_job = None
        self._start_time = time.time()
        # Animation parameters
        self._dot_count = 28
        self._base_radius = 34
        self._pulse_amp = 10
        self._spin_speed = 1.6  # rotations per second
        self._pulse_speed = 1.2  # pulses per second
        self._min_dot = 2
        self._max_dot = 6
        self._accent = config.WAVEFORM_ACCENT_COLOR
        self._secondary = config.WAVEFORM_SECONDARY_COLOR
        self._ui_created = False
    
    def _create_loading_screen(self):
        """Create and display the loading screen."""
        self.root = tk.Tk()
        self.root.title("Audio Recorder")
        self.root.geometry(config.LOADING_WINDOW_SIZE)
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)
        
        # Use dark theme consistent with waveform overlay
        bg_color = config.WAVEFORM_BG_COLOR
        text_primary = "#e6e6e6"
        text_secondary = "#b0b0b0"
        self.root.configure(bg=bg_color)
        
        # Center the loading screen
        self.root.eval('tk::PlaceWindow . center')
        
        # Force the window to appear immediately
        self.root.update_idletasks()
        self.root.deiconify()
        self.root.lift()
        self.root.update()
        
        # Create main frame
        main_frame = tk.Frame(self.root, bg=bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # App title
        title_label = tk.Label(
            main_frame,
            text="Audio Recorder",
            font=("Segoe UI", 16, "bold"),
            bg=bg_color,
            fg=self._accent,
        )
        title_label.pack(pady=(0, 20))
        
        # Animated canvas loader
        canvas_wrapper = tk.Frame(main_frame, bg=bg_color)
        canvas_wrapper.pack(fill=tk.BOTH, expand=False)
        self.canvas = tk.Canvas(canvas_wrapper, width=260, height=110, bg=bg_color, highlightthickness=0)
        self.canvas.pack()

        # Loading status label
        self.status_label = tk.Label(
            main_frame,
            text="Initializing application...",
            font=("Segoe UI", 10),
            bg=bg_color,
            fg=text_secondary,
        )
        self.status_label.pack(pady=(12, 0))
        
        # Version or additional info
        info_label = tk.Label(
            main_frame,
            text="Please wait while components load...",
            font=("Segoe UI", 8),
            bg=bg_color,
            fg=text_secondary,
        )
        info_label.pack()
        
        # Final update to make everything visible
        self.root.update()
        self._start_animation()
    
    def update_status(self, status_text: str):
        """Update the loading screen status text.
        
        Args:
            status_text: New status text to display.
        """
        if self.status_label and self.root:
            self.status_label.config(text=status_text)
            self.root.update()
    
    def show(self):
        """Show the loading screen."""
        if not self._ui_created:
            self._create_loading_screen()
            self._ui_created = True
        if self.root:
            self.root.deiconify()
            self.root.lift()
            self.root.attributes('-topmost', True)
            self.root.update()
    
    def hide(self):
        """Hide the loading screen."""
        if self.root:
            self.root.withdraw()
    
    def destroy(self):
        """Destroy the loading screen."""
        if self.root:
            self._stop_animation()
            self.root.destroy()
            self.root = None
            self.status_label = None
            self.canvas = None
    
    def is_visible(self) -> bool:
        """Check if the loading screen is visible.
        
        Returns:
            True if visible, False otherwise.
        """
        return self.root is not None and self._ui_created and self.root.winfo_viewable()

    # --- Animation helpers ---
    def _hex_to_rgb(self, hex_color: str):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(self, rgb):
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    def _interpolate_color(self, c1: str, c2: str, t: float) -> str:
        t = max(0.0, min(1.0, t))
        r1, g1, b1 = self._hex_to_rgb(c1)
        r2, g2, b2 = self._hex_to_rgb(c2)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        return self._rgb_to_hex((r, g, b))

    def _start_animation(self):
        if self._anim_job is None and self.canvas is not None:
            self._anim_job = self.root.after(0, self._animate)

    def _stop_animation(self):
        if self._anim_job is not None and self.root is not None:
            try:
                self.root.after_cancel(self._anim_job)
            except Exception:
                pass
        self._anim_job = None

    def _draw_orbit_loader(self, t: float):
        if not self.canvas:
            return
        w = int(self.canvas['width'])
        h = int(self.canvas['height'])
        cx, cy = w // 2, h // 2

        # Clear and draw subtle center glow
        self.canvas.delete("all")

        # Outer pulsing ring
        pulse = self._pulse_amp * (0.5 + 0.5 * math.sin(2 * math.pi * self._pulse_speed * t))
        radius = self._base_radius + pulse

        # Draw orbiting dots
        for i in range(self._dot_count):
            phase = (i / self._dot_count)
            angle = 2 * math.pi * (phase + self._spin_speed * t)
            r = radius * (0.92 + 0.08 * math.sin(2 * math.pi * (self._pulse_speed * t + phase)))
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            size = self._min_dot + (self._max_dot - self._min_dot) * (0.5 + 0.5 * math.sin(2 * math.pi * (self._pulse_speed * t + phase)))
            color_t = 0.5 + 0.5 * math.sin(2 * math.pi * (phase + t * 0.5))
            color = self._interpolate_color(self._secondary, self._accent, color_t)

            # Soft outline ring (fake glow without alpha)
            self.canvas.create_oval(
                x - size - 1,
                y - size - 1,
                x + size + 1,
                y + size + 1,
                outline=self._interpolate_color(self._secondary, color, 0.3),
                width=2,
            )
            # Core dot
            self.canvas.create_oval(
                x - size,
                y - size,
                x + size,
                y + size,
                fill=color,
                outline="",
            )

        # Center text badge
        badge_w, badge_h = 110, 28
        badge_color = self._interpolate_color(self._secondary, self._accent, 0.35)
        self.canvas.create_rectangle(
            cx - badge_w // 2,
            cy - badge_h // 2,
            cx + badge_w // 2,
            cy + badge_h // 2,
            outline=badge_color,
            width=2,
        )
        self.canvas.create_text(cx, cy, text="Loading", fill="#e6e6e6", font=("Segoe UI", 10, "bold"))

    def _animate(self):
        if not self.root or not self.canvas:
            return
        t = time.time() - self._start_time
        try:
            self._draw_orbit_loader(t)
        finally:
            # Aim for ~60 FPS
            self._anim_job = self.root.after(16, self._animate)