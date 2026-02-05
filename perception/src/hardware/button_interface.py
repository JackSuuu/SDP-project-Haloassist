"""
Button Interface
Wraps GPIO button functionality for perception system
"""
import sys
from pathlib import Path

# Add hardware directory to path
hardware_dir = Path(__file__).parent.parent.parent.parent / "hardware"
sys.path.insert(0, str(hardware_dir))


class ButtonInterface:
    """Interface for button input using GPIO"""
    
    def __init__(self, button_pin: int = 5):
        """
        Initialize button interface
        
        Args:
            button_pin: GPIO pin number for button (BCM mode)
        """
        self.button_pin = button_pin
        self.gpio = None
        self._is_pi = self._check_raspberry_pi()
        
        if self._is_pi:
            self._setup_gpio()
    
    def _check_raspberry_pi(self) -> bool:
        """Check if running on Raspberry Pi"""
        try:
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read()
                return 'raspberry pi' in model.lower()
        except:
            return False
    
    def _setup_gpio(self):
        """Setup GPIO for button input"""
        try:
            import RPi.GPIO as GPIO
            self.gpio = GPIO
            # Suppress warnings about GPIO already in use
            self.gpio.setwarnings(False)
            self.gpio.setmode(GPIO.BCM)
            self.gpio.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            print(f"Button initialized on GPIO pin {self.button_pin}")
        except Exception as e:
            print(f"Warning: Failed to setup GPIO: {e}")
            self._is_pi = False
    
    def is_pressed(self) -> bool:
        """
        Check if button is currently pressed
        
        Returns:
            True if button is pressed, False otherwise
        """
        if not self._is_pi or self.gpio is None:
            return False
        
        try:
            # Button is active LOW (pressed = 0)
            return self.gpio.input(self.button_pin) == 0
        except Exception as e:
            print(f"Error reading button: {e}")
            return False
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        if self._is_pi and self.gpio is not None:
            try:
                # Only cleanup if GPIO was properly initialized
                self.gpio.cleanup(self.button_pin)  # Cleanup only this pin
                print("Button GPIO cleaned up")
            except Exception as e:
                print(f"Warning: GPIO cleanup error (likely already cleaned): {e}")
