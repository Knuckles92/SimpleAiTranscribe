"""
Waveform style configuration dialog for the Audio Recorder application.
Shows live previews of all available waveform styles in a grid layout.
"""
import tkinter as tk
from tkinter import messagebox, ttk
import math
import random
import time
from typing import Dict, Optional, List
from config import config
from settings import settings_manager
from ui.waveform_styles.style_factory import WaveformStyleFactory
from ui.waveform_styles.base_style import BaseWaveformStyle


class WaveformStyleDialog:
    """Dialog for configuring waveform style with live previews."""
    
    def __init__(self, parent, current_style: str = "particle", current_config: Dict = None):
        """Initialize the waveform style dialog.
        
        Args:
            parent: Parent window.
            current_style: Currently selected style name.
            current_config: Current style configurations.
        """
        self.parent = parent
        self.current_style = current_style
        self.selected_style = current_style
        self.current_config = current_config or {}
        self.dialog: Optional[tk.Toplevel] = None
        
        # Animation state
        self.animation_running = False
        self.animation_job = None
        self.animation_start_time = time.time()
        
        # Preview canvases and styles
        self.preview_canvases: Dict[str, tk.Canvas] = {}
        self.preview_styles: Dict[str, BaseWaveformStyle] = {}
        self.preview_frames: Dict[str, tk.Frame] = {}
        self.select_buttons: Dict[str, tk.Button] = {}
        
        # Preview settings
        self.preview_width = 150
        self.preview_height = 60
        
        # Get available styles info
        self.available_styles = WaveformStyleFactory.get_available_styles()
        self.style_info = {}
        for style_name in self.available_styles:
            self.style_info[style_name] = WaveformStyleFactory.get_style_info(style_name)
    
    def show(self):
        """Show the waveform style configuration dialog."""
        self._create_dialog()
        self._setup_dialog_content()
        self._initialize_previews()
        self._start_animation()
        self.dialog.grab_set()
        self.dialog.transient(self.parent)
        self.dialog.focus_set()
    
    def _create_dialog(self):
        """Create the dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Choose Waveform Style")
        # Adaptive sizing based on screen
        screen_w = self.parent.winfo_screenwidth()
        screen_h = self.parent.winfo_screenheight()
        width = min(900, max(600, screen_w - 120))
        height = min(700, max(420, screen_h - 160))
        self.dialog.geometry(f"{width}x{height}")
        self.dialog.minsize(600, 420)
        self.dialog.resizable(True, True)
        
        # Center the dialog
        self._center_dialog(width, height)
        
        # Handle close event
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        # Keyboard shortcuts
        self.dialog.bind("<Escape>", lambda e: self._on_cancel())
        self.dialog.bind("<Return>", lambda e: self._on_apply())
    
    def _center_dialog(self, width: int, height: int):
        """Center the dialog within the screen bounds."""
        try:
            screen_w = self.parent.winfo_screenwidth()
            screen_h = self.parent.winfo_screenheight()
            x = max(0, (screen_w - width) // 2)
            y = max(0, (screen_h - height) // 3)
            self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            # Fallback to small offset from parent
            x = self.parent.winfo_rootx() + 50
            y = self.parent.winfo_rooty() + 50
            self.dialog.geometry(f"+{x}+{y}")
    
    def _setup_dialog_content(self):
        """Setup the dialog content."""
        # Main container
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="Choose Waveform Style", 
                              font=('TkDefaultFont', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Subtitle
        subtitle_label = tk.Label(main_frame, 
                                 text="Select a waveform visualization style for the overlay", 
                                 font=('TkDefaultFont', 10))
        subtitle_label.pack(pady=(0, 20))
        
        # Create scrollable frame for styles
        self._create_styles_grid(main_frame)
        
        # Instructions
        self._create_instructions(main_frame)
        
        # Buttons
        self._create_buttons(main_frame)
    
    def _create_styles_grid(self, parent):
        """Create the grid of style previews.
        
        Args:
            parent: Parent widget for the grid.
        """
        # Create canvas and scrollbar for scrolling
        canvas_frame = tk.Frame(parent)
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Let canvas expand; height is initial hint only
        canvas = tk.Canvas(canvas_frame, height=400, bg='#f0f0f0', highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mouse wheel support (scoped to canvas only)
        def _on_mousewheel(event):
            delta = 0
            if hasattr(event, 'delta') and event.delta:
                delta = int(-1 * (event.delta / 120))
            elif getattr(event, 'num', None) == 5:
                delta = 1
            elif getattr(event, 'num', None) == 4:
                delta = -1
            canvas.yview_scroll(delta, "units")

        # Bind to the canvas and also support Linux button events
        canvas.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Button-4>", _on_mousewheel)
        canvas.bind("<Button-5>", _on_mousewheel)
        
        # Grid configuration
        cols = 3 if len(self.available_styles) > 3 else len(self.available_styles)
        rows = (len(self.available_styles) + cols - 1) // cols
        
        # Create style preview widgets
        for idx, style_name in enumerate(sorted(self.available_styles)):
            row = idx // cols
            col = idx % cols
            
            self._create_style_preview(scrollable_frame, style_name, row, col)
        
        # Configure grid weights
        for col in range(cols):
            scrollable_frame.columnconfigure(col, weight=1)
    
    def _create_style_preview(self, parent, style_name: str, row: int, col: int):
        """Create a preview widget for a specific style.
        
        Args:
            parent: Parent widget.
            style_name: Name of the style.
            row: Grid row position.
            col: Grid column position.
        """
        # Main frame for this style
        style_frame = tk.Frame(parent, relief=tk.RAISED, borderwidth=2, padx=10, pady=10)
        style_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        self.preview_frames[style_name] = style_frame
        
        # Style info
        info = self.style_info[style_name]
        
        # Title
        title_label = tk.Label(style_frame, text=info['display_name'], 
                              font=('TkDefaultFont', 12, 'bold'))
        title_label.pack(pady=(0, 5))
        
        # Description
        desc_label = tk.Label(style_frame, text=info['description'], 
                             font=('TkDefaultFont', 9), 
                             wraplength=self.preview_width, 
                             justify=tk.CENTER)
        desc_label.pack(pady=(0, 10))
        
        # Preview canvas
        canvas = tk.Canvas(style_frame, 
                          width=self.preview_width, 
                          height=self.preview_height,
                          bg='black', 
                          relief=tk.SUNKEN, 
                          borderwidth=2)
        canvas.pack(pady=(0, 10))
        self.preview_canvases[style_name] = canvas
        
        # Select button (select = apply immediately, keep dialog open)
        is_current = style_name == self.current_style
        button_text = "Current" if is_current else "Select"
        button_state = tk.DISABLED if is_current else tk.NORMAL
        
        select_button = tk.Button(style_frame, 
                                 text=button_text,
                                 state=button_state,
                                 width=12,
                                 command=lambda s=style_name: self._select_style(s))
        select_button.pack()
        self.select_buttons[style_name] = select_button
        
        # Highlight current style
        if is_current:
            style_frame.configure(bg='#e6f3ff')
            title_label.configure(bg='#e6f3ff')
            desc_label.configure(bg='#e6f3ff')
    
    def _initialize_previews(self):
        """Initialize the preview styles and canvases."""
        for style_name in self.available_styles:
            canvas = self.preview_canvases[style_name]
            
            try:
                # Get preview configuration
                preview_config = WaveformStyleFactory.get_preview_config(style_name)
                
                # Create style instance
                style_instance = WaveformStyleFactory.create_style(
                    style_name, canvas, self.preview_width, self.preview_height, preview_config
                )
                
                self.preview_styles[style_name] = style_instance
                
            except Exception as e:
                print(f"Failed to initialize preview for {style_name}: {e}")
                # Create a fallback error display
                canvas.create_text(
                    self.preview_width // 2, self.preview_height // 2,
                    text=f"Error loading\n{style_name}", 
                    fill="white", 
                    font=('TkDefaultFont', 8),
                    justify=tk.CENTER
                )
    
    def _select_style(self, style_name: str):
        """Select a new style.
        
        Args:
            style_name: Name of the selected style.
        """
        # Update selected style
        old_selection = self.selected_style
        self.selected_style = style_name
        
        # Update button states and frame appearances
        for name, button in self.select_buttons.items():
            frame = self.preview_frames[name]
            if name == style_name:
                button.configure(text="Applied ✓", state=tk.DISABLED, bg='#4CAF50', fg='white')
                frame.configure(bg='#d4edda', relief=tk.RAISED, borderwidth=3)
                # Update child widget backgrounds
                for child in frame.winfo_children():
                    if isinstance(child, tk.Label):
                        child.configure(bg='#d4edda')
            else:
                is_current = name == self.current_style
                button.configure(
                    text="Current" if is_current else "Select", 
                    state=tk.DISABLED if is_current else tk.NORMAL,
                    bg='SystemButtonFace', fg='black'
                )
                frame.configure(bg='SystemButtonFace' if not is_current else '#f0f0f0', 
                              relief=tk.RAISED, borderwidth=2)
                # Reset child widget backgrounds
                for child in frame.winfo_children():
                    if isinstance(child, tk.Label):
                        child.configure(bg='SystemButtonFace' if not is_current else '#f0f0f0')
        
        # Apply the changes immediately then refresh button states so only the
        # true current style is disabled and others remain selectable.
        self._apply_style_change()

        # Refresh button states using updated current_style
        for name, button in self.select_buttons.items():
            frame = self.preview_frames[name]
            is_current = name == self.current_style
            if is_current:
                button.configure(text="Current", state=tk.DISABLED, bg='#4CAF50', fg='white')
                frame.configure(bg='#d4edda', relief=tk.RAISED, borderwidth=3)
                for child in frame.winfo_children():
                    if isinstance(child, tk.Label):
                        child.configure(bg='#d4edda')
            else:
                button.configure(text="Select", state=tk.NORMAL, bg='SystemButtonFace', fg='black')
                frame.configure(bg='SystemButtonFace', relief=tk.RAISED, borderwidth=2)
                for child in frame.winfo_children():
                    if isinstance(child, tk.Label):
                        child.configure(bg='SystemButtonFace')
    
    def _apply_style_change(self):
        """Apply the selected style without closing the dialog."""
        try:
            # Validate selection
            if not self.selected_style or self.selected_style not in self.available_styles:
                return
            
            # Save using SettingsManager while preserving existing configs
            current_style, all_configs = settings_manager.load_waveform_style_settings()
            # Persist new current style, keep all style configs as-is
            settings_manager.save_waveform_style_settings(self.selected_style, all_configs)
            
            # Update current_style to reflect the change for future selections
            self.current_style = self.selected_style
            
        except Exception as e:
            print(f"Failed to save waveform style: {e}")
            # Don't show error dialog to avoid interrupting the flow
    
    def _start_animation(self):
        """Start the animation loop for previews."""
        self.animation_running = True
        self.animation_start_time = time.time()
        self._animate_previews()
    
    def _stop_animation(self):
        """Stop the animation loop."""
        self.animation_running = False
        if self.animation_job:
            self.dialog.after_cancel(self.animation_job)
            self.animation_job = None
    
    def _animate_previews(self):
        """Animate all preview styles."""
        if not self.animation_running or not self.dialog:
            return
        
        current_time = time.time()
        elapsed = current_time - self.animation_start_time
        
        # Update each preview
        for style_name, style in self.preview_styles.items():
            try:
                self._update_preview(style, elapsed)
            except Exception as e:
                print(f"Animation error for {style_name}: {e}")
        
        # Schedule next frame
        self.animation_job = self.dialog.after(33, self._animate_previews)  # ~30 FPS
    
    def _update_preview(self, style: BaseWaveformStyle, elapsed: float):
        """Update a single preview animation.
        
        Args:
            style: Style instance to update.
            elapsed: Elapsed time since animation start.
        """
        # Generate simulated audio data
        audio_levels = self._generate_simulated_audio(style.name, elapsed)
        current_level = sum(audio_levels) / len(audio_levels) if audio_levels else 0.0
        
        # Update style with simulated data
        style.update_audio_levels(audio_levels, current_level)
        style.update_animation_time(elapsed)
        
        # Draw based on a rotating state cycle
        state_cycle = (elapsed * 0.5) % 3
        
        if state_cycle < 1:
            style.draw_recording_state("REC")
        elif state_cycle < 2:
            style.draw_processing_state("PROC")
        else:
            style.draw_transcribing_state("TRANS")
    
    def _generate_simulated_audio(self, style_name: str, elapsed: float) -> List[float]:
        """Generate simulated audio data for preview.
        
        Args:
            style_name: Name of the style (for variation).
            elapsed: Elapsed time for animation.
            
        Returns:
            List of simulated audio levels.
        """
        # Different patterns for different styles
        levels = []
        bar_count = 20  # Default number of bars
        
        if style_name == "modern":
            # Smooth sine wave pattern
            for i in range(bar_count):
                level = 0.3 + 0.4 * math.sin(elapsed * 2 + i * 0.3)
                level += 0.1 * random.random()  # Add some noise
                levels.append(max(0.0, min(1.0, level)))
                
        elif style_name == "retro":
            # Retro-style stepped pattern
            for i in range(16):  # Retro uses fewer bars
                base_freq = 0.4 + 0.3 * math.sin(elapsed * 3 + i * 0.5)
                level = base_freq + 0.2 * math.sin(elapsed * 8 + i)
                level += random.choice([-0.1, 0, 0.1])  # Digital-style noise
                levels.append(max(0.0, min(1.0, level)))
                
        elif style_name == "minimalist":
            # Gentle, subtle pattern
            for i in range(bar_count):
                level = 0.2 + 0.3 * math.sin(elapsed * 1.5 + i * 0.2)
                level += 0.05 * math.sin(elapsed * 5 + i * 0.8)
                levels.append(max(0.0, min(1.0, level)))
                
        elif style_name == "spectrum":
            # Circular spectrum pattern
            for i in range(bar_count):
                # Simulate frequency response
                freq_response = 0.5 + 0.4 * math.sin(elapsed * 2.5 + i * 0.4)
                freq_response += 0.1 * math.sin(elapsed * 6 + i * 1.2)
                levels.append(max(0.0, min(1.0, freq_response)))
                
        elif style_name == "particle":
            # Dynamic, chaotic pattern
            for i in range(bar_count):
                energy = 0.4 + 0.5 * abs(math.sin(elapsed * 4 + i * 0.6))
                energy += 0.2 * random.random()  # Random energy spikes
                levels.append(max(0.0, min(1.0, energy)))
        
        else:
            # Default pattern
            for i in range(bar_count):
                level = 0.3 + 0.3 * math.sin(elapsed + i * 0.5)
                levels.append(max(0.0, min(1.0, level)))
        
        return levels
    
    def _create_instructions(self, parent):
        """Create instruction text.
        
        Args:
            parent: Parent widget for instructions.
        """
        instructions_text = (
            "Each style shows a live preview of how it will look during recording.\n"
            "Click 'Select' to apply immediately (the dialog stays open). Press Enter to apply and close, or click 'Close' when done."
        )
        
        instructions = tk.Label(parent, text=instructions_text,
                               justify=tk.LEFT, wraplength=750, 
                               font=('TkDefaultFont', 9))
        instructions.pack(pady=(10, 20), fill=tk.X)
    
    def _create_buttons(self, parent):
        """Create dialog buttons.
        
        Args:
            parent: Parent widget for buttons.
        """
        button_frame = tk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Reset to default button
        reset_button = tk.Button(button_frame, text="Reset to Default", 
                                command=self._reset_to_default)
        reset_button.pack(side=tk.LEFT)
        
        # Close button
        cancel_button = tk.Button(button_frame, text="Close", 
                                 command=self._on_cancel)
        cancel_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # No separate Apply button; selecting a style applies immediately
    
    def _reset_to_default(self):
        """Reset to default style (Particle Storm)."""
        # Use configured default to keep a single source of truth
        self._select_style(config.CURRENT_WAVEFORM_STYLE)
    
    def _on_apply(self):
        """Apply the selected style."""
        try:
            # Validate selection
            if not self.selected_style or self.selected_style not in self.available_styles:
                messagebox.showerror("Error", "Please select a valid waveform style")
                return
            
            # Save using SettingsManager while preserving existing configs
            current_style, all_configs = settings_manager.load_waveform_style_settings()
            # Persist new current style, keep all style configs as-is
            settings_manager.save_waveform_style_settings(self.selected_style, all_configs)
            
            # Close dialog without showing popup
            self._on_cancel()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save waveform style: {str(e)}")
    
    def _on_cancel(self):
        """Cancel and close the dialog."""
        self._stop_animation()
        if self.dialog:
            # Release any active grab to avoid blocking future dialogs
            try:
                self.dialog.grab_release()
            except Exception:
                pass
            # Best-effort unbind in case older versions used bind_all
            try:
                self.dialog.unbind_all("<MouseWheel>")
                self.dialog.unbind_all("<Button-4>")
                self.dialog.unbind_all("<Button-5>")
            except Exception:
                pass
            try:
                self.dialog.destroy()
            finally:
                self.dialog = None


def show_waveform_style_dialog(parent, current_style: str = "particle"):
    """Show the waveform style configuration dialog.
    
    Args:
        parent: Parent window.
        current_style: Currently selected style name.
        
    Returns:
        The dialog instance (mainly for testing).
    """
    dialog = WaveformStyleDialog(parent, current_style)
    dialog.show()
    return dialog


if __name__ == "__main__":
    # Test the dialog
    import sys
    import os
    
    # Add the project root to Python path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    
    # Import required modules
    from ui.waveform_styles.modern_style import ModernStyle
    from ui.waveform_styles.retro_style import RetroStyle
    from ui.waveform_styles.minimalist_style import MinimalistStyle
    from ui.waveform_styles.spectrum_style import SpectrumStyle
    from ui.waveform_styles.particle_style import ParticleStyle
    
    # Create test window
    root = tk.Tk()
    root.title("Test Waveform Style Dialog")
    root.geometry("400x200")
    
    def open_dialog():
        show_waveform_style_dialog(root, "modern")
    
    test_button = tk.Button(root, text="Open Waveform Style Dialog", command=open_dialog)
    test_button.pack(expand=True)
    
    root.mainloop()
