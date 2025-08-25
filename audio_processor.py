"""
Audio processing utilities for handling large audio files.
Includes file size checking and smart audio splitting with silence detection.
"""
import os
import wave
import numpy as np
import tempfile
import logging
from typing import List, Tuple, Optional
from pathlib import Path
from config import config


class AudioProcessor:
    """Handles audio file processing including size checking and smart splitting."""
    
    def __init__(self):
        """Initialize the audio processor."""
        self.temp_files: List[str] = []  # Track temporary files for cleanup
    
    def check_file_size(self, file_path: str) -> Tuple[bool, float]:
        """Check if audio file exceeds size limit.
        
        Args:
            file_path: Path to the audio file to check.
            
        Returns:
            Tuple of (needs_splitting, file_size_mb)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        file_size_bytes = os.path.getsize(file_path)
        file_size_mb = file_size_bytes / (1024 * 1024)  # Convert to MB
        
        needs_splitting = file_size_mb > config.MAX_FILE_SIZE_MB
        
        logging.info(f"Audio file size: {file_size_mb:.2f} MB (limit: {config.MAX_FILE_SIZE_MB} MB)")
        if needs_splitting:
            logging.info("File exceeds size limit, splitting will be required")
        
        return needs_splitting, file_size_mb
    
    def split_audio_file(self, input_file: str, progress_callback: Optional[callable] = None) -> List[str]:
        """Split audio file into smaller chunks using silence detection.
        
        Args:
            input_file: Path to the input audio file.
            progress_callback: Optional callback function for progress updates.
            
        Returns:
            List of paths to the split audio files.
            
        Raises:
            Exception: If splitting fails.
        """
        try:
            if progress_callback:
                progress_callback("Loading audio file...")
            
            # Load audio data
            audio_data, sample_rate = self._load_audio_data(input_file)
            
            if progress_callback:
                progress_callback("Analyzing audio for optimal split points...")
            
            # Find optimal split points using silence detection
            split_points = self._find_split_points(audio_data, sample_rate)
            
            if not split_points:
                # Fallback to time-based splitting if no silence found
                logging.warning("No suitable silence points found, using time-based splitting")
                if progress_callback:
                    progress_callback("Generating time-based splits...")
                split_points = self._generate_time_based_splits(len(audio_data), sample_rate)
            
            if progress_callback:
                progress_callback(f"Creating {len(split_points)} audio chunks...")
            
            # Create chunks
            chunk_files = self._create_chunks(audio_data, sample_rate, split_points, input_file)
            
            logging.info(f"Successfully split audio into {len(chunk_files)} chunks")
            return chunk_files
            
        except Exception as e:
            logging.error(f"Failed to split audio file: {e}")
            self.cleanup_temp_files()
            raise
    
    def _load_audio_data(self, file_path: str) -> Tuple[np.ndarray, int]:
        """Load audio data from WAV file.
        
        Args:
            file_path: Path to the WAV file.
            
        Returns:
            Tuple of (audio_data, sample_rate)
        """
        with wave.open(file_path, 'rb') as wav_file:
            # Get audio parameters
            frames = wav_file.getnframes()
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            
            # Read raw audio data
            raw_data = wav_file.readframes(frames)
            
            # Convert to numpy array based on sample width
            if sample_width == 1:
                audio_data = np.frombuffer(raw_data, dtype=np.uint8)
                # Convert to signed 16-bit for consistency
                audio_data = (audio_data.astype(np.int16) - 128) * 256
            elif sample_width == 2:
                audio_data = np.frombuffer(raw_data, dtype=np.int16)
            elif sample_width == 4:
                audio_data = np.frombuffer(raw_data, dtype=np.int32)
                # Convert to 16-bit for consistency
                audio_data = (audio_data / 65536).astype(np.int16)
            else:
                raise ValueError(f"Unsupported sample width: {sample_width}")
            
            # Handle stereo by taking the average
            if channels == 2:
                audio_data = audio_data.reshape(-1, 2)
                audio_data = np.mean(audio_data, axis=1).astype(np.int16)
            
            return audio_data, sample_rate
    
    def _find_split_points(self, audio_data: np.ndarray, sample_rate: int) -> List[int]:
        """Find optimal split points in audio using silence detection.
        
        Args:
            audio_data: Audio data as numpy array.
            sample_rate: Sample rate of the audio.
            
        Returns:
            List of frame indices where splits should occur.
        """
        # Calculate target chunk size in samples
        max_chunk_samples = int((config.MAX_FILE_SIZE_MB * 1024 * 1024) / 2)  # Rough estimate for 16-bit audio
        min_chunk_samples = int(config.MIN_CHUNK_DURATION_SEC * sample_rate)
        silence_samples = int(config.SILENCE_DURATION_SEC * sample_rate)
        
        # Normalize audio for silence detection
        audio_abs = np.abs(audio_data.astype(np.float32)) / 32767.0
        
        # Apply smoothing to reduce noise in silence detection
        window_size = int(0.1 * sample_rate)  # 100ms window
        if window_size > 1:
            audio_smooth = np.convolve(audio_abs, np.ones(window_size) / window_size, mode='same')
        else:
            audio_smooth = audio_abs
        
        split_points = []
        last_split = 0
        
        # Search for split points
        search_start = min_chunk_samples
        while search_start < len(audio_data):
            # Define search window for split point
            search_end = min(search_start + max_chunk_samples - min_chunk_samples, len(audio_data))
            
            # Find silence in the search window
            best_split = self._find_best_silence(audio_smooth, search_start, search_end, 
                                               silence_samples, sample_rate)
            
            if best_split is not None:
                split_points.append(best_split)
                last_split = best_split
                search_start = best_split + min_chunk_samples
            else:
                # No silence found, force a split at max chunk size
                forced_split = min(last_split + max_chunk_samples, len(audio_data) - 1)
                split_points.append(forced_split)
                last_split = forced_split
                search_start = forced_split + min_chunk_samples
        
        return split_points
    
    def _find_best_silence(self, audio_smooth: np.ndarray, start: int, end: int, 
                          silence_samples: int, sample_rate: int) -> Optional[int]:
        """Find the best silence period in a given range.
        
        Args:
            audio_smooth: Smoothed audio data.
            start: Start index to search.
            end: End index to search.
            silence_samples: Required silence duration in samples.
            sample_rate: Sample rate.
            
        Returns:
            Index of the best split point, or None if no suitable silence found.
        """
        # Search from the end of the range backwards to prefer later splits
        search_range = range(end - silence_samples, start, -int(0.1 * sample_rate))
        
        best_silence_start = None
        best_silence_quality = float('inf')
        
        for i in search_range:
            if i + silence_samples >= len(audio_smooth):
                continue
            
            # Check if this region is silent enough
            silence_region = audio_smooth[i:i + silence_samples]
            max_level = np.max(silence_region)
            avg_level = np.mean(silence_region)
            
            if max_level < config.SILENCE_THRESHOLD:
                # Calculate silence quality (lower is better)
                silence_quality = avg_level + (max_level * 0.1)
                
                if silence_quality < best_silence_quality:
                    best_silence_quality = silence_quality
                    best_silence_start = i + silence_samples // 2  # Split in middle of silence
        
        return best_silence_start
    
    def _generate_time_based_splits(self, total_samples: int, sample_rate: int) -> List[int]:
        """Generate time-based splits as fallback when no silence is found.
        
        Args:
            total_samples: Total number of audio samples.
            sample_rate: Sample rate.
            
        Returns:
            List of split point indices.
        """
        # Target duration per chunk (slightly less than max to account for overhead)
        target_duration = (config.MAX_FILE_SIZE_MB * 0.8) * 1024 * 1024 / (2 * sample_rate)
        target_samples = int(target_duration * sample_rate)
        
        split_points = []
        current_pos = 0
        
        while current_pos + target_samples < total_samples:
            current_pos += target_samples
            split_points.append(current_pos)
        
        return split_points
    
    def _create_chunks(self, audio_data: np.ndarray, sample_rate: int, 
                      split_points: List[int], original_file: str) -> List[str]:
        """Create individual audio chunk files.
        
        Args:
            audio_data: Original audio data.
            sample_rate: Sample rate.
            split_points: List of split point indices.
            original_file: Path to original file for metadata.
            
        Returns:
            List of paths to created chunk files.
        """
        chunk_files = []
        overlap_samples = int(config.OVERLAP_DURATION_SEC * sample_rate)
        
        # Create temporary directory for chunks
        temp_dir = tempfile.mkdtemp(prefix="audio_chunks_")
        
        # Create chunks
        start_idx = 0
        for i, end_idx in enumerate(split_points + [len(audio_data)]):
            # Add overlap to avoid cutting words
            chunk_start = max(0, start_idx - (overlap_samples if i > 0 else 0))
            chunk_end = min(len(audio_data), end_idx + overlap_samples)
            
            chunk_data = audio_data[chunk_start:chunk_end]
            
            # Create chunk filename
            chunk_filename = os.path.join(temp_dir, f"chunk_{i:03d}.wav")
            
            # Save chunk
            self._save_audio_chunk(chunk_data, sample_rate, chunk_filename)
            
            chunk_files.append(chunk_filename)
            self.temp_files.append(chunk_filename)
            
            start_idx = end_idx
            
            logging.info(f"Created chunk {i+1}: {chunk_filename} "
                        f"({len(chunk_data)/sample_rate:.1f}s, "
                        f"{os.path.getsize(chunk_filename)/(1024*1024):.1f}MB)")
        
        self.temp_files.append(temp_dir)  # Add directory for cleanup
        return chunk_files
    
    def _save_audio_chunk(self, audio_data: np.ndarray, sample_rate: int, filename: str):
        """Save audio chunk to WAV file.
        
        Args:
            audio_data: Audio data to save.
            sample_rate: Sample rate.
            filename: Output filename.
        """
        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
    
    def cleanup_temp_files(self):
        """Clean up temporary files created during splitting."""
        for temp_path in self.temp_files:
            try:
                if os.path.isfile(temp_path):
                    os.remove(temp_path)
                elif os.path.isdir(temp_path):
                    import shutil
                    shutil.rmtree(temp_path)
            except Exception as e:
                logging.warning(f"Failed to cleanup temp file {temp_path}: {e}")
        
        self.temp_files.clear()
        logging.info("Temporary files cleaned up")
    
    def combine_transcriptions(self, transcriptions: List[str]) -> str:
        """Combine multiple transcriptions into a single text.
        
        Args:
            transcriptions: List of transcription strings from chunks.
            
        Returns:
            Combined transcription text.
        """
        if not transcriptions:
            return ""
        
        # Remove any empty transcriptions
        valid_transcriptions = [t.strip() for t in transcriptions if t.strip()]
        
        if not valid_transcriptions:
            return ""
        
        # Combine with space separation, handling sentence boundaries
        combined = ""
        for i, transcription in enumerate(valid_transcriptions):
            if i > 0:
                # Add space between chunks, but avoid double spaces
                if not combined.endswith(" ") and not transcription.startswith(" "):
                    combined += " "
            
            combined += transcription
        
        # Clean up any double spaces
        while "  " in combined:
            combined = combined.replace("  ", " ")
        
        return combined.strip()


# Global instance for easy access
audio_processor = AudioProcessor()