"""
Speech Interface
Wraps speech-to-text functionality for perception system.
Supports both fixed-duration and button-held recording modes.
"""
import sys
from pathlib import Path
from typing import Optional, Callable

# Add hardware directory to path
hardware_dir = Path(__file__).parent.parent.parent.parent / "hardware"
sys.path.insert(0, str(hardware_dir))


class SpeechInterface:
    """Interface for speech-to-text using Vosk"""
    
    def __init__(self, model_path: str = "/home/ubuntu/vosk-model/vosk-model-small-en-us-0.15"):
        """
        Initialize speech interface
        
        Args:
            model_path: Path to Vosk model
        """
        self.model_path = model_path
        self.stt_module = None
        self._is_available = self._initialize_stt()
    
    def _initialize_stt(self) -> bool:
        """Initialize speech-to-text module"""
        try:
            import stt
            self.stt_module = stt
            print(f"Speech interface initialized with model: {self.model_path}")
            return True
        except ImportError:
            print("Warning: STT module not available. Speech recognition disabled.")
            return False
        except Exception as e:
            print(f"Warning: Failed to initialize STT: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if speech recognition is available"""
        return self._is_available
    
    def listen(self, duration: int = 3) -> Optional[str]:
        """
        Listen for speech input (fixed duration – legacy).
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Recognized text or None
        """
        if not self._is_available or self.stt_module is None:
            print("Speech recognition not available")
            return None
        
        try:
            text = self.stt_module.listen(duration)
            return text if text else None
        except Exception as e:
            print(f"Error during speech recognition: {e}")
            return None

    def listen_while_pressed(self, button_check_fn: Callable[[], bool]) -> Optional[str]:
        """
        Listen as long as *button_check_fn()* returns True.
        
        This removes fixed-duration latency – the recording length
        matches exactly how long the user holds the button.
        
        Args:
            button_check_fn: Callable returning True while button is held.
            
        Returns:
            Recognized text or None
        """
        if not self._is_available or self.stt_module is None:
            print("Speech recognition not available")
            return None
        
        try:
            text = self.stt_module.listen_while_button_pressed(button_check_fn)
            return text if text else None
        except AttributeError:
            # Fallback to fixed-duration if the stt module lacks the new function
            print("Warning: listen_while_button_pressed not available, falling back to fixed duration")
            return self.listen(duration=3)
        except Exception as e:
            print(f"Error during speech recognition: {e}")
            return None
