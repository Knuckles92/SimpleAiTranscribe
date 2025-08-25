"""
WaveformEditor - Visual chunk editing interface for meeting audio.
Provides professional audio waveform visualization and interactive chunk boundary editing.
"""
import tkinter as tk
from tkinter import ttk, Canvas, Scrollbar, messagebox, simpledialog
import numpy as np
import wave
import threading
import time
import math
import logging
import json
from typing import List, Dict, Tuple, Optional, Callable, Union, Any
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timedelta

# Import meeting configuration and processor
from .config_meeting import MeetingConfig
from .meeting_processor import MeetingProcessor, ChunkMetadata

# Try to import pygame for audio playback, fallback to basic playback
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    logging.warning("pygame not available - audio playback will be limited")


@dataclass
class WaveformSettings:
    """Configuration settings for waveform display."""
    # Visual settings
    waveform_color: str = "#00AAFF"
    chunk_boundary_color: str = "#FF4444"
    selected_chunk_color: str = "#FFAA00"
    background_color: str = "#1E1E1E"
    grid_color: str = "#333333"
    time_label_color: str = "#CCCCCC"
    
    # Display parameters
    pixels_per_second: float = 50.0  # Horizontal zoom level
    waveform_height_ratio: float = 0.6  # Portion of canvas height for waveform
    ruler_height: int = 30  # Height of time ruler
    chunk_label_height: int = 25  # Height of chunk labels
    
    # Interaction settings
    boundary_snap_distance: int = 10  # Pixels to snap to nearby boundaries
    min_chunk_duration: float = 1.0  # Minimum chunk duration in seconds
    max_zoom: float = 500.0  # Maximum pixels per second
    min_zoom: float = 10.0   # Minimum pixels per second


class AudioPlayback:
    """Simple audio playback handler."""
    
    def __init__(self):
        """Initialize audio playback."""
        self.is_playing = False
        self.current_position = 0.0
        self.duration = 0.0
        self.audio_data = None
        self.sample_rate = 44100
        
        if PYGAME_AVAILABLE:
            pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=1, buffer=512)
        
    def load_audio(self, file_path: str):
        """Load audio file for playback.
        
        Args:
            file_path: Path to audio file
        """
        try:
            with wave.open(file_path, 'rb') as wav_file:
                self.sample_rate = wav_file.getframerate()
                frames = wav_file.readframes(wav_file.getnframes())
                self.audio_data = np.frombuffer(frames, dtype=np.int16)
                self.duration = len(self.audio_data) / self.sample_rate
                
            if PYGAME_AVAILABLE:
                pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=1, buffer=512)
                
        except Exception as e:
            logging.error(f"Failed to load audio for playback: {e}")
            
    def play_from_position(self, position: float):
        """Play audio from specific position.
        
        Args:
            position: Start position in seconds
        """
        if not PYGAME_AVAILABLE or self.audio_data is None:
            logging.warning("Audio playback not available")
            return
            
        try:
            start_sample = int(position * self.sample_rate)
            if start_sample >= len(self.audio_data):
                return
                
            # Create temporary audio segment
            segment = self.audio_data[start_sample:]
            
            # Convert to pygame sound format
            sound_array = np.array([segment], dtype=np.int16)
            sound = pygame.sndarray.make_sound(sound_array)
            
            pygame.mixer.stop()
            sound.play()
            self.is_playing = True
            self.current_position = position
            
        except Exception as e:
            logging.error(f"Failed to play audio: {e}")
            
    def stop(self):
        """Stop audio playback."""
        if PYGAME_AVAILABLE:
            pygame.mixer.stop()
        self.is_playing = False


class WaveformEditor:
    """Professional waveform editor for visual chunk boundary editing."""
    
    def __init__(self, parent: tk.Widget, meeting_processor: MeetingProcessor, 
                 width: int = 800, height: int = 300):
        """Initialize the waveform editor.
        
        Args:
            parent: Parent tkinter widget
            meeting_processor: MeetingProcessor instance for chunk management
            width: Editor width in pixels
            height: Editor height in pixels
        """
        self.parent = parent
        self.meeting_processor = meeting_processor
        self.width = width
        self.height = height
        
        # Settings and state
        self.settings = WaveformSettings()
        self.config = MeetingConfig()
        
        # Audio data
        self.audio_file_path: Optional[str] = None
        self.waveform_data: Optional[np.ndarray] = None
        self.sample_rate: int = 44100
        self.duration: float = 0.0
        
        # Chunk management
        self.chunks: List[ChunkMetadata] = []
        self.selected_chunk_id: Optional[str] = None
        self.dragging_boundary: Optional[Tuple[str, str]] = None  # (chunk_id, 'start'|'end')
        
        # View state
        self.view_start = 0.0  # Start time of current view in seconds
        self.view_end = 10.0   # End time of current view in seconds
        self.zoom_level = 1.0  # Current zoom multiplier
        
        # UI components
        self.main_frame: Optional[tk.Frame] = None
        self.canvas: Optional[Canvas] = None
        self.h_scrollbar: Optional[Scrollbar] = None
        self.v_scrollbar: Optional[Scrollbar] = None
        self.toolbar_frame: Optional[tk.Frame] = None
        self.status_label: Optional[tk.Label] = None
        
        # Mouse interaction state
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.mouse_pressed = False
        self.pan_start_x = 0
        self.pan_start_view = 0.0
        
        # Audio playback
        self.playback = AudioPlayback()
        
        # Context menu
        self.context_menu: Optional[tk.Menu] = None
        
        self._setup_ui()
        self._setup_bindings()
        
    def _setup_ui(self):
        """Create the user interface components."""
        # Main container frame
        self.main_frame = tk.Frame(self.parent, bg=self.settings.background_color)
        
        # Toolbar
        self._create_toolbar()
        
        # Canvas frame with scrollbars
        canvas_frame = tk.Frame(self.main_frame, bg=self.settings.background_color)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create canvas
        self.canvas = Canvas(
            canvas_frame,
            width=self.width,
            height=self.height,
            bg=self.settings.background_color,
            highlightthickness=0,
            scrollregion=(0, 0, 1000, self.height)
        )
        
        # Scrollbars
        self.h_scrollbar = Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self._on_h_scroll)
        self.v_scrollbar = Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self._on_v_scroll)
        
        self.canvas.configure(
            xscrollcommand=self.h_scrollbar.set,
            yscrollcommand=self.v_scrollbar.set
        )
        
        # Grid layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)
        
        # Status bar
        self.status_label = tk.Label(
            self.main_frame, 
            text="No audio file loaded", 
            bg=self.settings.background_color,
            fg=self.settings.time_label_color,
            font=("Arial", 9)
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)
        
        # Context menu
        self._create_context_menu()
        
    def _create_toolbar(self):
        """Create the toolbar with zoom and control buttons."""
        self.toolbar_frame = tk.Frame(self.main_frame, bg=self.settings.background_color, height=40)
        self.toolbar_frame.pack(fill=tk.X, padx=5, pady=2)
        self.toolbar_frame.pack_propagate(False)
        
        # Zoom controls
        tk.Label(self.toolbar_frame, text="Zoom:", bg=self.settings.background_color, 
                fg=self.settings.time_label_color).pack(side=tk.LEFT, padx=(5, 2))
        
        zoom_out_btn = tk.Button(self.toolbar_frame, text="-", width=3, command=self.zoom_out)
        zoom_out_btn.pack(side=tk.LEFT, padx=2)
        
        zoom_in_btn = tk.Button(self.toolbar_frame, text="+", width=3, command=self.zoom_in)
        zoom_in_btn.pack(side=tk.LEFT, padx=2)
        
        zoom_fit_btn = tk.Button(self.toolbar_frame, text="Fit", width=4, command=self.zoom_to_fit)
        zoom_fit_btn.pack(side=tk.LEFT, padx=5)
        
        # Separator
        tk.Frame(self.toolbar_frame, width=2, bg=self.settings.grid_color).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Playback controls
        play_btn = tk.Button(self.toolbar_frame, text="▶", width=3, command=self.play_from_cursor)
        play_btn.pack(side=tk.LEFT, padx=2)
        
        stop_btn = tk.Button(self.toolbar_frame, text="⏹", width=3, command=self.stop_playback)
        stop_btn.pack(side=tk.LEFT, padx=2)
        
        # Separator
        tk.Frame(self.toolbar_frame, width=2, bg=self.settings.grid_color).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Chunk operations
        add_boundary_btn = tk.Button(self.toolbar_frame, text="Add Boundary", command=self.add_boundary_at_cursor)
        add_boundary_btn.pack(side=tk.LEFT, padx=2)
        
        merge_btn = tk.Button(self.toolbar_frame, text="Merge Chunks", command=self.merge_selected_chunks)
        merge_btn.pack(side=tk.LEFT, padx=2)
        
    def _create_context_menu(self):
        """Create right-click context menu."""
        self.context_menu = tk.Menu(self.parent, tearoff=0)
        self.context_menu.add_command(label="Add Boundary Here", command=self.add_boundary_at_cursor)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete Chunk", command=self.delete_selected_chunk)
        self.context_menu.add_command(label="Merge with Next", command=self.merge_with_next_chunk)
        self.context_menu.add_command(label="Split Chunk", command=self.split_chunk_at_cursor)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Export Chunk", command=self.export_selected_chunk)
        self.context_menu.add_command(label="Play Chunk", command=self.play_selected_chunk)
        
    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings."""
        if not self.canvas:
            return
            
        # Mouse events
        self.canvas.bind("<Button-1>", self._on_mouse_click)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_release)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        
        # Keyboard events (when canvas has focus)
        self.canvas.bind("<Key>", self._on_key_press)
        self.canvas.focus_set()
        
    def pack(self, **kwargs):
        """Pack the waveform editor."""
        if self.main_frame:
            self.main_frame.pack(**kwargs)
            
    def grid(self, **kwargs):
        """Grid the waveform editor."""
        if self.main_frame:
            self.main_frame.grid(**kwargs)
    
    def load_audio_file(self, file_path: str):
        """Load an audio file and display its waveform.
        
        Args:
            file_path: Path to the audio file to load
        """
        try:
            self.audio_file_path = file_path
            
            # Load audio data
            self._load_waveform_data(file_path)
            
            # Load audio for playback
            self.playback.load_audio(file_path)
            
            # Load existing chunks from meeting processor
            self._load_chunks()
            
            # Update view to fit entire waveform
            self.zoom_to_fit()
            
            # Refresh display
            self._redraw_canvas()
            
            self.status_label.configure(text=f"Loaded: {Path(file_path).name} ({self.duration:.2f}s)")
            logging.info(f"Loaded audio file: {file_path}")
            
        except Exception as e:
            error_msg = f"Failed to load audio file: {e}"
            logging.error(error_msg)
            messagebox.showerror("Error", error_msg)
            
    def _load_waveform_data(self, file_path: str):
        """Load and process waveform data from audio file.
        
        Args:
            file_path: Path to the audio file
        """
        with wave.open(file_path, 'rb') as wav_file:
            self.sample_rate = wav_file.getframerate()
            frames = wav_file.readframes(wav_file.getnframes())
            
            # Convert to numpy array
            if wav_file.getsampwidth() == 1:
                dtype = np.uint8
            elif wav_file.getsampwidth() == 2:
                dtype = np.int16
            elif wav_file.getsampwidth() == 4:
                dtype = np.int32
            else:
                raise ValueError(f"Unsupported sample width: {wav_file.getsampwidth()}")
                
            raw_data = np.frombuffer(frames, dtype=dtype)
            
            # Convert to float and normalize
            if wav_file.getsampwidth() == 1:
                raw_data = raw_data.astype(np.float32) / 128.0 - 1.0
            elif wav_file.getsampwidth() == 2:
                raw_data = raw_data.astype(np.float32) / 32768.0
            elif wav_file.getsampwidth() == 4:
                raw_data = raw_data.astype(np.float32) / 2147483648.0
                
            # Handle stereo by taking mean
            if wav_file.getnchannels() == 2:
                raw_data = raw_data.reshape(-1, 2).mean(axis=1)
                
            self.waveform_data = raw_data
            self.duration = len(raw_data) / self.sample_rate
            
    def _load_chunks(self):
        """Load chunk data from meeting processor."""
        if self.meeting_processor and hasattr(self.meeting_processor, 'get_chunks'):
            try:
                self.chunks = self.meeting_processor.get_chunks()
            except Exception as e:
                logging.warning(f"Failed to load chunks from processor: {e}")
                self.chunks = []
        else:
            # Create default chunks if no processor available
            if self.duration > 0:
                chunk_duration = self.config.MEETING_MAX_CHUNK_MINUTES * 60
                num_chunks = max(1, int(np.ceil(self.duration / chunk_duration)))
                
                self.chunks = []
                for i in range(num_chunks):
                    start_time = i * chunk_duration
                    end_time = min((i + 1) * chunk_duration, self.duration)
                    
                    chunk = ChunkMetadata(
                        chunk_id=f"chunk_{i:03d}",
                        start_timestamp=start_time,
                        end_timestamp=end_time,
                        duration=end_time - start_time,
                        file_path="",
                        transcription=""
                    )
                    self.chunks.append(chunk)
    
    def _redraw_canvas(self):
        """Redraw the entire canvas with waveform and chunks."""
        if not self.canvas or not self.waveform_data is not None:
            return
            
        # Clear canvas
        self.canvas.delete("all")
        
        # Update scroll region based on zoom
        total_width = self.duration * self.settings.pixels_per_second * self.zoom_level
        self.canvas.configure(scrollregion=(0, 0, total_width, self.height))
        
        # Draw time grid
        self._draw_time_grid()
        
        # Draw waveform
        self._draw_waveform()
        
        # Draw chunk boundaries
        self._draw_chunk_boundaries()
        
        # Draw time ruler
        self._draw_time_ruler()
        
        # Update status
        self._update_status()
        
    def _draw_waveform(self):
        """Draw the audio waveform."""
        if not self.canvas or self.waveform_data is None:
            return
            
        canvas_width = self.canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = self.width
            
        waveform_top = self.settings.ruler_height + self.settings.chunk_label_height
        waveform_bottom = self.height - 20
        waveform_center = (waveform_top + waveform_bottom) // 2
        waveform_height = (waveform_bottom - waveform_top) * self.settings.waveform_height_ratio // 2
        
        # Calculate visible time range
        scroll_x = self.canvas.canvasx(0)
        pixels_per_second = self.settings.pixels_per_second * self.zoom_level
        start_time = scroll_x / pixels_per_second
        end_time = (scroll_x + canvas_width) / pixels_per_second
        
        # Get audio samples for visible range
        start_sample = max(0, int(start_time * self.sample_rate))
        end_sample = min(len(self.waveform_data), int(end_time * self.sample_rate))
        
        if start_sample >= end_sample:
            return
            
        # Downsample for performance
        samples_per_pixel = max(1, (end_sample - start_sample) // canvas_width)
        
        if samples_per_pixel > 1:
            # Downsample by taking max/min values for each pixel
            audio_segment = self.waveform_data[start_sample:end_sample]
            
            # Reshape and get min/max for each pixel column
            num_pixels = len(audio_segment) // samples_per_pixel
            reshaped = audio_segment[:num_pixels * samples_per_pixel].reshape(num_pixels, samples_per_pixel)
            max_vals = np.max(reshaped, axis=1)
            min_vals = np.min(reshaped, axis=1)
            
            # Draw waveform
            for i in range(len(max_vals)):
                x = start_time * pixels_per_second + i * (pixels_per_second / (len(max_vals) / (end_time - start_time)))
                
                y_max = waveform_center - max_vals[i] * waveform_height
                y_min = waveform_center - min_vals[i] * waveform_height
                
                self.canvas.create_line(
                    x, y_max, x, y_min,
                    fill=self.settings.waveform_color,
                    width=1
                )
        else:
            # Draw individual samples
            for i in range(start_sample, end_sample, max(1, samples_per_pixel)):
                x = i / self.sample_rate * pixels_per_second
                y = waveform_center - self.waveform_data[i] * waveform_height
                
                if i == start_sample:
                    points = [x, waveform_center]
                
                points.extend([x, y])
                
            if len(points) > 2:
                points.extend([points[-2], waveform_center])  # Close the shape
                self.canvas.create_polygon(
                    points,
                    fill=self.settings.waveform_color,
                    outline=self.settings.waveform_color,
                    width=1
                )
    
    def _draw_chunk_boundaries(self):
        """Draw chunk boundary markers."""
        if not self.canvas or not self.chunks:
            return
            
        pixels_per_second = self.settings.pixels_per_second * self.zoom_level
        
        for chunk in self.chunks:
            # Draw start boundary (except for first chunk)
            if chunk.start_timestamp > 0:
                x = chunk.start_timestamp * pixels_per_second
                self._draw_boundary_line(x, chunk.chunk_id, 'start')
                
            # Draw end boundary
            x = chunk.end_timestamp * pixels_per_second
            self._draw_boundary_line(x, chunk.chunk_id, 'end')
            
            # Draw chunk label
            chunk_center = (chunk.start_timestamp + chunk.end_timestamp) / 2 * pixels_per_second
            self._draw_chunk_label(chunk_center, chunk)
            
    def _draw_boundary_line(self, x: float, chunk_id: str, boundary_type: str):
        """Draw a chunk boundary line.
        
        Args:
            x: X coordinate of the boundary
            chunk_id: ID of the chunk
            boundary_type: 'start' or 'end'
        """
        color = self.settings.chunk_boundary_color
        if self.selected_chunk_id == chunk_id:
            color = self.settings.selected_chunk_color
            
        # Draw vertical line
        line_id = self.canvas.create_line(
            x, self.settings.ruler_height,
            x, self.height - 20,
            fill=color,
            width=2,
            tags=f"boundary_{chunk_id}_{boundary_type}"
        )
        
        # Add small handle at top
        handle_id = self.canvas.create_rectangle(
            x - 4, self.settings.ruler_height,
            x + 4, self.settings.ruler_height + 8,
            fill=color,
            outline=color,
            tags=f"handle_{chunk_id}_{boundary_type}"
        )
        
    def _draw_chunk_label(self, x: float, chunk: ChunkMetadata):
        """Draw chunk label.
        
        Args:
            x: X coordinate for the label center
            chunk: Chunk metadata
        """
        label_y = self.settings.ruler_height + self.settings.chunk_label_height // 2
        
        # Background rectangle
        label_text = f"{chunk.chunk_id}"
        if chunk.transcription:
            # Show first few words of transcription
            words = chunk.transcription.split()[:3]
            if len(words) > 0:
                label_text += f": {' '.join(words)}..."
                
        # Estimate text width
        text_width = len(label_text) * 6  # Rough estimate
        
        bg_id = self.canvas.create_rectangle(
            x - text_width // 2 - 4, label_y - 8,
            x + text_width // 2 + 4, label_y + 8,
            fill=self.settings.background_color,
            outline=self.settings.grid_color,
            tags=f"chunk_label_{chunk.chunk_id}"
        )
        
        # Label text
        text_color = self.settings.selected_chunk_color if self.selected_chunk_id == chunk.chunk_id else self.settings.time_label_color
        text_id = self.canvas.create_text(
            x, label_y,
            text=label_text,
            fill=text_color,
            font=("Arial", 8),
            tags=f"chunk_text_{chunk.chunk_id}"
        )
        
    def _draw_time_ruler(self):
        """Draw time ruler at the top."""
        if not self.canvas:
            return
            
        canvas_width = self.canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = self.width
            
        pixels_per_second = self.settings.pixels_per_second * self.zoom_level
        scroll_x = self.canvas.canvasx(0)
        
        start_time = scroll_x / pixels_per_second
        end_time = (scroll_x + canvas_width) / pixels_per_second
        
        # Determine appropriate time interval
        time_span = end_time - start_time
        if time_span < 10:
            interval = 1  # 1 second
        elif time_span < 60:
            interval = 5  # 5 seconds
        elif time_span < 300:
            interval = 30  # 30 seconds
        else:
            interval = 60  # 1 minute
            
        # Draw time marks
        start_mark = int(start_time // interval) * interval
        current_time = start_mark
        
        while current_time <= end_time:
            x = current_time * pixels_per_second
            
            # Draw tick mark
            self.canvas.create_line(
                x, 0, x, self.settings.ruler_height // 2,
                fill=self.settings.grid_color,
                width=1
            )
            
            # Draw time label
            time_str = self._format_time(current_time)
            self.canvas.create_text(
                x, self.settings.ruler_height // 4,
                text=time_str,
                fill=self.settings.time_label_color,
                font=("Arial", 8)
            )
            
            current_time += interval
            
    def _draw_time_grid(self):
        """Draw vertical time grid lines."""
        if not self.canvas:
            return
            
        canvas_width = self.canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = self.width
            
        pixels_per_second = self.settings.pixels_per_second * self.zoom_level
        scroll_x = self.canvas.canvasx(0)
        
        start_time = scroll_x / pixels_per_second
        end_time = (scroll_x + canvas_width) / pixels_per_second
        
        # Determine grid interval
        time_span = end_time - start_time
        if time_span < 10:
            interval = 1
        elif time_span < 60:
            interval = 5
        else:
            interval = 10
            
        # Draw grid lines
        start_mark = int(start_time // interval) * interval
        current_time = start_mark
        
        while current_time <= end_time:
            x = current_time * pixels_per_second
            
            self.canvas.create_line(
                x, self.settings.ruler_height,
                x, self.height - 20,
                fill=self.settings.grid_color,
                width=1,
                stipple="gray25"
            )
            
            current_time += interval
    
    def _format_time(self, seconds: float) -> str:
        """Format time in seconds to MM:SS or HH:MM:SS format.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string
        """
        total_seconds = int(seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def _update_status(self):
        """Update status bar with current information."""
        if not self.status_label:
            return
            
        status_parts = []
        
        if self.audio_file_path:
            status_parts.append(f"File: {Path(self.audio_file_path).name}")
            status_parts.append(f"Duration: {self._format_time(self.duration)}")
            
        if self.chunks:
            status_parts.append(f"Chunks: {len(self.chunks)}")
            
        if self.selected_chunk_id:
            selected_chunk = next((c for c in self.chunks if c.chunk_id == self.selected_chunk_id), None)
            if selected_chunk:
                status_parts.append(f"Selected: {selected_chunk.chunk_id} ({self._format_time(selected_chunk.duration)})")
                
        zoom_percent = int(self.zoom_level * 100)
        status_parts.append(f"Zoom: {zoom_percent}%")
        
        self.status_label.configure(text=" | ".join(status_parts))
    
    # Event handlers
    def _on_mouse_click(self, event):
        """Handle mouse click events."""
        if not self.canvas:
            return
            
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        self.mouse_pressed = True
        
        # Check if clicking on a boundary handle
        clicked_items = self.canvas.find_overlapping(canvas_x - 2, canvas_y - 2, canvas_x + 2, canvas_y + 2)
        
        for item in clicked_items:
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag.startswith("handle_"):
                    parts = tag.split("_")
                    if len(parts) >= 3:
                        chunk_id = "_".join(parts[1:-1])
                        boundary_type = parts[-1]
                        self.dragging_boundary = (chunk_id, boundary_type)
                        return
                        
        # Check if clicking on a chunk
        time_position = canvas_x / (self.settings.pixels_per_second * self.zoom_level)
        clicked_chunk = self._get_chunk_at_time(time_position)
        
        if clicked_chunk:
            self.selected_chunk_id = clicked_chunk.chunk_id
            self._redraw_canvas()
        else:
            # Start panning
            self.pan_start_x = event.x
            self.pan_start_view = self.canvas.canvasx(0)
            
    def _on_mouse_drag(self, event):
        """Handle mouse drag events."""
        if not self.canvas or not self.mouse_pressed:
            return
            
        if self.dragging_boundary:
            # Drag boundary
            canvas_x = self.canvas.canvasx(event.x)
            time_position = canvas_x / (self.settings.pixels_per_second * self.zoom_level)
            self._move_boundary(self.dragging_boundary[0], self.dragging_boundary[1], time_position)
            
        else:
            # Pan view
            dx = self.pan_start_x - event.x
            new_scroll_x = self.pan_start_view + dx
            
            # Constrain panning
            scroll_region = self.canvas.cget("scrollregion").split()
            if len(scroll_region) >= 3:
                max_scroll = float(scroll_region[2]) - self.canvas.winfo_width()
                new_scroll_x = max(0, min(new_scroll_x, max_scroll))
                
            self.canvas.xview_moveto(new_scroll_x / float(scroll_region[2]) if float(scroll_region[2]) > 0 else 0)
            
    def _on_mouse_release(self, event):
        """Handle mouse release events."""
        self.mouse_pressed = False
        self.dragging_boundary = None
        
    def _on_right_click(self, event):
        """Handle right-click context menu."""
        if not self.canvas or not self.context_menu:
            return
            
        canvas_x = self.canvas.canvasx(event.x)
        time_position = canvas_x / (self.settings.pixels_per_second * self.zoom_level)
        
        # Select chunk at cursor
        clicked_chunk = self._get_chunk_at_time(time_position)
        if clicked_chunk:
            self.selected_chunk_id = clicked_chunk.chunk_id
            self._redraw_canvas()
            
        # Show context menu
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        except tk.TclError:
            pass
        finally:
            self.context_menu.grab_release()
            
    def _on_mouse_move(self, event):
        """Handle mouse move for hover effects."""
        if not self.canvas:
            return
            
        # Update cursor based on hover target
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Check if hovering over boundary handle
        items = self.canvas.find_overlapping(canvas_x - 4, canvas_y - 4, canvas_x + 4, canvas_y + 4)
        hover_boundary = False
        
        for item in items:
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag.startswith("handle_"):
                    hover_boundary = True
                    break
                    
        if hover_boundary:
            self.canvas.configure(cursor="sb_h_double_arrow")
        else:
            self.canvas.configure(cursor="")
            
    def _on_mouse_wheel(self, event):
        """Handle mouse wheel for zooming."""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
            
    def _on_key_press(self, event):
        """Handle keyboard shortcuts."""
        if event.keysym == "space":
            if self.playback.is_playing:
                self.stop_playback()
            else:
                self.play_from_cursor()
        elif event.keysym == "Delete" and self.selected_chunk_id:
            self.delete_selected_chunk()
            
    def _on_h_scroll(self, *args):
        """Handle horizontal scrollbar."""
        if self.canvas:
            self.canvas.xview(*args)
            
    def _on_v_scroll(self, *args):
        """Handle vertical scrollbar.""" 
        if self.canvas:
            self.canvas.yview(*args)
    
    # Utility methods
    def _get_chunk_at_time(self, time_position: float) -> Optional[ChunkMetadata]:
        """Get chunk at specific time position.
        
        Args:
            time_position: Time position in seconds
            
        Returns:
            ChunkMetadata if found, None otherwise
        """
        for chunk in self.chunks:
            if chunk.start_timestamp <= time_position <= chunk.end_timestamp:
                return chunk
        return None
        
    def _move_boundary(self, chunk_id: str, boundary_type: str, new_time: float):
        """Move a chunk boundary to new time position.
        
        Args:
            chunk_id: ID of the chunk
            boundary_type: 'start' or 'end'
            new_time: New time position in seconds
        """
        chunk = next((c for c in self.chunks if c.chunk_id == chunk_id), None)
        if not chunk:
            return
            
        # Constrain to valid range
        new_time = max(0, min(new_time, self.duration))
        
        if boundary_type == 'start':
            # Ensure minimum chunk duration
            max_start = chunk.end_timestamp - self.settings.min_chunk_duration
            chunk.start_timestamp = min(new_time, max_start)
            
            # Update adjacent chunk
            prev_chunk = self._get_previous_chunk(chunk_id)
            if prev_chunk:
                prev_chunk.end_timestamp = chunk.start_timestamp
                prev_chunk.duration = prev_chunk.end_timestamp - prev_chunk.start_timestamp
                
        else:  # end boundary
            # Ensure minimum chunk duration
            min_end = chunk.start_timestamp + self.settings.min_chunk_duration
            chunk.end_timestamp = max(new_time, min_end)
            
            # Update adjacent chunk
            next_chunk = self._get_next_chunk(chunk_id)
            if next_chunk:
                next_chunk.start_timestamp = chunk.end_timestamp
                next_chunk.duration = next_chunk.end_timestamp - next_chunk.start_timestamp
                
        # Update chunk duration
        chunk.duration = chunk.end_timestamp - chunk.start_timestamp
        
        # Save changes and redraw
        self._save_chunks()
        self._redraw_canvas()
        
    def _get_previous_chunk(self, chunk_id: str) -> Optional[ChunkMetadata]:
        """Get the chunk immediately before the specified chunk."""
        target_chunk = next((c for c in self.chunks if c.chunk_id == chunk_id), None)
        if not target_chunk:
            return None
            
        prev_chunk = None
        for chunk in sorted(self.chunks, key=lambda c: c.start_timestamp):
            if chunk.chunk_id == chunk_id:
                return prev_chunk
            prev_chunk = chunk
            
        return None
        
    def _get_next_chunk(self, chunk_id: str) -> Optional[ChunkMetadata]:
        """Get the chunk immediately after the specified chunk."""
        found_target = False
        for chunk in sorted(self.chunks, key=lambda c: c.start_timestamp):
            if found_target:
                return chunk
            if chunk.chunk_id == chunk_id:
                found_target = True
                
        return None
        
    def _save_chunks(self):
        """Save chunk changes back to meeting processor."""
        if self.meeting_processor and hasattr(self.meeting_processor, 'update_chunks'):
            try:
                self.meeting_processor.update_chunks(self.chunks)
            except Exception as e:
                logging.error(f"Failed to save chunks: {e}")
                
    # Public methods for toolbar actions
    def zoom_in(self):
        """Zoom in on the waveform."""
        new_zoom = min(self.zoom_level * 1.5, self.settings.max_zoom / self.settings.pixels_per_second)
        self.zoom_level = new_zoom
        self._redraw_canvas()
        
    def zoom_out(self):
        """Zoom out on the waveform."""
        new_zoom = max(self.zoom_level / 1.5, self.settings.min_zoom / self.settings.pixels_per_second)
        self.zoom_level = new_zoom
        self._redraw_canvas()
        
    def zoom_to_fit(self):
        """Zoom to fit entire waveform in view."""
        if self.duration <= 0:
            return
            
        canvas_width = self.canvas.winfo_width() if self.canvas else self.width
        if canvas_width <= 1:
            canvas_width = self.width
            
        pixels_per_second = (canvas_width - 40) / self.duration  # Leave some margin
        self.zoom_level = pixels_per_second / self.settings.pixels_per_second
        self.zoom_level = max(self.settings.min_zoom / self.settings.pixels_per_second, 
                             min(self.zoom_level, self.settings.max_zoom / self.settings.pixels_per_second))
        
        # Reset scroll position
        if self.canvas:
            self.canvas.xview_moveto(0)
            
        self._redraw_canvas()
        
    def play_from_cursor(self):
        """Play audio from current cursor position."""
        if not self.canvas:
            return
            
        # Get current view position as playback start
        scroll_x = self.canvas.canvasx(0)
        start_time = scroll_x / (self.settings.pixels_per_second * self.zoom_level)
        
        self.playback.play_from_position(start_time)
        
    def stop_playback(self):
        """Stop audio playback."""
        self.playback.stop()
        
    def add_boundary_at_cursor(self):
        """Add chunk boundary at current cursor position."""
        if not self.canvas:
            return
            
        # Get cursor position
        cursor_x = self.canvas.winfo_pointerx() - self.canvas.winfo_rootx()
        canvas_x = self.canvas.canvasx(cursor_x)
        time_position = canvas_x / (self.settings.pixels_per_second * self.zoom_level)
        
        # Find chunk to split
        target_chunk = self._get_chunk_at_time(time_position)
        if not target_chunk:
            return
            
        # Check minimum chunk duration
        if (time_position - target_chunk.start_timestamp < self.settings.min_chunk_duration or
            target_chunk.end_timestamp - time_position < self.settings.min_chunk_duration):
            messagebox.showwarning("Warning", f"Cannot split chunk - resulting chunks would be less than {self.settings.min_chunk_duration}s")
            return
            
        # Create new chunk
        new_chunk_id = f"{target_chunk.chunk_id}_split"
        new_chunk = ChunkMetadata(
            chunk_id=new_chunk_id,
            start_timestamp=time_position,
            end_timestamp=target_chunk.end_timestamp,
            duration=target_chunk.end_timestamp - time_position,
            file_path="",
            transcription=""
        )
        
        # Update original chunk
        target_chunk.end_timestamp = time_position
        target_chunk.duration = time_position - target_chunk.start_timestamp
        
        # Add new chunk
        self.chunks.append(new_chunk)
        
        # Save and refresh
        self._save_chunks()
        self._redraw_canvas()
        
    def delete_selected_chunk(self):
        """Delete the currently selected chunk."""
        if not self.selected_chunk_id:
            return
            
        # Find selected chunk
        selected_chunk = next((c for c in self.chunks if c.chunk_id == self.selected_chunk_id), None)
        if not selected_chunk:
            return
            
        # Confirm deletion
        result = messagebox.askyesno(
            "Delete Chunk",
            f"Are you sure you want to delete chunk '{selected_chunk.chunk_id}'?\nThis action cannot be undone."
        )
        
        if not result:
            return
            
        # Find adjacent chunks to merge
        prev_chunk = self._get_previous_chunk(self.selected_chunk_id)
        next_chunk = self._get_next_chunk(self.selected_chunk_id)
        
        if prev_chunk and next_chunk:
            # Merge previous and next chunks
            prev_chunk.end_timestamp = next_chunk.end_timestamp
            prev_chunk.duration = prev_chunk.end_timestamp - prev_chunk.start_timestamp
            # Combine transcriptions if available
            if next_chunk.transcription:
                if prev_chunk.transcription:
                    prev_chunk.transcription += " " + next_chunk.transcription
                else:
                    prev_chunk.transcription = next_chunk.transcription
                    
            # Remove both selected and next chunk
            self.chunks = [c for c in self.chunks if c.chunk_id not in [self.selected_chunk_id, next_chunk.chunk_id]]
            
        elif prev_chunk:
            # Extend previous chunk
            prev_chunk.end_timestamp = selected_chunk.end_timestamp
            prev_chunk.duration = prev_chunk.end_timestamp - prev_chunk.start_timestamp
            self.chunks = [c for c in self.chunks if c.chunk_id != self.selected_chunk_id]
            
        elif next_chunk:
            # Extend next chunk
            next_chunk.start_timestamp = selected_chunk.start_timestamp
            next_chunk.duration = next_chunk.end_timestamp - next_chunk.start_timestamp
            self.chunks = [c for c in self.chunks if c.chunk_id != self.selected_chunk_id]
            
        else:
            # Only chunk, just remove it
            self.chunks = [c for c in self.chunks if c.chunk_id != self.selected_chunk_id]
            
        self.selected_chunk_id = None
        
        # Save and refresh
        self._save_chunks()
        self._redraw_canvas()
        
    def merge_selected_chunks(self):
        """Merge selected chunk with next chunk."""
        if not self.selected_chunk_id:
            return
            
        selected_chunk = next((c for c in self.chunks if c.chunk_id == self.selected_chunk_id), None)
        next_chunk = self._get_next_chunk(self.selected_chunk_id)
        
        if not selected_chunk or not next_chunk:
            messagebox.showinfo("Info", "Cannot merge - no adjacent chunk found")
            return
            
        # Merge chunks
        selected_chunk.end_timestamp = next_chunk.end_timestamp
        selected_chunk.duration = selected_chunk.end_timestamp - selected_chunk.start_timestamp
        
        # Combine transcriptions
        if next_chunk.transcription:
            if selected_chunk.transcription:
                selected_chunk.transcription += " " + next_chunk.transcription
            else:
                selected_chunk.transcription = next_chunk.transcription
                
        # Remove next chunk
        self.chunks = [c for c in self.chunks if c.chunk_id != next_chunk.chunk_id]
        
        # Save and refresh
        self._save_chunks()
        self._redraw_canvas()
        
    def merge_with_next_chunk(self):
        """Context menu action to merge with next chunk."""
        self.merge_selected_chunks()
        
    def split_chunk_at_cursor(self):
        """Context menu action to split chunk at cursor."""
        self.add_boundary_at_cursor()
        
    def export_selected_chunk(self):
        """Export selected chunk as separate audio file."""
        if not self.selected_chunk_id or not self.audio_file_path:
            return
            
        selected_chunk = next((c for c in self.chunks if c.chunk_id == self.selected_chunk_id), None)
        if not selected_chunk:
            return
            
        try:
            from tkinter import filedialog
            
            output_path = filedialog.asksaveasfilename(
                title="Export Chunk",
                defaultextension=".wav",
                filetypes=[("WAV files", "*.wav"), ("All files", "*.*")],
                initialname=f"{selected_chunk.chunk_id}.wav"
            )
            
            if not output_path:
                return
                
            # Extract audio segment
            start_sample = int(selected_chunk.start_timestamp * self.sample_rate)
            end_sample = int(selected_chunk.end_timestamp * self.sample_rate)
            
            if self.waveform_data is not None:
                chunk_data = self.waveform_data[start_sample:end_sample]
                
                # Convert back to int16 for WAV export
                chunk_data_int = (chunk_data * 32767).astype(np.int16)
                
                # Write WAV file
                with wave.open(output_path, 'wb') as wav_out:
                    wav_out.setnchannels(1)
                    wav_out.setsampwidth(2)
                    wav_out.setframerate(self.sample_rate)
                    wav_out.writeframes(chunk_data_int.tobytes())
                    
                messagebox.showinfo("Export Complete", f"Chunk exported to:\n{output_path}")
                
        except Exception as e:
            error_msg = f"Failed to export chunk: {e}"
            logging.error(error_msg)
            messagebox.showerror("Export Error", error_msg)
            
    def play_selected_chunk(self):
        """Play only the selected chunk."""
        if not self.selected_chunk_id:
            return
            
        selected_chunk = next((c for c in self.chunks if c.chunk_id == self.selected_chunk_id), None)
        if selected_chunk:
            self.playback.play_from_position(selected_chunk.start_timestamp)
            
            # Stop playback after chunk duration
            def stop_after_duration():
                time.sleep(selected_chunk.duration)
                if self.playback.is_playing:
                    self.playback.stop()
                    
            threading.Thread(target=stop_after_duration, daemon=True).start()