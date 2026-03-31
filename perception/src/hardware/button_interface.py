"""
Button Interface
Wraps gpiozero button functionality with automatic fallback to keyboard
"""

class ButtonInterface:
    def __init__(self, button_pin: int = 27, key: str = "b"):
        self.button_pin = button_pin
        self.key = key.lower()
        self._button = None
        self._key_pressed = False
        self._key_listener_thread = None

        # Try GPIO first
        try:
            from gpiozero import Button
            self._button = Button(button_pin)
            print(f"Button initialized on GPIO pin {button_pin}")
        except Exception as e:
            print(f"GPIO setup failed ({e}), falling back to keyboard.")
            self._start_keyboard_listener()

    def _start_keyboard_listener(self):
        import sys
        import tty
        import termios
        import select
        import time

        def listen():
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setcbreak(fd)
                while True:
                    r, _, _ = select.select([sys.stdin], [], [], 0.05)
                    if r:
                        ch = sys.stdin.read(1)
                        if ch.lower() == self.key:
                            self._key_pressed = True
                            time.sleep(0.05)
                            self._key_pressed = False
            except Exception as e:
                print(f"[KeyboardFallback] Error: {e}")
            finally:
                try:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                except Exception:
                    pass

        from threading import Thread
        self._key_listener_thread = Thread(target=listen, daemon=True)
        self._key_listener_thread.start()
        print("Using keyboard fallback (tap 'b' to record).")

    def is_pressed(self) -> bool:
        if self._button is not None:
            return self._button.is_pressed
        return self._key_pressed

    def cleanup(self):
        if self._button is not None:
            self._button.close()
            print("Button cleaned up")
