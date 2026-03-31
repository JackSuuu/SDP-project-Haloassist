"""
Button Interface
Wraps gpiozero button functionality with automatic fallback to keyboard.
"""

class ButtonInterface:
    def __init__(self, button_pin: int = 13, pull_up: bool = False, key: str = "b"):
        self.button_pin = button_pin
        self.key = key.lower()
        self._button = None
        self._key_pressed = False
        self._key_listener_thread = None

        # Try GPIO first
        try:
            from gpiozero import Button
            self._button = Button(button_pin, pull_up=pull_up)
            print(f"Button initialized on GPIO pin {button_pin} (pull_up={pull_up})")
        except Exception as e:
            print(f"GPIO setup failed ({e}), falling back to keyboard.")
            self._start_keyboard_listener()

    def _start_keyboard_listener(self):
        from pynput import keyboard

        def on_key_press(key):
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
            with keyboard.Listener(on_press=on_key_press, on_release=on_key_release) as listener:
                listener.join()

        from threading import Thread
        self._key_listener_thread = Thread(target=listen, daemon=True)
        self._key_listener_thread.start()
        print("Using keyboard fallback.")

    def is_pressed(self) -> bool:
        if self._button is not None:
            return self._button.is_pressed
        return self._key_pressed

    def cleanup(self):
        if self._button is not None:
            self._button.close()
            print("Button cleaned up")
