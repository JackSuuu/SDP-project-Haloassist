"""
Button Interface
Handles button input for system control
"""
import time

try:
    import RPi.GPIO as GPIO
    RPI_AVAILABLE = True
except ImportError:
    RPI_AVAILABLE = False


class ButtonInterface:
    """
    Button interface for starting/stopping detection
    Wraps external hardware button_press() function
    """
    
    def __init__(self, button_pin: int = 5, simulation_mode: bool = None):
        """
        Initialize button interface
        
        Args:
            button_pin: GPIO pin for button (default: 5)
            simulation_mode: Force simulation mode (None = auto-detect)
        """
        self.button_pin = button_pin
        self.simulation_mode = not RPI_AVAILABLE if simulation_mode is None else simulation_mode
        self._button_pressed = False
        
        if not self.simulation_mode:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            # Setup interrupt for button press
            GPIO.add_event_detect(self.button_pin, GPIO.FALLING, 
                                callback=self._button_callback, bouncetime=300)
    
    def _button_callback(self, channel):
        """Callback for button press interrupt"""
        self._button_pressed = True
    
    def button_press(self) -> bool:
        """
        Check if button has been pressed
        This wraps the external button_press() hardware function
        
        Returns:
            True if button was pressed since last check
        
        TODO: Replace with actual external hardware function call
        Example: return your_hardware_lib.button_press()
        """
        if self.simulation_mode:
            return False
        
        # Using internal GPIO implementation
        pressed = self._button_pressed
        self._button_pressed = False
        return pressed
    
    def wait_for_button(self, timeout: float = None) -> bool:
        """
        Wait for button press
        
        Args:
            timeout: Maximum time to wait in seconds (None = infinite)
            
        Returns:
            True if button was pressed, False if timeout
        """
        if self.simulation_mode:
            print("[BUTTON] Waiting for button press (simulation mode)...")
            time.sleep(0.1)
            return True
        
        start_time = time.time()
        while True:
            if self._button_pressed:
                self._button_pressed = False
                return True
            
            if timeout and (time.time() - start_time) > timeout:
                return False
            
            time.sleep(0.01)
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        if not self.simulation_mode:
            GPIO.cleanup(self.button_pin)
