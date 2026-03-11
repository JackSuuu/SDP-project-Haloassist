"""
Button Interface
Wraps gpiozero button functionality for perception system
"""


class ButtonInterface:
    """Interface for button input using gpiozero"""
    
    def __init__(self, button_pin: int = 27):
        self.button_pin = button_pin
        self._button = None
        self._is_pi = False
        
        try:
            from gpiozero import Button
            self._button = Button(button_pin)
            self._is_pi = True
            print(f"Button initialized on GPIO pin {button_pin}")
        except Exception as e:
            print(f"Warning: Failed to setup button: {e}")
    
    def is_pressed(self) -> bool:
        if self._button is None:
            return False
        return self._button.is_pressed
    
    def cleanup(self):
        if self._button is not None:
            self._button.close()
            print("Button cleaned up")
