# Overlay Display Fix - Implementation Summary

## Problem
Transcription overlays were not displaying during any state (recording, processing, transcribing) in the PyQt6 application.

## Root Cause
The automatic status → overlay state mapping that existed in the old Tkinter app was lost during the PyQt6 refactor. Specifically:

1. **Missing Status Mapping**: The old `UIStatusController.update_status()` automatically showed/hid overlays based on status messages
2. **Hardcoded State**: `overlay_qt.py:show_at_cursor()` always set `STATE_RECORDING` regardless of actual state
3. **No State Transitions**: Status updates for "Processing" and "Transcribing" didn't trigger overlay state changes
4. **Race Conditions**: Direct overlay calls bypassed the signal/slot system

## Changes Made

### 1. UIController - Added Status-Based Overlay Management
**File**: `ui_qt/ui_controller.py:170-193`

Enhanced `set_status()` method to automatically map status messages to overlay states:

- **"Recording"** → Shows overlay in `STATE_RECORDING`
- **"Processing"** → Shows overlay in `STATE_PROCESSING`
- **"Transcribing"** → Shows overlay in `STATE_TRANSCRIBING`
- **"complete", "ready", "failed", "error"** → Hides overlay

This mirrors the old Tkinter app's automatic overlay management behavior.

### 2. Overlay - Accept State Parameter
**File**: `ui_qt/overlay_qt.py:314-334`

Modified `show_at_cursor()` to accept optional `state` parameter:

```python
def show_at_cursor(self, state: Optional[str] = None):
```

- If `state` is provided, uses it
- Otherwise, defaults to `STATE_RECORDING` only if currently `IDLE`
- Prevents hardcoding of states

### 3. UIController - Enhanced Signal Handlers
**Files**: `ui_qt/ui_controller.py:111-133`

Updated internal signal handlers to properly show overlays:

**`_on_internal_record_started()`**:
- Shows overlay with `STATE_RECORDING` if not visible
- Sets state if already visible

**`_on_internal_record_stopped()`**:
- Shows overlay with `STATE_PROCESSING` if not visible
- Sets state if already visible

**`_on_internal_transcription()`**:
- Hides overlay when transcription completes

### 4. ApplicationController - Removed Direct Overlay Call
**File**: `app_qt.py:119-125`

Removed direct `show_overlay()` call from `start_recording()`:
- Signal handlers now manage overlay visibility
- Prevents race conditions
- Ensures proper state management

## How It Works Now

### Recording Flow
1. User presses record button
2. `UIController.start_recording()` called
3. `record_started` signal emitted
4. `_on_internal_record_started()` shows overlay with `STATE_RECORDING`
5. Overlay appears near cursor with waveform animation

### Processing Flow
1. Recording stops
2. `record_stopped` signal emitted
3. `_on_internal_record_stopped()` shows overlay with `STATE_PROCESSING`
4. Overlay shows rotating spinner

### Transcription Flow
1. `_transcribe_audio()` emits `status_update` signal with "Transcribing..."
2. `set_status()` receives status
3. Detects "Transcribing" keyword
4. Shows/updates overlay to `STATE_TRANSCRIBING`
5. Overlay shows pulsing circles

### Completion Flow
1. Transcription completes
2. `set_status("Transcription complete!")` called
3. Detects "complete" keyword
4. Automatically hides overlay

## Testing Checklist

- [ ] Start recording → Overlay appears with waveform animation
- [ ] Stop recording → Overlay transitions to spinner (Processing)
- [ ] During transcription → Overlay shows pulsing circles (Transcribing)
- [ ] After transcription → Overlay disappears
- [ ] Cancel recording → Overlay shows shrinking X
- [ ] Large file processing → Overlay shows "Processing large file"
- [ ] Error handling → Overlay hides on error

## Comparison to Old Tkinter App

| Feature | Old Tkinter App | New PyQt6 App (Fixed) |
|---------|----------------|----------------------|
| Status → Overlay Mapping | ✓ `update_status()` | ✓ `set_status()` |
| Auto-show on state change | ✓ Automatic | ✓ Automatic |
| State transitions | ✓ All states | ✓ All states |
| Signal-based updates | ✗ Direct calls | ✓ Signal/slot |

## Notes

- The fix restores parity with the old Tkinter implementation
- Uses PyQt6 signal/slot architecture for thread safety
- Status updates now automatically control overlay visibility
- No manual overlay management needed in application code

## Files Modified

1. `ui_qt/ui_controller.py` - Added status-based overlay management
2. `ui_qt/overlay_qt.py` - Made `show_at_cursor()` accept state parameter
3. `app_qt.py` - Removed direct overlay call from `start_recording()`
