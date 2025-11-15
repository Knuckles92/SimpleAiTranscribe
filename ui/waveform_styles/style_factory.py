"""
Factory for creating and managing waveform overlay styles.
"""
from typing import Dict, Type, List, Optional
from tkinter import Canvas
from .base_style import BaseWaveformStyle


class WaveformStyleFactory:
    """Factory class for creating waveform overlay styles."""
    
    _styles: Dict[str, Type[BaseWaveformStyle]] = {}
    
    @classmethod
    def register_style(cls, style_class: Type[BaseWaveformStyle]):
        """Register a new waveform style.
        
        Args:
            style_class: Style class that inherits from BaseWaveformStyle
        """
        if not issubclass(style_class, BaseWaveformStyle):
            raise ValueError(f"Style class {style_class} must inherit from BaseWaveformStyle")
        
        # Create a temporary instance to get the name
        temp_instance = style_class(None, 100, 100, {})
        style_name = temp_instance.name
        cls._styles[style_name] = style_class
    
    @classmethod
    def get_available_styles(cls) -> List[str]:
        """Get list of available style names.
        
        Returns:
            List of style names
        """
        return list(cls._styles.keys())
    
    @classmethod
    def get_style_info(cls, style_name: str) -> Dict[str, str]:
        """Get information about a specific style.
        
        Args:
            style_name: Name of the style
            
        Returns:
            Dictionary with style information (name, display_name, description)
        """
        if style_name not in cls._styles:
            raise ValueError(f"Unknown style: {style_name}")
        
        style_class = cls._styles[style_name]
        temp_instance = style_class(None, 100, 100, {})
        
        return {
            'name': temp_instance.name,
            'display_name': temp_instance.display_name,
            'description': temp_instance.description
        }
    
    @classmethod
    def create_style(cls, style_name: str, canvas: Canvas, width: int, height: int, 
                    config: Optional[Dict] = None) -> BaseWaveformStyle:
        """Create an instance of the specified style.
        
        Args:
            style_name: Name of the style to create
            canvas: Canvas to draw on
            width: Canvas width
            height: Canvas height
            config: Style-specific configuration
            
        Returns:
            Instance of the requested style
            
        Raises:
            ValueError: If style name is not recognized
        """
        if style_name not in cls._styles:
            available_styles = ', '.join(cls.get_available_styles())
            raise ValueError(f"Unknown style '{style_name}'. Available styles: {available_styles}")
        
        style_class = cls._styles[style_name]
        
        # Use default config if none provided
        if config is None:
            config = style_class.get_default_config()
        
        return style_class(canvas, width, height, config)
    
    @classmethod
    def get_default_config(cls, style_name: str) -> Dict:
        """Get default configuration for a style.
        
        Args:
            style_name: Name of the style
            
        Returns:
            Default configuration dictionary
        """
        if style_name not in cls._styles:
            raise ValueError(f"Unknown style: {style_name}")
        
        return cls._styles[style_name].get_default_config()
    
    @classmethod
    def get_preview_config(cls, style_name: str) -> Dict:
        """Get preview configuration for a style.
        
        Args:
            style_name: Name of the style
            
        Returns:
            Preview configuration dictionary
        """
        if style_name not in cls._styles:
            raise ValueError(f"Unknown style: {style_name}")
        
        return cls._styles[style_name].get_preview_config()


def register_style(style_class: Type[BaseWaveformStyle]):
    """Decorator for registering waveform styles.
    
    Args:
        style_class: Style class to register
        
    Returns:
        The same style class (for decorator usage)
    """
    WaveformStyleFactory.register_style(style_class)
    return style_class