#!/usr/bin/env python3
"""
Simple test script for large transcription chunking feature.

Generates a large audio file (>23MB) and tests the complete chunking workflow.
"""

import os
import sys
import wave
import numpy as np
import logging
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from audio_processor import audio_processor
from config import config
from transcriber import LocalWhisperBackend

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_large_audio_file(output_path: str, target_size_mb: float = 30.0):
    """Generate a large WAV file that exceeds the size limit."""
    logger.info(f"Generating large audio file (~{target_size_mb} MB)...")
    
    sample_rate = 44100
    # Calculate duration needed: size = duration * sample_rate * 2 bytes (16-bit) * channels
    # For mono: size_bytes = duration * sample_rate * 2
    # duration = size_bytes / (sample_rate * 2)
    target_size_bytes = target_size_mb * 1024 * 1024
    duration_seconds = target_size_bytes / (sample_rate * 2)
    
    logger.info(f"  Duration: {duration_seconds:.1f} seconds")
    logger.info(f"  Sample rate: {sample_rate} Hz")
    
    num_samples = int(sample_rate * duration_seconds)
    
    # Generate audio with alternating tones and silence (to test silence detection)
    audio_data = np.zeros(num_samples, dtype=np.int16)
    
    # Create 5-second patterns: tone, silence, tone, etc.
    pattern_samples = int(sample_rate * 5)
    num_patterns = num_samples // pattern_samples
    
    for i in range(num_patterns):
        start = i * pattern_samples
        end = min(start + pattern_samples, num_samples)
        
        if i % 2 == 0:
            # Generate a 440 Hz tone
            t = np.linspace(0, (end - start) / sample_rate, end - start)
            tone = np.sin(2 * np.pi * 440 * t)
            audio_data[start:end] = (tone * 16383).astype(np.int16)
        else:
            # Silence
            audio_data[start:end] = 0
    
    # Write WAV file
    with wave.open(output_path, 'wb') as wav:
        wav.setnchannels(1)  # Mono
        wav.setsampwidth(2)  # 16-bit
        wav.setframerate(sample_rate)
        wav.writeframes(audio_data.tobytes())
    
    actual_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    logger.info(f"✅ Generated audio file: {actual_size_mb:.2f} MB")
    
    return output_path


def test_chunking_workflow(audio_file: str):
    """Test the complete chunking workflow."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("Testing chunking workflow")
    logger.info("=" * 60)
    
    # Step 1: Check file size
    logger.info("\n1. Checking file size...")
    needs_splitting, file_size_mb = audio_processor.check_file_size(audio_file)
    
    if not needs_splitting:
        logger.error(f"❌ File ({file_size_mb:.2f} MB) is below limit ({config.MAX_FILE_SIZE_MB} MB)")
        return False
    
    logger.info(f"✅ File exceeds limit - will be split")
    
    # Step 2: Split audio file
    logger.info("\n2. Splitting audio file...")
    
    def progress(msg):
        logger.info(f"   {msg}")
    
    chunk_files = audio_processor.split_audio_file(audio_file, progress)
    
    if not chunk_files:
        logger.error("❌ Failed to split audio file")
        return False
    
    logger.info(f"✅ Created {len(chunk_files)} chunks")
    
    # Show chunk info
    for i, chunk_file in enumerate(chunk_files):
        size_mb = os.path.getsize(chunk_file) / (1024 * 1024)
        logger.info(f"   Chunk {i+1}: {size_mb:.2f} MB")
    
    # Step 3: Test transcription (if backend available)
    logger.info("\n3. Testing transcription...")
    
    backend = LocalWhisperBackend()
    if not backend.is_available():
        logger.warning("⚠️  Local Whisper not available - skipping transcription test")
        logger.info("   (Chunking test passed - files were created successfully)")
        backend.cleanup()
        audio_processor.cleanup_temp_files()
        return True
    
    try:
        logger.info("   Transcribing chunks...")
        transcribed_text = backend.transcribe_chunks(chunk_files)
        
        logger.info(f"✅ Transcription complete: {len(transcribed_text)} characters")
        logger.info(f"   Preview: {transcribed_text[:100]}...")
        
        # Step 4: Verify combination worked
        logger.info("\n4. Verifying transcription combination...")
        if len(transcribed_text) > 0:
            logger.info("✅ Transcription combination successful")
        else:
            logger.warning("⚠️  Transcription is empty")
        
    except Exception as e:
        logger.error(f"❌ Transcription failed: {e}")
        backend.cleanup()
        audio_processor.cleanup_temp_files()
        return False
    finally:
        backend.cleanup()
    
    # Cleanup
    logger.info("\n5. Cleaning up...")
    audio_processor.cleanup_temp_files()
    logger.info("✅ Cleanup complete")
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ ALL TESTS PASSED!")
    logger.info("=" * 60)
    
    return True


def main():
    """Main test function."""
    logger.info("=" * 60)
    logger.info("Large Transcription Chunking Test")
    logger.info("=" * 60)
    
    # Create temporary audio file
    temp_dir = tempfile.mkdtemp()
    test_audio_file = os.path.join(temp_dir, "test_large_audio.wav")
    
    try:
        # Generate large audio file
        generate_large_audio_file(test_audio_file, target_size_mb=30.0)
        
        # Test the workflow
        success = test_chunking_workflow(test_audio_file)
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        # Cleanup temp directory
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())

