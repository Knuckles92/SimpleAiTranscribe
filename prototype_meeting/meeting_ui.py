"""
Dedicated Meeting UI for the Meeting Transcription System.

Provides a separate window interface specifically designed for longer meeting recordings
with pause/resume functionality, real-time monitoring, and session management.
"""

import tkinter as tk
from tkinter import messagebox, ttk
import threading
import logging
import time
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import keyboard
import os

# Import meeting-specific modules
from prototype_meeting.meeting_recorder import MeetingRecorder
from prototype_meeting.session_manager import SessionManager, SessionStatus
from prototype_meeting.file_manager import create_file_manager
from prototype_meeting.config_meeting import meeting_config
from prototype_meeting.meeting_processor import MeetingProcessor
from prototype_meeting.waveform_editor import WaveformEditor

# Import base UI components for consistency  
from settings import settings_manager


class MeetingStatusController:
    """Manages status updates and visual feedback for meeting UI."""
    
    def __init__(self, meeting_ui):
        """Initialize the status controller.
        
        Args:
            meeting_ui: Reference to the MeetingUI instance.
        """
        self.meeting_ui = meeting_ui
    
    def update_status(self, status: str, show_overlay: bool = True):
        """Update status in main window.
        
        Args:
            status: Status message to display.
            show_overlay: Unused parameter (kept for compatibility).
        """
        # Update main window status
        if self.meeting_ui.status_label:
            self.meeting_ui.status_label.config(text=f"Status: {status}")
    
    def clear_status(self):
        """Clear the status display."""
        if self.meeting_ui.status_label:
            self.meeting_ui.status_label.config(text="Status: Ready")
    
    def update_status_with_auto_clear(self, status: str, delay_ms: int = 3000):
        """Update status with automatic clearing after a delay.
        
        Args:
            status: Status message to display.
            delay_ms: Delay in milliseconds before clearing.
        """
        self.update_status(status, show_overlay=False)
        self.meeting_ui.root.after(delay_ms, self.clear_status)


class MeetingUI:
    """
    Dedicated Meeting UI for longer recording sessions with enhanced features:
    - Separate window from main transcription app
    - Meeting control buttons (Start/Pause/Resume/Stop)
    - Real-time session monitoring
    - Progress indicators and status updates
    - Session information panel
    - File management controls
    """
    
    def __init__(self, parent_window=None):
        """Initialize the Meeting UI.
        
        Args:
            parent_window: Optional reference to the main window
        """
        # Create main window
        self.root = tk.Tk()
        self.root.title("Meeting Transcription")
        self.root.geometry(meeting_config.MEETING_WINDOW_SIZE)
        self.root.withdraw()  # Hide initially
        
        # Store parent window reference
        self.parent_window = parent_window
        
        # Initialize components
        self.meeting_recorder = MeetingRecorder()
        self.session_manager = SessionManager()
        self.file_manager = create_file_manager()
        # Share session manager with the processor
        self.meeting_processor = MeetingProcessor(session_manager=self.session_manager)
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Meeting state
        self.current_session_id: Optional[str] = None
        self.is_meeting_active = False
        self.recording_start_time: Optional[datetime] = None
        self.total_pause_time = 0.0
        self.last_pause_start: Optional[datetime] = None
        self.progress_running = False  # Track if progress bar is running
        
        # UI components
        self.setup_ui_components()
        
        # Status management
        self.status_controller = MeetingStatusController(self)
        
        # Setup components
        self._setup_gui()
        self._setup_hotkeys()
        
        # Real-time updates
        self._setup_real_time_updates()
        
        # Handle window close event
        self.root.protocol('WM_DELETE_WINDOW', self.on_closing)
        
        logging.info("Meeting UI initialized")
    
    def setup_ui_components(self):
        """Initialize UI component variables."""
        # Control buttons
        self.start_meeting_button: Optional[ttk.Button] = None
        self.pause_resume_button: Optional[ttk.Button] = None
        self.stop_meeting_button: Optional[ttk.Button] = None
        self.save_meeting_button: Optional[ttk.Button] = None
        
        # Status displays
        self.status_label: Optional[ttk.Label] = None
        self.session_id_label: Optional[ttk.Label] = None
        self.duration_label: Optional[ttk.Label] = None
        self.file_size_label: Optional[ttk.Label] = None
        self.chunk_count_label: Optional[ttk.Label] = None
        
        # Progress indicators
        self.recording_progress: Optional[ttk.Progressbar] = None
        self.processing_progress: Optional[ttk.Progressbar] = None
        
        # Session information
        self.session_info_text: Optional[tk.Text] = None
        
        # Waveform editor
        self.waveform_editor: Optional[WaveformEditor] = None
        
        # Variables
        self.pause_resume_text = tk.StringVar(value="Pause Meeting")
    
    def _setup_gui(self):
        """Create and configure the meeting GUI interface."""
        # Create menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Create Meeting menu
        meeting_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Meeting", menu=meeting_menu)
        meeting_menu.add_command(label="New Meeting", command=self.new_meeting)
        meeting_menu.add_command(label="Load Session...", command=self.load_session)
        meeting_menu.add_separator()
        meeting_menu.add_command(label="Export Meeting...", command=self.export_meeting)
        meeting_menu.add_command(label="Cleanup Session...", command=self.cleanup_session)
        meeting_menu.add_separator()
        meeting_menu.add_command(label="Close", command=self.hide_window)
        
        # Create Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Meeting Settings...", command=self.open_meeting_settings)
        settings_menu.add_command(label="Waveform Style...", command=self.open_waveform_style_settings)
        
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Meeting control buttons (top)
        self._create_control_buttons(main_frame)
        
        # Session status and timing info (middle-top)
        self._create_status_section(main_frame)
        
        # Progress indicators and current status (middle)
        self._create_progress_section(main_frame)
        
        # Waveform editor section (middle-bottom)
        self._create_waveform_editor_section(main_frame)
        
        # Session information and file management (bottom)
        self._create_session_info_section(main_frame)
    
    def _create_control_buttons(self, parent):
        """Create meeting control buttons section."""
        control_frame = ttk.LabelFrame(parent, text="Meeting Controls", padding=10)
        control_frame.pack(pady=5, fill=tk.X)
        
        # Button frame
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)
        
        # Start Meeting button
        self.start_meeting_button = ttk.Button(
            button_frame, 
            text="Start Meeting", 
            command=self.start_meeting,
            width=15
        )
        self.start_meeting_button.pack(side=tk.LEFT, padx=5)
        
        # Pause/Resume button
        self.pause_resume_button = ttk.Button(
            button_frame, 
            textvariable=self.pause_resume_text,
            command=self.toggle_pause_resume,
            state=tk.DISABLED,
            width=15
        )
        self.pause_resume_button.pack(side=tk.LEFT, padx=5)
        
        # Stop Meeting button
        self.stop_meeting_button = ttk.Button(
            button_frame, 
            text="Stop Meeting", 
            command=self.stop_meeting,
            state=tk.DISABLED,
            width=15
        )
        self.stop_meeting_button.pack(side=tk.LEFT, padx=5)
        
        # Save Meeting button
        self.save_meeting_button = ttk.Button(
            button_frame, 
            text="Save Meeting", 
            command=self.save_meeting,
            state=tk.DISABLED,
            width=15
        )
        self.save_meeting_button.pack(side=tk.LEFT, padx=5)
    
    def _create_status_section(self, parent):
        """Create session status and timing info section."""
        status_frame = ttk.LabelFrame(parent, text="Session Status", padding=10)
        status_frame.pack(pady=5, fill=tk.X)
        
        # Status display
        self.status_label = ttk.Label(status_frame, text="Status: Ready", font=('TkDefaultFont', 10, 'bold'))
        self.status_label.pack(anchor=tk.W)
        
        # Session info grid
        info_frame = ttk.Frame(status_frame)
        info_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Row 1
        ttk.Label(info_frame, text="Session ID:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.session_id_label = ttk.Label(info_frame, text="None", foreground="gray")
        self.session_id_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(info_frame, text="Duration:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.duration_label = ttk.Label(info_frame, text="00:00:00")
        self.duration_label.grid(row=0, column=3, sticky=tk.W)
        
        # Row 2
        ttk.Label(info_frame, text="File Size:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.file_size_label = ttk.Label(info_frame, text="0 MB")
        self.file_size_label.grid(row=1, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(info_frame, text="Chunks:").grid(row=1, column=2, sticky=tk.W, padx=(0, 10))
        self.chunk_count_label = ttk.Label(info_frame, text="0")
        self.chunk_count_label.grid(row=1, column=3, sticky=tk.W)
    
    def _create_progress_section(self, parent):
        """Create progress indicators section."""
        progress_frame = ttk.LabelFrame(parent, text="Progress", padding=10)
        progress_frame.pack(pady=5, fill=tk.X)
        
        # Recording progress
        ttk.Label(progress_frame, text="Recording Progress:").pack(anchor=tk.W)
        self.recording_progress = ttk.Progressbar(
            progress_frame, 
            mode='indeterminate', 
            length=400
        )
        self.recording_progress.pack(fill=tk.X, pady=(2, 10))
        
        # Processing progress
        ttk.Label(progress_frame, text="Processing Progress:").pack(anchor=tk.W)
        self.processing_progress = ttk.Progressbar(
            progress_frame, 
            mode='determinate', 
            length=400
        )
        self.processing_progress.pack(fill=tk.X, pady=(2, 0))
    
    def _create_session_info_section(self, parent):
        """Create session information and file management section."""
        info_frame = ttk.LabelFrame(parent, text="Session Information", padding=10)
        info_frame.pack(pady=5, fill=tk.BOTH, expand=True)
        
        # Session info text area with scrollbar
        text_frame = ttk.Frame(info_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create text widget with scrollbar
        self.session_info_text = tk.Text(
            text_frame, 
            height=8, 
            wrap=tk.WORD, 
            relief=tk.SUNKEN,
            font=('TkDefaultFont', 9),
            state=tk.DISABLED
        )
        
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.session_info_text.yview)
        self.session_info_text.configure(yscrollcommand=scrollbar.set)
        
        self.session_info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # File management buttons
        file_frame = ttk.Frame(info_frame)
        file_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            file_frame, 
            text="Export Audio", 
            command=self.export_audio
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            file_frame, 
            text="Export Transcript", 
            command=self.export_transcript
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            file_frame,
            text="Open Session Folder", 
            command=self.open_session_folder
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            file_frame, 
            text="Refresh Info", 
            command=self.refresh_session_info
        ).pack(side=tk.RIGHT)
    
    def _create_waveform_editor_section(self, parent):
        """Create waveform editor section."""
        waveform_frame = ttk.LabelFrame(parent, text="Waveform Editor", padding=10)
        waveform_frame.pack(pady=5, fill=tk.BOTH, expand=True)
        
        # Create waveform editor
        self.waveform_editor = WaveformEditor(
            waveform_frame, 
            self.meeting_processor,
            width=800, 
            height=200
        )
        self.waveform_editor.pack(fill=tk.BOTH, expand=True)
        
        # Editor controls
        editor_controls = ttk.Frame(waveform_frame)
        editor_controls.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(
            editor_controls, 
            text="Load Audio", 
            command=self.load_audio_in_editor
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            editor_controls, 
            text="Auto-Chunk", 
            command=self.auto_chunk_audio
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            editor_controls, 
            text="Export Chunks", 
            command=self.export_audio_chunks
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            editor_controls, 
            text="Transcribe All", 
            command=self.transcribe_all_chunks
        ).pack(side=tk.RIGHT)
    
    def _setup_hotkeys(self):
        """Setup meeting-specific hotkeys."""
        try:
            # Global hotkey to show meeting window
            keyboard.add_hotkey(
                meeting_config.MEETING_HOTKEYS['start_meeting'], 
                self.show_window
            )
            
            # Other hotkeys only work when window is focused
            keyboard.add_hotkey(
                meeting_config.MEETING_HOTKEYS['pause_resume_meeting'], 
                self.toggle_pause_resume
            )
            
            keyboard.add_hotkey(
                meeting_config.MEETING_HOTKEYS['stop_meeting'], 
                self.stop_meeting
            )
            
            keyboard.add_hotkey(
                meeting_config.MEETING_HOTKEYS['save_meeting'], 
                self.save_meeting
            )
            
            logging.info("Meeting hotkeys configured")
            
        except Exception as e:
            logging.warning(f"Failed to setup hotkeys: {e}")
    
    
    def _setup_real_time_updates(self):
        """Setup real-time UI updates."""
        self._update_ui_loop()
    
    def _update_ui_loop(self):
        """Periodic UI update loop."""
        try:
            if self.is_meeting_active and self.current_session_id:
                self._update_session_display()
            
        except Exception as e:
            logging.error(f"Error in UI update loop: {e}")
        
        # Schedule next update
        self.root.after(1000, self._update_ui_loop)  # Update every second
    
    def _update_session_display(self):
        """Update real-time session information display."""
        try:
            # Update duration
            if self.recording_start_time:
                current_time = datetime.now()
                total_elapsed = current_time - self.recording_start_time
                
                # Account for pause time
                pause_time = self.total_pause_time
                if self.last_pause_start:
                    pause_time += (current_time - self.last_pause_start).total_seconds()
                
                recording_duration = total_elapsed.total_seconds() - pause_time
                self._update_duration_display(recording_duration)
            
            # Get session info from recorder
            session_info = self.meeting_recorder.get_session_info()
            if session_info:
                # Update file size
                frame_count = session_info.get('frame_count', 0)
                estimated_size = frame_count * 2048 * 2  # Rough estimate
                self._update_file_size_display(estimated_size)
            
            # Update progress bars
            if self.meeting_recorder.is_recording and not self.meeting_recorder.is_paused:
                if not self.progress_running:
                    self.recording_progress.start(10)
                    self.progress_running = True
            else:
                if self.progress_running:
                    self.recording_progress.stop()
                    self.progress_running = False
            
        except Exception as e:
            logging.error(f"Error updating session display: {e}")
    
    def _update_duration_display(self, seconds: float):
        """Update the duration display."""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.duration_label.config(text=duration_str)
    
    def _update_file_size_display(self, size_bytes: int):
        """Update the file size display."""
        size_mb = size_bytes / (1024 * 1024)
        if size_mb < 1:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_mb:.1f} MB"
        self.file_size_label.config(text=size_str)
    
    def show_window(self):
        """Show the meeting window."""
        self.root.deiconify()
        self.root.state('normal')
        self.root.lift()  # Bring to front
        self.root.focus_force()  # Force focus to this window
        self.root.attributes('-topmost', True)  # Ensure it stays on top temporarily
        # Remove topmost after a short delay to allow normal window behavior
        self.root.after(500, lambda: self.root.attributes('-topmost', False))
        logging.info("Meeting window shown")
    
    def hide_window(self):
        """Hide the meeting window."""
        self.root.withdraw()
        
        # Restore parent window if it was minimized
        if self.parent_window:
            try:
                self.parent_window.state('normal')
                self.parent_window.lift()
            except tk.TclError:
                pass  # Ignore if parent window is no longer available
        
        logging.info("Meeting window hidden")
    
    def on_closing(self):
        """Handle window closing event."""
        if self.is_meeting_active:
            result = messagebox.askyesnocancel(
                "Meeting in Progress", 
                "A meeting is currently active. Do you want to stop it before closing?"
            )
            if result is True:  # Yes - stop meeting
                self.stop_meeting()
                self.hide_window()
            elif result is False:  # No - just hide
                self.hide_window()
            # Cancel - do nothing
        else:
            self.hide_window()
    
    def start_meeting(self):
        """Start a new meeting recording."""
        try:
            # Create new session
            session_id = self.session_manager.create_session(
                name=f"Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            # Start session in session manager
            self.session_manager.start_session(session_id)
            
            # Start recording
            if self.meeting_recorder.start_meeting_recording(session_id):
                self.current_session_id = session_id
                self.is_meeting_active = True
                self.recording_start_time = datetime.now()
                self.total_pause_time = 0.0
                self.last_pause_start = None
                
                # Update UI
                self.start_meeting_button.config(state=tk.DISABLED)
                self.pause_resume_button.config(state=tk.NORMAL)
                self.stop_meeting_button.config(state=tk.NORMAL)
                self.save_meeting_button.config(state=tk.NORMAL)
                self.progress_running = False  # Reset progress state
                
                self.session_id_label.config(text=session_id[-8:], foreground="black")  # Show last 8 chars
                self.status_controller.update_status("Recording meeting...")
                
                # Update session info
                self._update_session_info_display()
                
                logging.info(f"Meeting started - Session: {session_id}")
                
            else:
                messagebox.showerror("Error", "Failed to start meeting recording")
                
        except Exception as e:
            logging.error(f"Failed to start meeting: {e}")
            messagebox.showerror("Error", f"Failed to start meeting: {str(e)}")
    
    def toggle_pause_resume(self):
        """Toggle between pause and resume."""
        if not self.is_meeting_active:
            return
        
        try:
            if self.meeting_recorder.is_paused:
                # Resume recording
                if self.meeting_recorder.resume_recording():
                    self.session_manager.resume_session(self.current_session_id)
                    
                    # Track pause time
                    if self.last_pause_start:
                        self.total_pause_time += (datetime.now() - self.last_pause_start).total_seconds()
                        self.last_pause_start = None
                    
                    self.pause_resume_text.set("Pause Meeting")
                    self.status_controller.update_status("Recording meeting...")
                    
                    logging.info("Meeting resumed")
                else:
                    messagebox.showerror("Error", "Failed to resume recording")
            else:
                # Pause recording
                if self.meeting_recorder.pause_recording():
                    self.session_manager.pause_session(self.current_session_id)
                    
                    self.last_pause_start = datetime.now()
                    self.pause_resume_text.set("Resume Meeting")
                    self.status_controller.update_status("Meeting paused")
                    
                    logging.info("Meeting paused")
                else:
                    messagebox.showerror("Error", "Failed to pause recording")
                    
        except Exception as e:
            logging.error(f"Failed to toggle pause/resume: {e}")
            messagebox.showerror("Error", f"Failed to toggle pause/resume: {str(e)}")
    
    def stop_meeting(self):
        """Stop the current meeting recording."""
        if not self.is_meeting_active:
            return
        
        try:
            # Stop recording
            if self.meeting_recorder.stop_meeting_recording():
                self.session_manager.stop_session(self.current_session_id)
                
                # Update session with the actual audio file path used by the recorder
                session_info = self.meeting_recorder.get_session_info()
                if session_info and session_info.get('audio_file_path'):
                    session = self.session_manager.get_session(self.current_session_id)
                    if session:
                        session.audio_file_path = session_info['audio_file_path']
                        # Save the updated session state
                        self.session_manager.save_session_state()
                
                # Update final pause time if needed
                if self.last_pause_start:
                    self.total_pause_time += (datetime.now() - self.last_pause_start).total_seconds()
                    self.last_pause_start = None
                
                self.is_meeting_active = False
                
                # Update UI
                self.start_meeting_button.config(state=tk.NORMAL)
                self.pause_resume_button.config(state=tk.DISABLED)
                self.stop_meeting_button.config(state=tk.DISABLED)
                self.pause_resume_text.set("Pause Meeting")
                
                # Stop and reset progress bar
                if self.progress_running:
                    self.recording_progress.stop()
                    self.progress_running = False
                
                self.status_controller.update_status("Meeting stopped - Processing...")
                
                # Process meeting in background
                self.executor.submit(self._process_meeting)
                
                logging.info("Meeting stopped")
                
            else:
                messagebox.showerror("Error", "Failed to stop meeting recording")
                
        except Exception as e:
            logging.error(f"Failed to stop meeting: {e}")
            messagebox.showerror("Error", f"Failed to stop meeting: {str(e)}")
    
    def _process_meeting(self):
        """Process meeting audio in background thread."""
        try:
            if not self.current_session_id:
                return
            
            session = self.session_manager.get_session(self.current_session_id)
            if not session or not session.audio_file_path:
                return
            
            # Update status on main thread using thread-safe method
            def safe_update_status(msg):
                try:
                    if self.root and self.root.winfo_exists():
                        self.root.after(0, lambda: self._safe_status_update(msg))
                except (tk.TclError, RuntimeError):
                    # Widget destroyed or main thread not in main loop, ignore
                    pass
            
            safe_update_status("Processing meeting audio...")
            
            # Process with meeting processor
            def progress_callback(message):
                safe_update_status(message)
            
            processed_session_id = self.meeting_processor.process_meeting_audio(
                session.audio_file_path,
                self.current_session_id,
                progress_callback
            )
            
            # Mark session as completed
            self.session_manager.complete_session(self.current_session_id)
            
            # Update UI on main thread using thread-safe method
            try:
                if self.root and self.root.winfo_exists():
                    self.root.after(0, self._on_processing_complete)
            except (tk.TclError, RuntimeError):
                # Widget destroyed or main thread not in main loop, ignore
                pass
            
        except Exception as e:
            # Check if this is a shutdown-related error vs actual processing error
            if "main thread is not in main loop" in str(e) or isinstance(e, (tk.TclError, RuntimeError)):
                logging.debug(f"Meeting processing stopped due to UI shutdown: {e}")
            else:
                logging.error(f"Meeting processing failed: {e}")
                try:
                    if self.root and self.root.winfo_exists():
                        self.root.after(0, lambda: self._on_processing_error(str(e)))
                except (tk.TclError, RuntimeError):
                    # Widget destroyed or main thread not in main loop, ignore
                    pass
    
    def _safe_status_update(self, msg):
        """Safely update status with additional widget existence checks."""
        try:
            if self.status_controller and hasattr(self.status_controller, 'update_status'):
                self.status_controller.update_status(msg)
        except (tk.TclError, RuntimeError, AttributeError):
            # Widget destroyed, controller not available, or other UI error
            pass
    
    def _on_processing_complete(self):
        """Handle processing completion on main thread."""
        self.status_controller.update_status("Meeting completed and saved")
        self.save_meeting_button.config(state=tk.DISABLED)
        self._update_session_info_display()
        
        # Show completion message
        messagebox.showinfo(
            "Meeting Completed", 
            "Meeting has been processed and saved successfully."
        )
    
    def _on_processing_error(self, error_message: str):
        """Handle processing error on main thread."""
        self.status_controller.update_status("Processing failed")
        messagebox.showerror("Processing Error", f"Failed to process meeting: {error_message}")
    
    def save_meeting(self):
        """Manually save the current meeting."""
        if not self.current_session_id:
            return
        
        try:
            # Trigger auto-save checkpoint
            if self.meeting_recorder.auto_save_checkpoint():
                self.status_controller.update_status_with_auto_clear("Meeting saved")
                self._update_session_info_display()
                logging.info("Meeting manually saved")
            else:
                messagebox.showerror("Error", "Failed to save meeting")
                
        except Exception as e:
            logging.error(f"Failed to save meeting: {e}")
            messagebox.showerror("Error", f"Failed to save meeting: {str(e)}")
    
    def new_meeting(self):
        """Start a new meeting (stop current if active)."""
        if self.is_meeting_active:
            result = messagebox.askyesno(
                "Meeting in Progress", 
                "Stop the current meeting and start a new one?"
            )
            if result:
                self.stop_meeting()
                # Wait a moment for processing to start
                self.root.after(1000, self.start_meeting)
        else:
            self.start_meeting()
    
    def load_session(self):
        """Load a previous meeting session."""
        # This would show a dialog to select from available sessions
        messagebox.showinfo("Not Implemented", "Session loading will be implemented in a future update.")
    
    def export_meeting(self):
        """Export current meeting to various formats."""
        if not self.current_session_id:
            messagebox.showwarning("No Session", "No active meeting session to export.")
            return
        
        # This would show export options dialog
        messagebox.showinfo("Not Implemented", "Meeting export will be implemented in a future update.")
    
    def cleanup_session(self):
        """Clean up old meeting sessions."""
        # This would show cleanup options dialog
        messagebox.showinfo("Not Implemented", "Session cleanup will be implemented in a future update.")
    
    def export_audio(self):
        """Export current session audio."""
        if not self.current_session_id:
            messagebox.showwarning("No Session", "No active meeting session.")
            return
        
        messagebox.showinfo("Not Implemented", "Audio export will be implemented in a future update.")
    
    def export_transcript(self):
        """Export current session transcript."""
        if not self.current_session_id:
            messagebox.showwarning("No Session", "No active meeting session.")
            return
        
        messagebox.showinfo("Not Implemented", "Transcript export will be implemented in a future update.")
    
    def open_session_folder(self):
        """Open the current session folder in file explorer."""
        if not self.current_session_id:
            messagebox.showwarning("No Session", "No active meeting session.")
            return
        
        try:
            session = self.session_manager.get_session(self.current_session_id)
            if session and session.session_directory:
                import subprocess
                import platform
                
                if platform.system() == "Windows":
                    os.startfile(session.session_directory)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.call(["open", session.session_directory])
                else:  # Linux
                    subprocess.call(["xdg-open", session.session_directory])
                    
        except Exception as e:
            logging.error(f"Failed to open session folder: {e}")
            messagebox.showerror("Error", f"Failed to open session folder: {str(e)}")
    
    def refresh_session_info(self):
        """Refresh the session information display."""
        self._update_session_info_display()
    
    def _update_session_info_display(self):
        """Update the session information text display."""
        try:
            info_lines = []
            
            if self.current_session_id:
                session = self.session_manager.get_session(self.current_session_id)
                if session:
                    info_lines.extend([
                        f"Session ID: {session.session_id}",
                        f"Name: {session.name}",
                        f"Status: {session.status.value.title()}",
                        f"Created: {session.created_at.strftime('%Y-%m-%d %H:%M:%S') if session.created_at else 'Unknown'}",
                        ""
                    ])
                    
                    if session.started_at:
                        info_lines.append(f"Started: {session.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    if session.ended_at:
                        info_lines.append(f"Ended: {session.ended_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    info_lines.extend([
                        f"Total Duration: {session.get_duration_display()}",
                        f"Recording Duration: {session.recording_duration_seconds:.1f}s",
                        f"Pause Duration: {session.pause_duration_seconds:.1f}s",
                        f"Pause Count: {session.statistics.num_pauses}",
                        ""
                    ])
                    
                    if session.audio_file_path:
                        info_lines.append(f"Audio File: {os.path.basename(session.audio_file_path)}")
                    
                    if session.session_directory:
                        info_lines.append(f"Session Directory: {session.session_directory}")
                    
                    # Add recorder info if available
                    recorder_info = self.meeting_recorder.get_session_info()
                    if recorder_info:
                        info_lines.extend([
                            "",
                            "=== Real-time Info ===",
                            f"Frame Count: {recorder_info.get('frame_count', 0):,}",
                            f"Auto-save Count: {recorder_info.get('auto_save_count', 0)}",
                        ])
                        
                        if recorder_info.get('last_auto_save'):
                            last_save = datetime.fromisoformat(recorder_info['last_auto_save'])
                            info_lines.append(f"Last Auto-save: {last_save.strftime('%H:%M:%S')}")
            else:
                info_lines.append("No active meeting session.")
            
            # Update text widget
            self.session_info_text.config(state=tk.NORMAL)
            self.session_info_text.delete(1.0, tk.END)
            self.session_info_text.insert(tk.END, "\n".join(info_lines))
            self.session_info_text.config(state=tk.DISABLED)
            
        except Exception as e:
            logging.error(f"Error updating session info display: {e}")
    
    def open_meeting_settings(self):
        """Open meeting-specific settings dialog."""
        messagebox.showinfo("Not Implemented", "Meeting settings will be implemented in a future update.")
    
    def open_waveform_style_settings(self):
        """Open waveform style configuration dialog."""
        try:
            from ui.waveform_style_dialog import WaveformStyleDialog
            
            # Load current style via SettingsManager
            current_style, all_configs = settings_manager.load_waveform_style_settings()
            current_config = all_configs.get(current_style, {})
            
            # Create and show dialog
            dialog = WaveformStyleDialog(self.root, current_style, current_config)
            dialog.show()
            
            if getattr(dialog, 'dialog', None) is not None:
                try:
                    dialog.dialog.wait_window(dialog.dialog)
                except Exception:
                    pass
            
            # Reload settings and apply to overlay
            new_style, new_configs = settings_manager.load_waveform_style_settings()
            new_config = new_configs.get(new_style, {})
            if hasattr(self.status_controller, 'waveform_overlay') and self.status_controller.waveform_overlay:
                self.status_controller.waveform_overlay.set_style(new_style, new_config)
                
        except Exception as e:
            logging.error(f"Failed to open waveform style settings: {e}")
            messagebox.showerror("Error", f"Failed to open waveform style settings: {e}")
    
    def load_audio_in_editor(self):
        """Load current session audio into the waveform editor."""
        if not self.current_session_id or not self.waveform_editor:
            messagebox.showwarning("No Session", "No active meeting session or waveform editor.")
            return
        
        try:
            session = self.session_manager.get_session(self.current_session_id)
            if session and session.audio_file_path:
                self.waveform_editor.load_audio_file(session.audio_file_path)
                self.status_controller.update_status_with_auto_clear("Audio loaded in waveform editor")
            else:
                messagebox.showwarning("No Audio", "No audio file available for current session.")
        except Exception as e:
            logging.error(f"Failed to load audio in editor: {e}")
            messagebox.showerror("Error", f"Failed to load audio: {str(e)}")
    
    def auto_chunk_audio(self):
        """Automatically chunk the audio using the meeting processor."""
        if not self.current_session_id:
            messagebox.showwarning("No Session", "No active meeting session.")
            return
        
        try:
            session = self.session_manager.get_session(self.current_session_id)
            if session and session.audio_file_path:
                # Process audio with auto-chunking
                self.status_controller.update_status("Auto-chunking audio...")
                
                def progress_callback(message):
                    try:
                        if self.root and self.root.winfo_exists():
                            self.root.after(0, lambda: self._safe_status_update(message))
                    except (tk.TclError, RuntimeError):
                        pass
                
                # Run in background
                self.executor.submit(self._auto_chunk_background, session.audio_file_path, progress_callback)
            else:
                messagebox.showwarning("No Audio", "No audio file available for current session.")
        except Exception as e:
            logging.error(f"Failed to auto-chunk audio: {e}")
            messagebox.showerror("Error", f"Failed to auto-chunk audio: {str(e)}")
    
    def _auto_chunk_background(self, audio_file_path, progress_callback):
        """Background auto-chunking process."""
        try:
            processed_session_id = self.meeting_processor.process_meeting_audio(
                audio_file_path,
                self.current_session_id,
                progress_callback
            )
            
            # Update waveform editor with new chunks
            try:
                if self.waveform_editor and self.root and self.root.winfo_exists():
                    self.root.after(0, lambda: self.waveform_editor.load_audio_file(audio_file_path))
            except (tk.TclError, RuntimeError):
                pass
            
            try:
                if self.root and self.root.winfo_exists():
                    self.root.after(0, lambda: self._safe_status_update("Auto-chunking completed"))
            except (tk.TclError, RuntimeError):
                pass
            
        except Exception as e:
            logging.error(f"Auto-chunking failed: {e}")
            try:
                if self.root and self.root.winfo_exists():
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Auto-chunking failed: {str(e)}"))
            except (tk.TclError, RuntimeError):
                pass
    
    def export_audio_chunks(self):
        """Export individual audio chunks."""
        messagebox.showinfo("Not Implemented", "Audio chunk export will be implemented in a future update.")
    
    def transcribe_all_chunks(self):
        """Transcribe all audio chunks."""
        messagebox.showinfo("Not Implemented", "Bulk transcription will be implemented in a future update.")
    
    def cleanup(self):
        """Clean up resources."""
        try:
            # Clear status overlay
            self.status_controller.clear_status()
            
            # Stop any active meeting
            if self.is_meeting_active:
                self.meeting_recorder.stop_meeting_recording()
            
            # Cleanup components
            if hasattr(self.status_controller, 'waveform_overlay') and self.status_controller.waveform_overlay:
                self.status_controller.waveform_overlay.cleanup()
            
            if self.meeting_recorder:
                self.meeting_recorder.cleanup()
            
            if self.executor:
                self.executor.shutdown(wait=False)
            
            # Cleanup hotkeys
            try:
                keyboard.unhook_all_hotkeys()
            except Exception as e:
                logging.warning(f"Error cleaning up hotkeys: {e}")
            
            logging.info("Meeting UI cleanup completed")
            
        except Exception as e:
            logging.error(f"Error during Meeting UI cleanup: {e}")
    
    def run(self):
        """Start the meeting UI application loop."""
        self.root.attributes('-topmost', True)
        self.root.deiconify()  # Show window
        
        try:
            self.root.mainloop()
        finally:
            self.cleanup()


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    meeting_ui = MeetingUI()
    meeting_ui.run()