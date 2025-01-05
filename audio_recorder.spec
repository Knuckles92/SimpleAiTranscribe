# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Add whisper model files
import os
import site
import sys
from importlib.util import find_spec

# Find the whisper module location
whisper_spec = find_spec('whisper')
if whisper_spec is None:
    raise ImportError("Could not find whisper module")

model_path = os.path.dirname(whisper_spec.origin)
whisper_files = [(os.path.join(model_path, 'assets'), 'whisper/assets')]

a = Analysis(
    ['audio_recorder.py'],
    pathex=[],
    binaries=[],
    datas=whisper_files,
    hiddenimports=[
        'whisper',
        'numpy',
        'pyaudio',
        'keyboard',
        'openai',
        'pystray',
        'PIL',
        'tkinter',
        'wave',
        'pyperclip'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AudioRecorder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)


