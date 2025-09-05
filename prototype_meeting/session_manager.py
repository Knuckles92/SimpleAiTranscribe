"""
SessionManager for managing meeting session lifecycle and state.

Handles session creation, lifecycle management, state persistence, and file organization
for meeting recordings with support for pause/resume functionality and crash recovery.
"""

import json
import os
import shutil
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import threading
from contextlib import contextmanager

from .config_meeting import meeting_config


class SessionStatus(Enum):
    """Enumeration for session states."""
    CREATED = "created"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class SessionStatistics:
    """Statistics for a meeting session."""
    total_duration_seconds: float = 0.0
    recording_duration_seconds: float = 0.0
    pause_duration_seconds: float = 0.0
    num_chunks: int = 0
    total_file_size_bytes: int = 0
    audio_file_size_bytes: int = 0
    transcript_file_size_bytes: int = 0
    num_pauses: int = 0
    average_chunk_size_seconds: float = 0.0
    largest_chunk_size_seconds: float = 0.0
    smallest_chunk_size_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionStatistics':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class MeetingSession:
    """Data class to hold meeting session metadata and state."""
    
    # Core identifiers
    session_id: str
    name: str
    timestamp: str
    
    # Session state
    status: SessionStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    
    # File paths
    audio_file_path: Optional[str] = None
    transcript_file_path: Optional[str] = None
    metadata_file_path: Optional[str] = None
    chunks_directory: Optional[str] = None
    session_directory: Optional[str] = None
    
    # Session metadata
    description: str = ""
    tags: List[str] = None
    participants: List[str] = None
    
    # Timing information
    total_duration_seconds: float = 0.0
    recording_duration_seconds: float = 0.0
    pause_duration_seconds: float = 0.0
    pause_start_time: Optional[datetime] = None
    
    # Chunk information
    chunk_files: List[str] = None
    current_chunk_index: int = 0
    
    # Statistics
    statistics: SessionStatistics = None
    
    # Recovery information
    last_saved_at: Optional[datetime] = None
    recovery_data: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values after object creation."""
        if self.tags is None:
            self.tags = []
        if self.participants is None:
            self.participants = []
        if self.chunk_files is None:
            self.chunk_files = []
        if self.statistics is None:
            self.statistics = SessionStatistics()
        if self.recovery_data is None:
            self.recovery_data = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for JSON serialization."""
        data = {
            'session_id': self.session_id,
            'name': self.name,
            'timestamp': self.timestamp,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'last_activity_at': self.last_activity_at.isoformat() if self.last_activity_at else None,
            'audio_file_path': self.audio_file_path,
            'transcript_file_path': self.transcript_file_path,
            'metadata_file_path': self.metadata_file_path,
            'chunks_directory': self.chunks_directory,
            'session_directory': self.session_directory,
            'description': self.description,
            'tags': self.tags,
            'participants': self.participants,
            'total_duration_seconds': self.total_duration_seconds,
            'recording_duration_seconds': self.recording_duration_seconds,
            'pause_duration_seconds': self.pause_duration_seconds,
            'pause_start_time': self.pause_start_time.isoformat() if self.pause_start_time else None,
            'chunk_files': self.chunk_files,
            'current_chunk_index': self.current_chunk_index,
            'statistics': self.statistics.to_dict(),
            'last_saved_at': self.last_saved_at.isoformat() if self.last_saved_at else None,
            'recovery_data': self.recovery_data
        }
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MeetingSession':
        """Create session from dictionary."""
        # Handle datetime fields
        created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        started_at = datetime.fromisoformat(data['started_at']) if data.get('started_at') else None
        ended_at = datetime.fromisoformat(data['ended_at']) if data.get('ended_at') else None
        last_activity_at = datetime.fromisoformat(data['last_activity_at']) if data.get('last_activity_at') else None
        pause_start_time = datetime.fromisoformat(data['pause_start_time']) if data.get('pause_start_time') else None
        last_saved_at = datetime.fromisoformat(data['last_saved_at']) if data.get('last_saved_at') else None
        
        # Handle statistics
        stats_data = data.get('statistics', {})
        statistics = SessionStatistics.from_dict(stats_data) if stats_data else SessionStatistics()
        
        return cls(
            session_id=data['session_id'],
            name=data['name'],
            timestamp=data['timestamp'],
            status=SessionStatus(data['status']),
            created_at=created_at,
            started_at=started_at,
            ended_at=ended_at,
            last_activity_at=last_activity_at,
            audio_file_path=data.get('audio_file_path'),
            transcript_file_path=data.get('transcript_file_path'),
            metadata_file_path=data.get('metadata_file_path'),
            chunks_directory=data.get('chunks_directory'),
            session_directory=data.get('session_directory'),
            description=data.get('description', ''),
            tags=data.get('tags', []),
            participants=data.get('participants', []),
            total_duration_seconds=data.get('total_duration_seconds', 0.0),
            recording_duration_seconds=data.get('recording_duration_seconds', 0.0),
            pause_duration_seconds=data.get('pause_duration_seconds', 0.0),
            pause_start_time=pause_start_time,
            chunk_files=data.get('chunk_files', []),
            current_chunk_index=data.get('current_chunk_index', 0),
            statistics=statistics,
            last_saved_at=last_saved_at,
            recovery_data=data.get('recovery_data', {})
        )
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity_at = datetime.now()
    
    def get_duration_display(self) -> str:
        """Get human-readable duration string."""
        duration = timedelta(seconds=self.total_duration_seconds)
        hours, remainder = divmod(duration.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    
    def is_active(self) -> bool:
        """Check if session is currently active (recording or paused)."""
        return self.status in [SessionStatus.ACTIVE, SessionStatus.PAUSED]


class SessionManager:
    """Manages meeting session lifecycle, state persistence, and file organization."""
    
    def __init__(self, sessions_file: str = "meeting_sessions.json"):
        """Initialize session manager.
        
        Args:
            sessions_file: Path to the sessions persistence file
        """
        self.sessions_file = sessions_file
        self.sessions: Dict[str, MeetingSession] = {}
        self.active_session_id: Optional[str] = None
        self.lock = threading.RLock()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize directories
        self._ensure_directories()
        
        # Load existing sessions
        self.load_session_state()
        
        # Check for crash recovery
        self._perform_crash_recovery()
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        meeting_config.ensure_meetings_directory()
        
        # Create sessions directory
        sessions_dir = os.path.join(meeting_config.MEETINGS_BASE_DIR, "sessions")
        os.makedirs(sessions_dir, exist_ok=True)
        
        # Create backup directory
        backup_dir = os.path.join(meeting_config.MEETINGS_BASE_DIR, "backups")
        os.makedirs(backup_dir, exist_ok=True)
    
    def _get_sessions_file_path(self) -> str:
        """Get full path to sessions file."""
        return os.path.join(meeting_config.MEETINGS_BASE_DIR, self.sessions_file)
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        return str(uuid.uuid4())
    
    def _create_session_directory(self, session_id: str, timestamp: str) -> str:
        """Create and return session directory path."""
        session_dir = os.path.join(meeting_config.MEETINGS_BASE_DIR, "sessions", f"session_{timestamp}_{session_id[:8]}")
        os.makedirs(session_dir, exist_ok=True)
        return session_dir
    
    @contextmanager
    def _session_lock(self):
        """Context manager for thread-safe session operations."""
        with self.lock:
            yield
    
    def create_session(self, name: str = None, description: str = "", 
                      tags: List[str] = None, participants: List[str] = None) -> str:
        """Create a new meeting session.
        
        Args:
            name: Session name (auto-generated if not provided)
            description: Session description
            tags: List of tags for categorization
            participants: List of participant names
            
        Returns:
            Session ID of created session
            
        Raises:
            RuntimeError: If there's already an active session
        """
        with self._session_lock():
            # Check if there's already an active session
            if self.active_session_id and self.get_active_session():
                raise RuntimeError("Cannot create new session while another session is active")
            
            # Generate session data
            session_id = self._generate_session_id()
            timestamp = meeting_config.get_meeting_timestamp()
            
            if name is None:
                name = f"Meeting {timestamp}"
            
            # Don't create session directory structure here - let the meeting recorder set paths
            # The meeting recorder will set the actual audio_file_path
            audio_file_path = None  # Will be set by meeting recorder
            transcript_file_path = None  # Will be set during processing
            metadata_file_path = None  # Will be set by meeting recorder
            chunks_directory = None  # Will be created during processing if needed
            session_dir = None  # Not using session directory structure
            
            # Create session object
            session = MeetingSession(
                session_id=session_id,
                name=name,
                timestamp=timestamp,
                status=SessionStatus.CREATED,
                created_at=datetime.now(),
                audio_file_path=audio_file_path,
                transcript_file_path=transcript_file_path,
                metadata_file_path=metadata_file_path,
                chunks_directory=chunks_directory,
                session_directory=session_dir,
                description=description,
                tags=tags or [],
                participants=participants or []
            )
            
            # Store session
            self.sessions[session_id] = session
            
            # Save state
            self.save_session_state()
            
            self.logger.info(f"Created new session: {session_id} - {name}")
            return session_id
    
    def start_session(self, session_id: str) -> bool:
        """Start recording for a session.
        
        Args:
            session_id: ID of session to start
            
        Returns:
            True if session started successfully
            
        Raises:
            ValueError: If session doesn't exist or is in invalid state
            RuntimeError: If another session is already active
        """
        with self._session_lock():
            if session_id not in self.sessions:
                raise ValueError(f"Session {session_id} does not exist")
            
            session = self.sessions[session_id]
            
            # Check if another session is active
            if self.active_session_id and self.active_session_id != session_id:
                active_session = self.sessions.get(self.active_session_id)
                if active_session and active_session.is_active():
                    raise RuntimeError("Another session is already active")
            
            # Check session state
            if session.status not in [SessionStatus.CREATED, SessionStatus.PAUSED]:
                raise ValueError(f"Cannot start session in {session.status.value} state")
            
            # Update session state
            session.status = SessionStatus.ACTIVE
            session.started_at = datetime.now()
            session.update_activity()
            
            # Handle resume from pause
            if session.pause_start_time:
                pause_duration = (datetime.now() - session.pause_start_time).total_seconds()
                session.pause_duration_seconds += pause_duration
                session.pause_start_time = None
            
            # Set as active session
            self.active_session_id = session_id
            
            # Save state
            self.save_session_state()
            
            self.logger.info(f"Started session: {session_id}")
            return True
    
    def pause_session(self, session_id: str) -> bool:
        """Pause recording for a session.
        
        Args:
            session_id: ID of session to pause
            
        Returns:
            True if session paused successfully
            
        Raises:
            ValueError: If session doesn't exist or is not active
        """
        with self._session_lock():
            if session_id not in self.sessions:
                raise ValueError(f"Session {session_id} does not exist")
            
            session = self.sessions[session_id]
            
            if session.status != SessionStatus.ACTIVE:
                raise ValueError(f"Cannot pause session in {session.status.value} state")
            
            # Update session state
            session.status = SessionStatus.PAUSED
            session.pause_start_time = datetime.now()
            session.statistics.num_pauses += 1
            session.update_activity()
            
            # Save state
            self.save_session_state()
            
            self.logger.info(f"Paused session: {session_id}")
            return True
    
    def resume_session(self, session_id: str) -> bool:
        """Resume recording for a paused session.
        
        Args:
            session_id: ID of session to resume
            
        Returns:
            True if session resumed successfully
            
        Raises:
            ValueError: If session doesn't exist or is not paused
        """
        with self._session_lock():
            if session_id not in self.sessions:
                raise ValueError(f"Session {session_id} does not exist")
            
            session = self.sessions[session_id]
            
            if session.status != SessionStatus.PAUSED:
                raise ValueError(f"Cannot resume session in {session.status.value} state")
            
            # Calculate pause duration
            if session.pause_start_time:
                pause_duration = (datetime.now() - session.pause_start_time).total_seconds()
                session.pause_duration_seconds += pause_duration
                session.pause_start_time = None
            
            # Update session state
            session.status = SessionStatus.ACTIVE
            session.update_activity()
            
            # Save state
            self.save_session_state()
            
            self.logger.info(f"Resumed session: {session_id}")
            return True
    
    def stop_session(self, session_id: str, save_immediately: bool = True) -> bool:
        """Stop recording and finalize a session.
        
        Args:
            session_id: ID of session to stop
            save_immediately: Whether to save session state immediately
            
        Returns:
            True if session stopped successfully
            
        Raises:
            ValueError: If session doesn't exist or is not active/paused
        """
        with self._session_lock():
            if session_id not in self.sessions:
                raise ValueError(f"Session {session_id} does not exist")
            
            session = self.sessions[session_id]
            
            if session.status not in [SessionStatus.ACTIVE, SessionStatus.PAUSED]:
                raise ValueError(f"Cannot stop session in {session.status.value} state")
            
            # Handle final pause duration if paused
            if session.status == SessionStatus.PAUSED and session.pause_start_time:
                pause_duration = (datetime.now() - session.pause_start_time).total_seconds()
                session.pause_duration_seconds += pause_duration
                session.pause_start_time = None
            
            # Update session state
            session.status = SessionStatus.STOPPED
            session.ended_at = datetime.now()
            session.update_activity()
            
            # Calculate total duration
            if session.started_at:
                session.total_duration_seconds = (session.ended_at - session.started_at).total_seconds()
                session.recording_duration_seconds = session.total_duration_seconds - session.pause_duration_seconds
            
            # Clear active session
            if self.active_session_id == session_id:
                self.active_session_id = None
            
            # Update statistics
            self._update_session_statistics(session)
            
            # Save state if requested
            if save_immediately:
                self.save_session_state()
            
            self.logger.info(f"Stopped session: {session_id}")
            return True
    
    def complete_session(self, session_id: str) -> bool:
        """Mark a session as completed after processing.
        
        Args:
            session_id: ID of session to complete
            
        Returns:
            True if session completed successfully
        """
        with self._session_lock():
            if session_id not in self.sessions:
                raise ValueError(f"Session {session_id} does not exist")
            
            session = self.sessions[session_id]
            session.status = SessionStatus.COMPLETED
            session.update_activity()
            
            # Final statistics update
            self._update_session_statistics(session)
            
            self.save_session_state()
            
            self.logger.info(f"Completed session: {session_id}")
            return True
    
    def get_session(self, session_id: str) -> Optional[MeetingSession]:
        """Get session by ID.
        
        Args:
            session_id: ID of session to retrieve
            
        Returns:
            MeetingSession object or None if not found
        """
        return self.sessions.get(session_id)
    
    def get_active_session(self) -> Optional[MeetingSession]:
        """Get currently active session.
        
        Returns:
            Active MeetingSession or None if no session is active
        """
        if not self.active_session_id:
            return None
        
        session = self.sessions.get(self.active_session_id)
        if session and session.is_active():
            return session
        
        # Clean up stale active session reference
        self.active_session_id = None
        return None
    
    def get_session_history(self, limit: int = None, 
                           status_filter: List[SessionStatus] = None) -> List[MeetingSession]:
        """Get list of all sessions, optionally filtered.
        
        Args:
            limit: Maximum number of sessions to return
            status_filter: List of statuses to include
            
        Returns:
            List of MeetingSession objects sorted by creation time (newest first)
        """
        sessions = list(self.sessions.values())
        
        # Filter by status if requested
        if status_filter:
            sessions = [s for s in sessions if s.status in status_filter]
        
        # Sort by creation time (newest first)
        sessions.sort(key=lambda s: s.created_at or datetime.min, reverse=True)
        
        # Apply limit if specified
        if limit:
            sessions = sessions[:limit]
        
        return sessions
    
    def get_session_statistics(self, session_id: str) -> Optional[SessionStatistics]:
        """Get detailed statistics for a session.
        
        Args:
            session_id: ID of session
            
        Returns:
            SessionStatistics object or None if session not found
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Update statistics before returning
        self._update_session_statistics(session)
        return session.statistics
    
    def _update_session_statistics(self, session: MeetingSession):
        """Update statistics for a session."""
        stats = session.statistics
        
        # Update basic timing stats
        stats.total_duration_seconds = session.total_duration_seconds
        stats.recording_duration_seconds = session.recording_duration_seconds
        stats.pause_duration_seconds = session.pause_duration_seconds
        stats.num_pauses = session.statistics.num_pauses  # Preserve existing count
        
        # Update chunk statistics
        stats.num_chunks = len(session.chunk_files)
        if session.chunk_files:
            # Calculate chunk durations (would need actual file analysis)
            # For now, estimate based on total duration
            if stats.num_chunks > 0:
                stats.average_chunk_size_seconds = stats.recording_duration_seconds / stats.num_chunks
        
        # Update file size statistics
        try:
            if session.audio_file_path and os.path.exists(session.audio_file_path):
                stats.audio_file_size_bytes = os.path.getsize(session.audio_file_path)
            
            if session.transcript_file_path and os.path.exists(session.transcript_file_path):
                stats.transcript_file_size_bytes = os.path.getsize(session.transcript_file_path)
            
            stats.total_file_size_bytes = stats.audio_file_size_bytes + stats.transcript_file_size_bytes
            
            # Add chunk files sizes
            if session.chunks_directory and os.path.exists(session.chunks_directory):
                chunk_sizes = []
                for chunk_file in session.chunk_files:
                    chunk_path = os.path.join(session.chunks_directory, chunk_file)
                    if os.path.exists(chunk_path):
                        chunk_size = os.path.getsize(chunk_path)
                        stats.total_file_size_bytes += chunk_size
                        chunk_sizes.append(chunk_size)
                
                if chunk_sizes:
                    stats.largest_chunk_size_seconds = max(chunk_sizes) / (44100 * 2)  # Rough estimate
                    stats.smallest_chunk_size_seconds = min(chunk_sizes) / (44100 * 2)  # Rough estimate
        
        except (OSError, IOError) as e:
            self.logger.warning(f"Error updating file statistics for session {session.session_id}: {e}")
    
    def save_session_state(self):
        """Save current session state to persistence file."""
        try:
            sessions_data = {
                'active_session_id': self.active_session_id,
                'last_saved': datetime.now().isoformat(),
                'sessions': {sid: session.to_dict() for sid, session in self.sessions.items()}
            }
            
            sessions_file_path = self._get_sessions_file_path()
            
            # Create backup of existing file
            if os.path.exists(sessions_file_path):
                backup_path = f"{sessions_file_path}.backup"
                shutil.copy2(sessions_file_path, backup_path)
            
            # Write new state
            with open(sessions_file_path, 'w', encoding='utf-8') as f:
                json.dump(sessions_data, f, indent=2, ensure_ascii=False)
            
            # Update last saved time for all sessions
            for session in self.sessions.values():
                session.last_saved_at = datetime.now()
            
            self.logger.debug("Saved session state")
            
        except Exception as e:
            self.logger.error(f"Error saving session state: {e}")
            raise
    
    def load_session_state(self):
        """Load session state from persistence file."""
        sessions_file_path = self._get_sessions_file_path()
        
        if not os.path.exists(sessions_file_path):
            self.logger.info("No existing session state file found")
            return
        
        try:
            with open(sessions_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load sessions
            sessions_data = data.get('sessions', {})
            self.sessions = {}
            
            for session_id, session_data in sessions_data.items():
                try:
                    session = MeetingSession.from_dict(session_data)
                    self.sessions[session_id] = session
                except Exception as e:
                    self.logger.error(f"Error loading session {session_id}: {e}")
            
            # Restore active session
            self.active_session_id = data.get('active_session_id')
            
            # Validate active session still exists and is valid
            if self.active_session_id:
                active_session = self.sessions.get(self.active_session_id)
                if not active_session or not active_session.is_active():
                    self.active_session_id = None
            
            self.logger.info(f"Loaded {len(self.sessions)} sessions from state file")
            
        except Exception as e:
            self.logger.error(f"Error loading session state: {e}")
            # Try to load from backup
            self._try_load_backup()
    
    def _try_load_backup(self):
        """Try to load from backup file if main file is corrupted."""
        backup_path = f"{self._get_sessions_file_path()}.backup"
        
        if not os.path.exists(backup_path):
            return
        
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load sessions from backup
            sessions_data = data.get('sessions', {})
            for session_id, session_data in sessions_data.items():
                try:
                    session = MeetingSession.from_dict(session_data)
                    self.sessions[session_id] = session
                except Exception as e:
                    self.logger.error(f"Error loading session {session_id} from backup: {e}")
            
            self.logger.info(f"Loaded {len(self.sessions)} sessions from backup file")
            
        except Exception as e:
            self.logger.error(f"Error loading from backup: {e}")
    
    def _perform_crash_recovery(self):
        """Check for and recover from application crashes during recording."""
        recovered_count = 0
        
        for session in self.sessions.values():
            if session.status == SessionStatus.ACTIVE:
                # Session was active during crash - mark as error and try to recover
                self.logger.warning(f"Detected crashed session: {session.session_id}")
                
                session.status = SessionStatus.ERROR
                session.ended_at = datetime.now()
                session.recovery_data['crash_detected'] = True
                session.recovery_data['crash_time'] = datetime.now().isoformat()
                
                # Try to recover partial recording if files exist
                if session.audio_file_path and os.path.exists(session.audio_file_path):
                    # File exists, attempt to calculate actual duration
                    try:
                        file_size = os.path.getsize(session.audio_file_path)
                        # Rough estimate: 44100 Hz * 2 bytes * 1 channel = ~88KB per second
                        estimated_duration = file_size / (44100 * 2)
                        session.recording_duration_seconds = estimated_duration
                        session.total_duration_seconds = estimated_duration
                        
                        session.recovery_data['recovered_audio_size'] = file_size
                        session.recovery_data['estimated_duration'] = estimated_duration
                        
                        self.logger.info(f"Recovered partial audio for session {session.session_id}")
                        
                    except Exception as e:
                        self.logger.error(f"Error during crash recovery for {session.session_id}: {e}")
                
                recovered_count += 1
        
        # Clear active session reference after crash recovery
        if recovered_count > 0:
            self.active_session_id = None
            self.save_session_state()
            self.logger.info(f"Crash recovery completed: {recovered_count} sessions recovered")
    
    def cleanup_session(self, session_id: str, remove_files: bool = False) -> bool:
        """Clean up temporary files and optionally remove all session files.
        
        Args:
            session_id: ID of session to clean up
            remove_files: Whether to remove all session files (default: False)
            
        Returns:
            True if cleanup successful
            
        Raises:
            ValueError: If session doesn't exist
        """
        with self._session_lock():
            if session_id not in self.sessions:
                raise ValueError(f"Session {session_id} does not exist")
            
            session = self.sessions[session_id]
            
            try:
                # Remove temporary files
                temp_patterns = ["temp_*", "*.tmp", "processing_*"]
                if session.chunks_directory and os.path.exists(session.chunks_directory):
                    for pattern in temp_patterns:
                        for temp_file in Path(session.chunks_directory).glob(pattern):
                            temp_file.unlink()
                            self.logger.debug(f"Removed temp file: {temp_file}")
                
                # Remove all session files if requested
                if remove_files and session.session_directory and os.path.exists(session.session_directory):
                    shutil.rmtree(session.session_directory)
                    self.logger.info(f"Removed session directory: {session.session_directory}")
                    
                    # Remove session from memory
                    del self.sessions[session_id]
                    
                    # Clear active session if this was it
                    if self.active_session_id == session_id:
                        self.active_session_id = None
                    
                    self.save_session_state()
                
                return True
                
            except Exception as e:
                self.logger.error(f"Error during cleanup of session {session_id}: {e}")
                return False
    
    def get_sessions_summary(self) -> Dict[str, Any]:
        """Get summary statistics across all sessions.
        
        Returns:
            Dictionary with summary statistics
        """
        total_sessions = len(self.sessions)
        active_sessions = len([s for s in self.sessions.values() if s.is_active()])
        completed_sessions = len([s for s in self.sessions.values() if s.status == SessionStatus.COMPLETED])
        
        total_duration = sum(s.total_duration_seconds for s in self.sessions.values())
        total_recording_time = sum(s.recording_duration_seconds for s in self.sessions.values())
        
        total_file_size = sum(s.statistics.total_file_size_bytes for s in self.sessions.values())
        
        return {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'completed_sessions': completed_sessions,
            'total_duration_seconds': total_duration,
            'total_recording_seconds': total_recording_time,
            'total_file_size_bytes': total_file_size,
            'average_session_duration': total_duration / total_sessions if total_sessions > 0 else 0,
            'sessions_by_status': {
                status.value: len([s for s in self.sessions.values() if s.status == status])
                for status in SessionStatus
            }
        }
    
    def export_session_data(self, output_file: str, session_ids: List[str] = None):
        """Export session data to JSON file.
        
        Args:
            output_file: Path to output JSON file
            session_ids: List of specific session IDs to export (None for all)
        """
        sessions_to_export = self.sessions
        
        if session_ids:
            sessions_to_export = {sid: session for sid, session in self.sessions.items() 
                                if sid in session_ids}
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'sessions': {sid: session.to_dict() for sid, session in sessions_to_export.items()},
            'summary': self.get_sessions_summary()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Exported {len(sessions_to_export)} sessions to {output_file}")