"""
Waveform overlay styles package.
Contains different visual styles for the waveform overlay system.
"""

from .base_style import BaseWaveformStyle
from .style_factory import WaveformStyleFactory

# Import all style implementations to ensure they're registered
from . import modern_style
from . import retro_style
from . import minimalist_style
from . import spectrum_style
from . import particle_style
from . import neon_matrix_style
from . import galaxy_warp_style

__all__ = [
    'BaseWaveformStyle', 
    'WaveformStyleFactory',
    'modern_style',
    'retro_style', 
    'minimalist_style',
    'spectrum_style',
    'particle_style',
    'neon_matrix_style',
    'galaxy_warp_style'
]