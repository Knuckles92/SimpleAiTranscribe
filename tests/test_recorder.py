"""
Unit tests for the recorder module.
"""
import unittest
import tempfile
import os
import wave
from unittest.mock import patch, MagicMock

from recorder import AudioRecorder
from config import config


class TestAudioRecorder(unittest.TestCase):
    """Test cases for the AudioRecorder class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_audio_file = os.path.join(self.temp_dir, "test_audio.wav")
        
        # Mock pyaudio to avoid actual audio hardware
        self.pyaudio_patcher = patch('recorder.pyaudio.PyAudio')
        self.mock_pyaudio = self.pyaudio_patcher.start()
        
        # Create recorder instance
        self.recorder = AudioRecorder()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.pyaudio_patcher.stop()
        
        if os.path.exists(self.test_audio_file):
            os.remove(self.test_audio_file)
        os.rmdir(self.temp_dir)
        
        if hasattr(self.recorder, 'cleanup'):
            self.recorder.cleanup()
    
    def test_initialization(self):
        """Test recorder initialization."""
        self.assertFalse(self.recorder.is_recording)
        self.assertEqual(self.recorder.frames, [])
        self.assertEqual(self.recorder.chunk, config.CHUNK_SIZE)
        self.assertEqual(self.recorder.channels, config.CHANNELS)
        self.assertEqual(self.recorder.rate, config.SAMPLE_RATE)
    
    def test_start_recording(self):
        """Test starting recording."""
        result = self.recorder.start_recording()
        self.assertTrue(result)
        self.assertTrue(self.recorder.is_recording)
        self.assertEqual(self.recorder.frames, [])
    
    def test_start_recording_already_recording(self):
        """Test starting recording when already recording."""
        self.recorder.is_recording = True
        result = self.recorder.start_recording()
        self.assertFalse(result)
    
    def test_stop_recording(self):
        """Test stopping recording."""
        # Start recording first
        self.recorder.start_recording()
        
        # Stop recording
        result = self.recorder.stop_recording()
        self.assertTrue(result)
        self.assertFalse(self.recorder.is_recording)
    
    def test_stop_recording_not_recording(self):
        """Test stopping recording when not recording."""
        result = self.recorder.stop_recording()
        self.assertFalse(result)
    
    def test_has_recording_data(self):
        """Test checking for recording data."""
        # Initially no data
        self.assertFalse(self.recorder.has_recording_data())
        
        # Add some fake data
        self.recorder.frames = [b'fake_audio_data']
        self.assertTrue(self.recorder.has_recording_data())
    
    def test_clear_recording_data(self):
        """Test clearing recording data."""
        # Add some fake data
        self.recorder.frames = [b'fake_audio_data']
        
        # Clear data
        self.recorder.clear_recording_data()
        self.assertEqual(self.recorder.frames, [])
        self.assertFalse(self.recorder.has_recording_data())
    
    def test_get_recording_duration(self):
        """Test getting recording duration."""
        # No data initially
        self.assertEqual(self.recorder.get_recording_duration(), 0.0)
        
        # Add fake frames
        # Each frame is chunk_size samples, so duration = num_frames * chunk_size / sample_rate
        self.recorder.frames = [b'x' * 100] * 10  # 10 frames of 100 bytes each
        expected_duration = (10 * config.CHUNK_SIZE) / config.SAMPLE_RATE
        self.assertEqual(self.recorder.get_recording_duration(), expected_duration)
    
    def test_save_recording_no_data(self):
        """Test saving recording with no data."""
        result = self.recorder.save_recording(self.test_audio_file)
        self.assertFalse(result)
        self.assertFalse(os.path.exists(self.test_audio_file))
    
    def test_save_recording_with_data(self):
        """Test saving recording with data."""
        # Add fake audio data
        fake_data = b'fake_audio_data_chunk'
        self.recorder.frames = [fake_data] * 5
        
        # Mock the wave module
        with patch('recorder.wave.open') as mock_wave_open:
            mock_wave_file = MagicMock()
            mock_wave_open.return_value.__enter__.return_value = mock_wave_file
            
            result = self.recorder.save_recording(self.test_audio_file)
            
            self.assertTrue(result)
            mock_wave_open.assert_called_once_with(self.test_audio_file, 'wb')
            mock_wave_file.setnchannels.assert_called_once_with(config.CHANNELS)
            mock_wave_file.setframerate.assert_called_once_with(config.SAMPLE_RATE)
            mock_wave_file.writeframes.assert_called_once_with(fake_data * 5)
    
    def test_save_recording_default_filename(self):
        """Test saving recording with default filename."""
        self.recorder.frames = [b'fake_data']
        
        with patch('recorder.wave.open') as mock_wave_open:
            mock_wave_file = MagicMock()
            mock_wave_open.return_value.__enter__.return_value = mock_wave_file
            
            result = self.recorder.save_recording()
            
            self.assertTrue(result)
            mock_wave_open.assert_called_once_with(config.RECORDED_AUDIO_FILE, 'wb')


if __name__ == '__main__':
    unittest.main() 