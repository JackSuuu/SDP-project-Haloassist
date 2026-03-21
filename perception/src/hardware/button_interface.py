"""
Button Interface
Wraps gpiozero button functionality for perception system
"""

from run_config import RUN_CONFIG

class ButtonInterface:
    """Interface for button input using gpiozero or keyboard fallback based on platform profile."""

    def __init__(self, button_pin: int = 27, key: str = "b"):
        self.button_pin = button_pin
        self.key = key.lower()
        self._button = None
        self._key_pressed = False
        self._key_listener_thread = None

        platform_profile = RUN_CONFIG.get('platform_profile', 'windows')

        if platform_profile == 'pi':
            try:
                from gpiozero import Button
                self._button = Button(button_pin)
                print(f"Button initialized on GPIO pin {button_pin}")
            except Exception as e:
                print(f"Warning: Failed to setup button: {e}")

        elif platform_profile == 'windows':
            print("Using keyboard fallback for button on Windows.")
            self._start_keyboard_listener()

        else:
            print(f"Unsupported platform profile: {platform_profile}")

    def _start_keyboard_listener(self):
        """Start a thread to listen for keyboard input."""
        from pynput import keyboard

        def on__key_press(key):
            try:
                if key.char and key.char.lower() == self.key:
                    self._key_pressed = True
            except AttributeError:
                pass

        def on_key_release(key):
            try:
                if key.char and key.char.lower() == self.key:
                    self._key_pressed = False
            except AttributeError:
                pass

        def listen():
            with keyboard.Listener(on_press=on__key_press, on_release=on_key_release) as key_listener:
                key_listener.join()

        from threading import Thread
        self._key_listener_thread = Thread(target=listen, daemon=True)
        self._key_listener_thread.start()

    def is_pressed(self) -> bool:
        if self._button is not None:
            return self._button.is_pressed
        return self._key_pressed

    def cleanup(self):
        if self._button is not None:
            self._button.close()
            print("Button cleaned up")
        elif self._key_listener_thread is not None:
            print("Keyboard listener stopped")
