"""
Meeting-specific audio processing that extends the base AudioProcessor.
Provides enhanced chunking, metadata management, and meeting-specific features.
"""
import os
import json
import uuid
import wave
import numpy as np
import tempfile
import logging
from typing import List, Dict, Tuple, Optional, Union, Any
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

# Import base AudioProcessor
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from audio_processor import AudioProcessor
from prototype_meeting.config_meeting import meeting_config


@dataclass
class ChunkMetadata:
    """Metadata for individual audio chunks."""
    chunk_id: str
    start_timestamp: float  # Start time in seconds from meeting beginning
    end_timestamp: float    # End time in seconds from meeting beginning
    duration: float         # Duration in seconds
    file_path: str          # Path to chunk audio file
    transcription: str = "" # Transcribed text for this chunk
    speaker_info: Dict[str, Any] = None  # Speaker detection data
    topics: List[str] = None             # Identified topics in this chunk
    confidence_score: float = 0.0        # Transcription confidence
    is_silence: bool = False            # Whether chunk is primarily silence
    created_at: str = ""                # When chunk was created
    updated_at: str = ""                # When chunk was last modified
    custom_metadata: Dict[str, Any] = None  # User-defined metadata
    
    def __post_init__(self):
        """Initialize optional fields."""
        if self.speaker_info is None:
            self.speaker_info = {}
        if self.topics is None:
            self.topics = []
        if self.custom_metadata is None:
            self.custom_metadata = {}
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at


@dataclass
class MeetingSession:
    """Meeting session data container."""
    session_id: str
    title: str = ""
    start_time: str = ""
    end_time: str = ""
    total_duration: float = 0.0
    audio_file_path: str = ""
    chunks_dir: str = ""
    metadata_file: str = ""
    chunks: Dict[str, ChunkMetadata] = None
    meeting_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize optional fields."""
        if self.chunks is None:
            self.chunks = {}
        if self.meeting_metadata is None:
            self.meeting_metadata = {}
        if not self.start_time:
            self.start_time = datetime.now().isoformat()


class SessionManager:
    """Manages meeting sessions and their persistence."""
    
    def __init__(self):
        """Initialize the session manager."""
        self.sessions: Dict[str, MeetingSession] = {}
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        meeting_config.ensure_meetings_directory()
        
    def create_session(self, title: str = "", audio_file_path: str = "") -> str:
        """Create a new meeting session.
        
        Args:
            title: Optional title for the meeting session
            audio_file_path: Path to the audio file for this session
            
        Returns:
            Session ID string
        """
        session_id = str(uuid.uuid4())
        timestamp = meeting_config.get_meeting_timestamp()
        
        chunks_dir = meeting_config.get_meeting_chunks_dir(timestamp)
        os.makedirs(chunks_dir, exist_ok=True)
        
        metadata_file = meeting_config.get_meeting_metadata_path(timestamp)
        
        session = MeetingSession(
            session_id=session_id,
            title=title or f"Meeting {timestamp}",
            audio_file_path=audio_file_path,
            chunks_dir=chunks_dir,
            metadata_file=metadata_file
        )
        
        self.sessions[session_id] = session
        self._save_session(session_id)
        
        logging.info(f"Created meeting session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[MeetingSession]:
        """Get a meeting session by ID."""
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, **kwargs):
        """Update session fields."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        self._save_session(session_id)
    
    def _save_session(self, session_id: str):
        """Save session metadata to disk."""
        session = self.sessions[session_id]
        session_data = asdict(session)
        
        with open(session.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
    
    def load_session(self, session_id: str, metadata_file: str) -> bool:
        """Load a session from disk."""
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Reconstruct ChunkMetadata objects
            chunks = {}
            for chunk_id, chunk_data in session_data.get('chunks', {}).items():
                chunks[chunk_id] = ChunkMetadata(**chunk_data)
            session_data['chunks'] = chunks
            
            session = MeetingSession(**session_data)
            self.sessions[session_id] = session
            return True
            
        except Exception as e:
            logging.error(f"Failed to load session {session_id}: {e}")
            return False


class MeetingProcessor(AudioProcessor):
    """Enhanced audio processor for meeting transcription with advanced chunking and metadata."""
    
    def __init__(self):
        """Initialize the meeting processor."""
        super().__init__()
        self.session_manager = SessionManager()
        self.current_session_id: Optional[str] = None
        
    def process_meeting_audio(self, audio_file_path: str, session_id: str = None, 
                            progress_callback: Optional[callable] = None) -> str:
        """Main processing entry point for meeting audio.
        
        Args:
            audio_file_path: Path to the audio file to process
            session_id: Optional existing session ID, creates new if not provided
            progress_callback: Optional callback for progress updates
            
        Returns:
            Session ID for the processed meeting
            
        Raises:
            FileNotFoundError: If audio file doesn't exist
            Exception: If processing fails
        """
        try:
            if progress_callback:
                progress_callback("Initializing meeting processing...")
            
            # Create or get session
            if session_id is None:
                session_id = self.session_manager.create_session(
                    audio_file_path=audio_file_path
                )
            
            self.current_session_id = session_id
            session = self.session_manager.get_session(session_id)
            
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            if progress_callback:
                progress_callback("Loading and analyzing audio...")
            
            # Load audio data
            audio_data, sample_rate = self._load_audio_data(audio_file_path)
            
            # Update session with audio info
            duration = len(audio_data) / sample_rate
            self.session_manager.update_session(
                session_id,
                total_duration=duration,
                audio_file_path=audio_file_path
            )
            
            if progress_callback:
                progress_callback("Performing smart auto-chunking...")
            
            # Perform meeting-specific auto-chunking
            chunk_metadata_list = self.auto_chunk_meeting(audio_data, session_id, sample_rate)
            
            if progress_callback:
                progress_callback(f"Created {len(chunk_metadata_list)} chunks for processing")
            
            logging.info(f"Successfully processed meeting audio into {len(chunk_metadata_list)} chunks")
            return session_id
            
        except Exception as e:
            logging.error(f"Failed to process meeting audio: {e}")
            if progress_callback:
                progress_callback(f"Error: {str(e)}")
            raise
    
    def auto_chunk_meeting(self, audio_data: np.ndarray, session_id: str, 
                          sample_rate: int = None) -> List[ChunkMetadata]:
        """Smart auto-chunking specifically designed for meetings.
        
        Args:
            audio_data: Audio data as numpy array
            session_id: Meeting session ID
            sample_rate: Audio sample rate (auto-detected if None)
            
        Returns:
            List of ChunkMetadata objects for created chunks
        """
        if sample_rate is None:
            sample_rate = meeting_config.MEETING_SAMPLE_RATE
        
        session = self.session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Meeting-specific chunking parameters
        min_chunk_samples = int(meeting_config.MEETING_MIN_CHUNK_MINUTES * 60 * sample_rate)
        max_chunk_samples = int(meeting_config.MEETING_MAX_CHUNK_MINUTES * 60 * sample_rate)
        silence_samples = int(meeting_config.MEETING_SILENCE_DURATION_SEC * sample_rate)
        overlap_samples = int(meeting_config.MEETING_OVERLAP_SECONDS * sample_rate)
        
        # Enhanced silence detection for meetings
        split_points = self._find_meeting_split_points(
            audio_data, sample_rate, min_chunk_samples, max_chunk_samples, silence_samples
        )
        
        # Create chunk files and metadata
        chunk_metadata_list = self._create_meeting_chunks(
            audio_data, sample_rate, split_points, session, overlap_samples
        )
        
        # Update session with chunks
        session.chunks = {chunk.chunk_id: chunk for chunk in chunk_metadata_list}
        self.session_manager._save_session(session_id)
        
        return chunk_metadata_list
    
    def _find_meeting_split_points(self, audio_data: np.ndarray, sample_rate: int,
                                  min_chunk_samples: int, max_chunk_samples: int,
                                  silence_samples: int) -> List[int]:
        """Find optimal split points for meeting audio with enhanced detection."""
        # Normalize audio for analysis
        audio_abs = np.abs(audio_data.astype(np.float32)) / 32767.0
        
        # Apply more sophisticated smoothing for meeting audio
        window_size = int(0.5 * sample_rate)  # 500ms window for meeting analysis
        if window_size > 1:
            audio_smooth = np.convolve(audio_abs, np.ones(window_size) / window_size, mode='same')
        else:
            audio_smooth = audio_abs
        
        split_points = []
        last_split = 0
        
        # Analyze the entire audio for meeting structure
        meeting_structure = self.analyze_meeting_structure(audio_data, sample_rate)
        
        # Use structure analysis to guide chunking
        structure_points = [point['timestamp'] * sample_rate for point in meeting_structure['breakpoints']]
        
        # Search for split points
        search_start = min_chunk_samples
        while search_start < len(audio_data):
            search_end = min(search_start + max_chunk_samples - min_chunk_samples, len(audio_data))
            
            # Prefer structure-based split points when available
            best_split = self._find_best_meeting_split(
                audio_smooth, search_start, search_end, silence_samples,
                sample_rate, structure_points
            )
            
            if best_split is not None:
                split_points.append(best_split)
                last_split = best_split
                search_start = best_split + min_chunk_samples
            else:
                # Force split at max chunk size
                forced_split = min(last_split + max_chunk_samples, len(audio_data) - 1)
                split_points.append(forced_split)
                last_split = forced_split
                search_start = forced_split + min_chunk_samples
        
        return split_points
    
    def _find_best_meeting_split(self, audio_smooth: np.ndarray, start: int, end: int,
                                silence_samples: int, sample_rate: int,
                                structure_points: List[int]) -> Optional[int]:
        """Find the best split point considering meeting structure."""
        # First, check for structure-based breakpoints in the search range
        for struct_point in structure_points:
            if start <= struct_point <= end:
                # Verify there's enough silence around the structure point
                check_start = max(0, int(struct_point - silence_samples // 2))
                check_end = min(len(audio_smooth), int(struct_point + silence_samples // 2))
                
                if check_end > check_start:
                    silence_region = audio_smooth[check_start:check_end]
                    if np.max(silence_region) < meeting_config.MEETING_SILENCE_THRESHOLD:
                        return int(struct_point)
        
        # Fall back to traditional silence detection
        search_range = range(end - silence_samples, start, -int(0.2 * sample_rate))
        
        best_silence_start = None
        best_silence_quality = float('inf')
        
        for i in search_range:
            if i + silence_samples >= len(audio_smooth):
                continue
            
            silence_region = audio_smooth[i:i + silence_samples]
            max_level = np.max(silence_region)
            avg_level = np.mean(silence_region)
            
            if max_level < meeting_config.MEETING_SILENCE_THRESHOLD:
                # Enhanced silence quality scoring for meetings
                silence_quality = avg_level + (max_level * 0.2)
                
                if silence_quality < best_silence_quality:
                    best_silence_quality = silence_quality
                    best_silence_start = i + silence_samples // 2
        
        return best_silence_start
    
    def _create_meeting_chunks(self, audio_data: np.ndarray, sample_rate: int,
                              split_points: List[int], session: MeetingSession,
                              overlap_samples: int) -> List[ChunkMetadata]:
        """Create meeting-specific chunk files with enhanced metadata."""
        chunk_metadata_list = []
        
        # Create chunks with overlap
        start_idx = 0
        for i, end_idx in enumerate(split_points + [len(audio_data)]):
            # Calculate chunk boundaries with overlap
            chunk_start = max(0, start_idx - (overlap_samples if i > 0 else 0))
            chunk_end = min(len(audio_data), end_idx + overlap_samples)
            
            chunk_data = audio_data[chunk_start:chunk_end]
            
            # Create chunk file
            chunk_filename = os.path.join(session.chunks_dir, f"chunk_{i:03d}.wav")
            self._save_audio_chunk(chunk_data, sample_rate, chunk_filename)
            
            # Calculate timestamps
            start_time = start_idx / sample_rate
            end_time = end_idx / sample_rate
            duration = (chunk_end - chunk_start) / sample_rate
            
            # Create chunk metadata
            chunk_metadata = ChunkMetadata(
                chunk_id=str(uuid.uuid4()),
                start_timestamp=start_time,
                end_timestamp=end_time,
                duration=duration,
                file_path=chunk_filename,
                is_silence=self._is_chunk_silence(chunk_data)
            )
            
            chunk_metadata_list.append(chunk_metadata)
            start_idx = end_idx
            
            logging.info(f"Created meeting chunk {i+1}: {duration:.1f}s "
                        f"({start_time:.1f}s - {end_time:.1f}s)")
        
        return chunk_metadata_list
    
    def _is_chunk_silence(self, chunk_data: np.ndarray, threshold: float = None) -> bool:
        """Determine if a chunk is primarily silence."""
        if threshold is None:
            threshold = meeting_config.MEETING_SILENCE_THRESHOLD
        
        # Calculate RMS level
        rms = np.sqrt(np.mean(chunk_data.astype(np.float32) ** 2)) / 32767.0
        return rms < threshold
    
    def add_manual_chunk_boundary(self, timestamp: float) -> str:
        """Add a manual chunk boundary at specific timestamp.
        
        Args:
            timestamp: Time in seconds where to add boundary
            
        Returns:
            ID of the newly created chunk
            
        Raises:
            ValueError: If no current session or timestamp is invalid
        """
        if not self.current_session_id:
            raise ValueError("No active session")
        
        session = self.session_manager.get_session(self.current_session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Find which chunk contains this timestamp
        target_chunk = None
        for chunk in session.chunks.values():
            if chunk.start_timestamp <= timestamp <= chunk.end_timestamp:
                target_chunk = chunk
                break
        
        if not target_chunk:
            raise ValueError(f"No chunk found containing timestamp {timestamp}")
        
        # Split the chunk at the specified timestamp
        return self.split_chunk(target_chunk.chunk_id, timestamp)
    
    def remove_chunk_boundary(self, chunk_id: str) -> bool:
        """Remove an existing chunk boundary by merging with adjacent chunk.
        
        Args:
            chunk_id: ID of the chunk boundary to remove
            
        Returns:
            True if boundary was successfully removed
            
        Raises:
            ValueError: If chunk not found or operation not possible
        """
        if not self.current_session_id:
            raise ValueError("No active session")
        
        session = self.session_manager.get_session(self.current_session_id)
        if not session or chunk_id not in session.chunks:
            raise ValueError("Chunk not found")
        
        target_chunk = session.chunks[chunk_id]
        
        # Find adjacent chunk to merge with (prefer next chunk)
        adjacent_chunk = None
        for chunk in session.chunks.values():
            if abs(chunk.start_timestamp - target_chunk.end_timestamp) < 0.1:
                adjacent_chunk = chunk
                break
        
        if not adjacent_chunk:
            # Try previous chunk
            for chunk in session.chunks.values():
                if abs(chunk.end_timestamp - target_chunk.start_timestamp) < 0.1:
                    adjacent_chunk = chunk
                    break
        
        if not adjacent_chunk:
            raise ValueError("No adjacent chunk found for merging")
        
        # Merge the chunks
        merged_chunk_id = self.merge_chunks([chunk_id, adjacent_chunk.chunk_id])
        return merged_chunk_id is not None
    
    def merge_chunks(self, chunk_ids: List[str]) -> Optional[str]:
        """Combine multiple chunks into a single chunk.
        
        Args:
            chunk_ids: List of chunk IDs to merge
            
        Returns:
            ID of the merged chunk, or None if merge failed
        """
        if not self.current_session_id or not chunk_ids:
            return None
        
        session = self.session_manager.get_session(self.current_session_id)
        if not session:
            return None
        
        # Validate all chunks exist
        chunks_to_merge = []
        for chunk_id in chunk_ids:
            if chunk_id not in session.chunks:
                logging.error(f"Chunk {chunk_id} not found")
                return None
            chunks_to_merge.append(session.chunks[chunk_id])
        
        # Sort chunks by start timestamp
        chunks_to_merge.sort(key=lambda c: c.start_timestamp)
        
        # Load and combine audio data
        combined_audio_data = []
        sample_rate = None
        
        for chunk in chunks_to_merge:
            try:
                chunk_audio, chunk_sample_rate = self._load_audio_data(chunk.file_path)
                if sample_rate is None:
                    sample_rate = chunk_sample_rate
                elif sample_rate != chunk_sample_rate:
                    logging.warning(f"Sample rate mismatch in chunk {chunk.chunk_id}")
                
                combined_audio_data.append(chunk_audio)
            except Exception as e:
                logging.error(f"Failed to load chunk {chunk.chunk_id}: {e}")
                return None
        
        # Combine audio
        merged_audio = np.concatenate(combined_audio_data)
        
        # Create new merged chunk
        merged_chunk_id = str(uuid.uuid4())
        merged_filename = os.path.join(session.chunks_dir, f"merged_{merged_chunk_id[:8]}.wav")
        
        self._save_audio_chunk(merged_audio, sample_rate, merged_filename)
        
        # Create merged metadata
        first_chunk = chunks_to_merge[0]
        last_chunk = chunks_to_merge[-1]
        
        merged_metadata = ChunkMetadata(
            chunk_id=merged_chunk_id,
            start_timestamp=first_chunk.start_timestamp,
            end_timestamp=last_chunk.end_timestamp,
            duration=last_chunk.end_timestamp - first_chunk.start_timestamp,
            file_path=merged_filename,
            transcription=" ".join([c.transcription for c in chunks_to_merge if c.transcription]),
            topics=list(set(sum([c.topics for c in chunks_to_merge], []))),
            custom_metadata={"merged_from": chunk_ids}
        )
        
        # Update session
        session.chunks[merged_chunk_id] = merged_metadata
        
        # Remove old chunks
        for chunk_id in chunk_ids:
            old_chunk = session.chunks.pop(chunk_id)
            try:
                os.remove(old_chunk.file_path)
            except Exception as e:
                logging.warning(f"Failed to delete old chunk file {old_chunk.file_path}: {e}")
        
        self.session_manager._save_session(self.current_session_id)
        
        logging.info(f"Merged {len(chunk_ids)} chunks into {merged_chunk_id}")
        return merged_chunk_id
    
    def split_chunk(self, chunk_id: str, timestamp: float) -> str:
        """Split an existing chunk at the specified timestamp.
        
        Args:
            chunk_id: ID of the chunk to split
            timestamp: Time in seconds where to split (relative to chunk start)
            
        Returns:
            ID of the newly created second chunk
        """
        if not self.current_session_id:
            raise ValueError("No active session")
        
        session = self.session_manager.get_session(self.current_session_id)
        if not session or chunk_id not in session.chunks:
            raise ValueError("Chunk not found")
        
        original_chunk = session.chunks[chunk_id]
        
        # Validate timestamp
        if not (original_chunk.start_timestamp <= timestamp <= original_chunk.end_timestamp):
            raise ValueError("Timestamp outside chunk boundaries")
        
        # Load original audio
        audio_data, sample_rate = self._load_audio_data(original_chunk.file_path)
        
        # Calculate split point in samples
        split_offset = timestamp - original_chunk.start_timestamp
        split_sample = int(split_offset * sample_rate)
        
        # Split audio data
        first_part = audio_data[:split_sample]
        second_part = audio_data[split_sample:]
        
        # Create new chunk for second part
        new_chunk_id = str(uuid.uuid4())
        new_chunk_filename = os.path.join(session.chunks_dir, f"split_{new_chunk_id[:8]}.wav")
        
        # Save both parts
        self._save_audio_chunk(first_part, sample_rate, original_chunk.file_path)  # Overwrite original
        self._save_audio_chunk(second_part, sample_rate, new_chunk_filename)
        
        # Update original chunk metadata
        original_chunk.end_timestamp = timestamp
        original_chunk.duration = timestamp - original_chunk.start_timestamp
        original_chunk.updated_at = datetime.now().isoformat()
        
        # Create new chunk metadata
        new_chunk = ChunkMetadata(
            chunk_id=new_chunk_id,
            start_timestamp=timestamp,
            end_timestamp=original_chunk.end_timestamp,
            duration=original_chunk.end_timestamp - timestamp,
            file_path=new_chunk_filename,
            custom_metadata={"split_from": chunk_id}
        )
        
        # Update session
        session.chunks[new_chunk_id] = new_chunk
        self.session_manager._save_session(self.current_session_id)
        
        logging.info(f"Split chunk {chunk_id} at {timestamp}s, created {new_chunk_id}")
        return new_chunk_id
    
    def get_chunk_metadata(self, chunk_id: str) -> Optional[ChunkMetadata]:
        """Return chunk metadata information.
        
        Args:
            chunk_id: ID of the chunk
            
        Returns:
            ChunkMetadata object or None if not found
        """
        if not self.current_session_id:
            return None
        
        session = self.session_manager.get_session(self.current_session_id)
        if not session:
            return None
        
        return session.chunks.get(chunk_id)
    
    def update_chunk_metadata(self, chunk_id: str, metadata: Dict[str, Any]) -> bool:
        """Update chunk metadata with provided values.
        
        Args:
            chunk_id: ID of the chunk to update
            metadata: Dictionary of metadata fields to update
            
        Returns:
            True if update successful, False otherwise
        """
        if not self.current_session_id:
            return False
        
        session = self.session_manager.get_session(self.current_session_id)
        if not session or chunk_id not in session.chunks:
            return False
        
        chunk = session.chunks[chunk_id]
        
        # Update allowed fields
        updatable_fields = {
            'transcription', 'speaker_info', 'topics', 'confidence_score',
            'custom_metadata'
        }
        
        for key, value in metadata.items():
            if key in updatable_fields and hasattr(chunk, key):
                setattr(chunk, key, value)
        
        chunk.updated_at = datetime.now().isoformat()
        self.session_manager._save_session(self.current_session_id)
        
        return True
    
    def re_transcribe_chunk(self, chunk_id: str, transcriber=None) -> bool:
        """Re-process and transcribe a single chunk.
        
        Args:
            chunk_id: ID of the chunk to re-transcribe
            transcriber: Optional transcriber instance to use
            
        Returns:
            True if re-transcription successful, False otherwise
        """
        if not self.current_session_id:
            return False
        
        session = self.session_manager.get_session(self.current_session_id)
        if not session or chunk_id not in session.chunks:
            return False
        
        chunk = session.chunks[chunk_id]
        
        try:
            # This would integrate with the transcriber when available
            # For now, we'll just log the request
            logging.info(f"Re-transcription requested for chunk {chunk_id}")
            
            # Update metadata
            chunk.updated_at = datetime.now().isoformat()
            self.session_manager._save_session(self.current_session_id)
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to re-transcribe chunk {chunk_id}: {e}")
            return False
    
    def export_chunk_audio(self, chunk_id: str, output_path: str, format: str = "wav") -> bool:
        """Export individual chunk audio to specified format.
        
        Args:
            chunk_id: ID of the chunk to export
            output_path: Path where to save the exported audio
            format: Audio format (currently only supports 'wav')
            
        Returns:
            True if export successful, False otherwise
        """
        if not self.current_session_id:
            return False
        
        session = self.session_manager.get_session(self.current_session_id)
        if not session or chunk_id not in session.chunks:
            return False
        
        chunk = session.chunks[chunk_id]
        
        try:
            if format.lower() == "wav":
                # Simple copy for WAV format
                import shutil
                shutil.copy2(chunk.file_path, output_path)
            else:
                # Future: Add support for other formats using ffmpeg
                logging.warning(f"Format {format} not yet supported, using WAV")
                import shutil
                shutil.copy2(chunk.file_path, output_path)
            
            logging.info(f"Exported chunk {chunk_id} to {output_path}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to export chunk {chunk_id}: {e}")
            return False
    
    def analyze_meeting_structure(self, audio_data: np.ndarray, sample_rate: int = None) -> Dict[str, Any]:
        """Analyze meeting audio to detect natural breakpoints and structure.
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Sample rate (uses default if None)
            
        Returns:
            Dictionary containing meeting structure analysis
        """
        if sample_rate is None:
            sample_rate = meeting_config.MEETING_SAMPLE_RATE
        
        # Normalize audio
        audio_abs = np.abs(audio_data.astype(np.float32)) / 32767.0
        
        # Analysis parameters
        window_size = int(5.0 * sample_rate)  # 5-second analysis windows
        hop_size = int(1.0 * sample_rate)     # 1-second hops
        
        # Calculate energy levels over time
        energy_levels = []
        timestamps = []
        
        for i in range(0, len(audio_data) - window_size, hop_size):
            window = audio_abs[i:i + window_size]
            energy = np.mean(window ** 2)
            energy_levels.append(energy)
            timestamps.append(i / sample_rate)
        
        energy_levels = np.array(energy_levels)
        
        # Detect silence regions (potential breakpoints)
        silence_threshold = meeting_config.MEETING_SILENCE_THRESHOLD
        silence_mask = energy_levels < silence_threshold
        
        # Find extended silence periods
        min_silence_duration = 3.0  # 3 seconds minimum
        min_silence_samples = int(min_silence_duration)
        
        breakpoints = []
        in_silence = False
        silence_start = 0
        
        for i, is_silent in enumerate(silence_mask):
            if is_silent and not in_silence:
                # Start of silence
                in_silence = True
                silence_start = i
            elif not is_silent and in_silence:
                # End of silence
                in_silence = False
                silence_duration = i - silence_start
                
                if silence_duration >= min_silence_samples:
                    # This is a significant silence period
                    breakpoint_time = timestamps[silence_start + silence_duration // 2]
                    breakpoints.append({
                        'timestamp': breakpoint_time,
                        'type': 'silence',
                        'duration': silence_duration,
                        'confidence': min(1.0, silence_duration / (min_silence_samples * 2))
                    })
        
        # Detect energy transitions (speaker changes, topic changes)
        energy_diff = np.abs(np.diff(energy_levels))
        high_diff_threshold = np.percentile(energy_diff, 85)
        
        for i, diff in enumerate(energy_diff):
            if diff > high_diff_threshold and i < len(timestamps):
                breakpoints.append({
                    'timestamp': timestamps[i],
                    'type': 'energy_transition',
                    'magnitude': diff,
                    'confidence': min(1.0, diff / high_diff_threshold)
                })
        
        # Sort breakpoints by timestamp
        breakpoints.sort(key=lambda x: x['timestamp'])
        
        # Calculate overall meeting statistics
        total_duration = len(audio_data) / sample_rate
        avg_energy = np.mean(energy_levels)
        energy_variance = np.var(energy_levels)
        
        structure_analysis = {
            'breakpoints': breakpoints,
            'total_duration': total_duration,
            'average_energy': avg_energy,
            'energy_variance': energy_variance,
            'silence_percentage': np.sum(silence_mask) / len(silence_mask) * 100,
            'recommended_chunks': max(2, min(15, len([bp for bp in breakpoints if bp['confidence'] > 0.5])))
        }
        
        logging.info(f"Meeting structure analysis: {len(breakpoints)} breakpoints found, "
                    f"{structure_analysis['silence_percentage']:.1f}% silence")
        
        return structure_analysis
    
    def get_session_summary(self, session_id: str = None) -> Dict[str, Any]:
        """Get a comprehensive summary of the meeting session.
        
        Args:
            session_id: Optional session ID (uses current if not provided)
            
        Returns:
            Dictionary containing session summary
        """
        if session_id is None:
            session_id = self.current_session_id
        
        if not session_id:
            return {}
        
        session = self.session_manager.get_session(session_id)
        if not session:
            return {}
        
        # Calculate summary statistics
        total_chunks = len(session.chunks)
        total_transcribed = len([c for c in session.chunks.values() if c.transcription])
        total_silence_chunks = len([c for c in session.chunks.values() if c.is_silence])
        
        avg_chunk_duration = np.mean([c.duration for c in session.chunks.values()]) if session.chunks else 0
        
        summary = {
            'session_id': session_id,
            'title': session.title,
            'start_time': session.start_time,
            'end_time': session.end_time,
            'total_duration': session.total_duration,
            'total_chunks': total_chunks,
            'transcribed_chunks': total_transcribed,
            'silence_chunks': total_silence_chunks,
            'average_chunk_duration': avg_chunk_duration,
            'chunks_directory': session.chunks_dir,
            'metadata_file': session.metadata_file,
            'transcription_progress': (total_transcribed / total_chunks * 100) if total_chunks > 0 else 0
        }
        
        return summary
    
    def cleanup_session(self, session_id: str = None, remove_audio: bool = False) -> bool:
        """Clean up session data and temporary files.
        
        Args:
            session_id: Optional session ID (uses current if not provided)
            remove_audio: Whether to remove audio files as well
            
        Returns:
            True if cleanup successful
        """
        if session_id is None:
            session_id = self.current_session_id
        
        if not session_id:
            return False
        
        session = self.session_manager.get_session(session_id)
        if not session:
            return False
        
        try:
            # Clean up chunk files if requested
            if remove_audio:
                for chunk in session.chunks.values():
                    try:
                        if os.path.exists(chunk.file_path):
                            os.remove(chunk.file_path)
                    except Exception as e:
                        logging.warning(f"Failed to remove chunk file {chunk.file_path}: {e}")
                
                # Remove chunks directory if empty
                try:
                    if os.path.exists(session.chunks_dir):
                        os.rmdir(session.chunks_dir)
                except Exception as e:
                    logging.warning(f"Failed to remove chunks directory: {e}")
            
            # Remove from memory
            if session_id in self.session_manager.sessions:
                del self.session_manager.sessions[session_id]
            
            # Clear current session if it was the active one
            if self.current_session_id == session_id:
                self.current_session_id = None
            
            logging.info(f"Cleaned up session {session_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to cleanup session {session_id}: {e}")
            return False
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all available meeting sessions.
        
        Returns:
            List of session summary dictionaries
        """
        sessions = []
        for session_id in self.session_manager.sessions.keys():
            summary = self.get_session_summary(session_id)
            if summary:
                sessions.append(summary)
        
        return sessions


# Global instance for easy access
meeting_processor = MeetingProcessor()