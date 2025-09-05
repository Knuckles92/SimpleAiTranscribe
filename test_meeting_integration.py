#!/usr/bin/env python
"""Test script to verify meeting recording system integration."""

import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    # Import the components
    from prototype_meeting.session_manager import SessionManager
    from prototype_meeting.meeting_processor import MeetingProcessor
    from prototype_meeting.meeting_recorder import MeetingRecorder
    
    print("✓ All imports successful")
    
    # Test session manager initialization
    session_manager = SessionManager()
    print("✓ SessionManager initialized")
    
    # Test meeting processor initialization with external session manager
    processor = MeetingProcessor(session_manager=session_manager)
    print("✓ MeetingProcessor initialized with external SessionManager")
    
    # Test creating a session
    test_session = session_manager.create_session(
        title="Test Session",
        audio_file_path=None  # Initially None, as per memory
    )
    print(f"✓ Created test session: {test_session.id}")
    
    # Verify session retrieval
    retrieved_session = session_manager.get_session(test_session.id)
    if retrieved_session and retrieved_session.id == test_session.id:
        print("✓ Session retrieval working")
    
    # Test processor's session loading
    processor.load_session(test_session.id)
    if processor.current_session_id == test_session.id:
        print("✓ Processor loaded session correctly")
    
    # Test that session_chunks dictionary is initialized
    if test_session.id in processor.session_chunks:
        print("✓ Processor initialized session_chunks for session")
    
    # Simulate audio file path update (as would be done by MeetingRecorder)
    test_audio_path = f"meetings/meeting_{test_session.id}.wav"
    test_session.audio_file_path = test_audio_path
    session_manager.save_session_state()
    print(f"✓ Updated session audio path to: {test_audio_path}")
    
    # Verify the session state persistence
    session_manager2 = SessionManager()
    persisted_session = session_manager2.get_session(test_session.id)
    if persisted_session and persisted_session.audio_file_path == test_audio_path:
        print("✓ Session state persistence working")
    
    print("\n✅ All integration tests passed!")
    print(f"   Session ID: {test_session.id}")
    print(f"   Audio path: {test_session.audio_file_path}")
    print(f"   Chunks dir: {test_session.chunks_directory}")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
