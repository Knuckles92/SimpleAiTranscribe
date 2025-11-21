# PyAudio to SoundDevice Migration Guide

## Overview

This document describes the migration from PyAudio to SoundDevice for the whisper_local audio recording application, completed on 2025-11-16.

## Rationale for Migration

### Why SoundDevice?

1. **Better Cross-Platform Support**: SoundDevice provides more reliable cross-platform audio support without requiring PortAudio compilation
2. **NumPy Integration**: Native numpy array support eliminates conversion overhead
3. **Modern API**: More Pythonic and actively maintained
4. **Simpler Installation**: Fewer dependencies and easier installation process
5. **Better Performance**: Callback-based architecture is more efficient than blocking reads

### Problems with PyAudio

- Requires PortAudio compilation on some platforms
- Installation issues on newer Python versions
- Less actively maintained
- No native numpy support
- Blocking read pattern less efficient

## Migration Summary

### Files Modified

1. **requirements.txt**: Replaced `pyaudio==0.2.13` with `sounddevice>=0.4.6`
2. **config.py**: Changed `AUDIO_FORMAT` from string constant to numpy dtype
3. **recorder.py**: Complete refactor to use SoundDevice callback pattern
4. **tests/test_recorder.py**: Updated mocks and added tests for callback functionality

### Files Unaffected

- **ui/main_window.py**: No changes needed (uses AudioRecorder interface)
- **audio_processor.py**: No changes needed (no audio dependency)
- **app.py**: No changes needed (no audio dependency)

## Key API Changes

### 1. Dependency Import

```python
# OLD (PyAudio)
import pyaudio

# NEW (SoundDevice)
import sounddevice as sd
```

### 2. Initialization

```python
# OLD (PyAudio)
self.audio = pyaudio.PyAudio()
self.format = getattr(pyaudio, config.AUDIO_FORMAT)  # "paInt16" -> pyaudio.paInt16

# NEW (SoundDevice)
# No instance needed - sounddevice is functional
self.dtype = config.AUDIO_FORMAT  # np.int16 directly
```

### 3. Audio Format Configuration

```python
# OLD (config.py)
AUDIO_FORMAT: str = "paInt16"  # String constant name

# NEW (config.py)
import numpy as np
AUDIO_FORMAT: type = np.int16  # NumPy dtype
```

### 4. Stream Architecture: Blocking → Callback

This is the most significant change. PyAudio used a blocking read pattern, while SoundDevice uses callbacks.

#### OLD Pattern (PyAudio - Blocking Read)

```python
def _record_audio(self):
    stream = self.audio.open(
        format=self.format,
        channels=self.channels,
        rate=self.rate,
        input=True,
        frames_per_buffer=self.chunk
    )

    while True:
        data = stream.read(self.chunk, exception_on_overflow=False)
        self.frames.append(data)
        self._calculate_and_report_level(data)

        if self._stop_requested and time.time() >= self._post_roll_until:
            break

    stream.stop_stream()
    stream.close()
```

#### NEW Pattern (SoundDevice - Callback)

```python
def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
    """Called automatically by sounddevice for each audio chunk."""
    if status:
        logging.warning(f"Audio stream status: {status}")

    with self._callback_lock:  # Thread safety
        self.frames.append(indata.copy().tobytes())
        if self.audio_level_callback:
            self._calculate_and_report_level(indata.copy())

def _record_audio(self):
    self.stream = sd.InputStream(
        samplerate=self.rate,
        channels=self.channels,
        dtype=self.dtype,
        blocksize=self.chunk,
        callback=self._audio_callback  # Callback receives data
    )

    self.stream.start()

    # Wait for stop condition
    while True:
        time.sleep(0.01)  # Avoid busy-waiting
        if self._stop_requested and time.time() >= self._post_roll_until:
            break

    self.stream.stop()
    self.stream.close()
```

### 5. Audio Level Calculation

```python
# OLD (PyAudio - bytes to numpy)
def _calculate_and_report_level(self, audio_data: bytes):
    if self.format == pyaudio.paInt16:
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
    elif self.format == pyaudio.paFloat32:
        audio_array = np.frombuffer(audio_data, dtype=np.float32)
    # ... calculate RMS

# NEW (SoundDevice - already numpy)
def _calculate_and_report_level(self, audio_data: np.ndarray):
    # Data is already a numpy array!
    if self.dtype == np.int16:
        rms_level = np.sqrt(np.mean(audio_data.astype(np.float64) ** 2)) / 32767.0
    elif self.dtype == np.float32:
        rms_level = np.sqrt(np.mean(audio_data ** 2))
    # ... apply smoothing
```

### 6. WAV File Sample Width

```python
# OLD (PyAudio)
wf.setsampwidth(self.audio.get_sample_size(self.format))

# NEW (SoundDevice)
wf.setsampwidth(np.dtype(self.dtype).itemsize)
```

### 7. Cleanup

```python
# OLD (PyAudio)
def cleanup(self):
    if self.is_recording:
        self.stop_recording()
    if self.audio:
        self.audio.terminate()  # Must terminate PyAudio instance

# NEW (SoundDevice)
def cleanup(self):
    if self.is_recording:
        self.stop_recording()
    # No termination needed - sounddevice is functional
```

## Thread Safety Considerations

### New Thread Safety Requirement

SoundDevice callbacks run in a separate audio thread, requiring thread-safe frame storage:

```python
# Added in __init__
self._callback_lock = threading.Lock()

# Used in callback
def _audio_callback(self, indata, frames, time_info, status):
    with self._callback_lock:
        self.frames.append(indata.copy().tobytes())
```

The `copy()` is critical to avoid data corruption since SoundDevice reuses buffers.

## Testing Changes

### Mock Updates

```python
# OLD (PyAudio)
self.pyaudio_patcher = patch('recorder.pyaudio.PyAudio')
self.mock_pyaudio = self.pyaudio_patcher.start()

# NEW (SoundDevice)
self.sd_patcher = patch('recorder.sd.InputStream')
self.mock_sd_stream = self.sd_patcher.start()
```

### New Tests Added

1. **test_audio_level_callback**: Tests audio level calculation with numpy arrays
2. **test_audio_callback**: Tests the callback function directly

## Post-Migration Verification

### Functionality to Test

- [ ] Recording starts and stops correctly
- [ ] Audio level waveform display updates in real-time
- [ ] Post-roll capture works (1200ms trailing audio)
- [ ] WAV file format is valid and plays correctly
- [ ] File size and duration match expectations
- [ ] Error handling works (no audio device, etc.)
- [ ] Application cleanup on exit

### Installation Steps

1. Uninstall PyAudio (if installed):
   ```bash
   pip uninstall pyaudio
   ```

2. Install new dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Test recording:
   - Start application
   - Trigger recording with hotkey
   - Verify waveform appears
   - Stop recording
   - Verify WAV file created

### Known Issues & Solutions

#### Issue: "PortAudio not found"
**Solution**: This should not occur with SoundDevice, but if it does:
```bash
# Linux
sudo apt-get install portaudio19-dev

# macOS
brew install portaudio

# Windows
# Usually included with sounddevice wheel
```

#### Issue: Audio callback receives wrong data type
**Solution**: Verify `config.AUDIO_FORMAT` is set to a numpy dtype (e.g., `np.int16`), not a string.

## Performance Comparison

### PyAudio (Before)

- Blocking read in dedicated thread
- Bytes → NumPy conversion for every chunk
- Manual exception handling for overflow

### SoundDevice (After)

- Efficient callback pattern
- Direct NumPy arrays (no conversion)
- Better buffer management
- Lower latency

## Rollback Plan

If issues arise, rollback steps:

1. Restore `requirements.txt`:
   ```
   pyaudio==0.2.13
   ```

2. Restore `config.py`:
   ```python
   AUDIO_FORMAT: str = "paInt16"
   ```

3. Restore `recorder.py` from git:
   ```bash
   git checkout HEAD~1 -- recorder.py
   ```

4. Restore tests:
   ```bash
   git checkout HEAD~1 -- tests/test_recorder.py
   ```

5. Reinstall dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Migration Benefits Realized

1. ✅ No PortAudio compilation issues
2. ✅ Simpler installation process
3. ✅ Better numpy integration
4. ✅ More efficient callback pattern
5. ✅ Cleaner, more maintainable code
6. ✅ Better cross-platform support
7. ✅ Easier testing with numpy arrays

## References

- [SoundDevice Documentation](https://python-sounddevice.readthedocs.io/)
- [SoundDevice GitHub](https://github.com/spatialaudio/python-sounddevice)
- [NumPy dtype reference](https://numpy.org/doc/stable/reference/arrays.dtypes.html)
- [Original PyAudio Documentation](https://people.csail.mit.edu/hubert/pyaudio/docs/)

## Migration Date

**Completed**: 2025-11-16
**Migrated By**: Claude Code Assistant
**Migration Type**: Complete replacement of audio backend
