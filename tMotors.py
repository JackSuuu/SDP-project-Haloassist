import time
import busio
import board
from adafruit_tca9548a import TCA9548A
import adafruit_drv2605

def test_channel(ch, mux):
    """Test a single I2C channel for DRV2605 response."""
    try:
        print(f"  -> Initializing channel {ch}...")
        i2c_ch = mux[ch]
        print(f"  -> Channel {ch} initialized. Testing DRV2605...")
        drv = adafruit_drv2605.DRV2605(i2c_ch)
        print(f"  -> DRV2605 initialized on channel {ch}. Sending buzz effect...")
        drv.sequence[0] = adafruit_drv2605.Effect(47)  # buzz
        drv.play()
        time.sleep(0.3)
        drv.stop()
        print(f"  -> DRV2605 responded on channel {ch}.")
        return True
    except Exception as e:
        print(f"  -> Error on channel {ch}: {e}")
        return False

        

def scan_i2c_channels():
    """Scan all I2C channels for DRV2605 devices."""
    try:
        i2c = busio.I2C(board.SCL, board.SDA, timeout=1)
        mux = TCA9548A(i2c)

        found_channels = []

        for ch in range(8):
            print(f"Testing channel {ch}...")
            if test_channel(ch, mux):
                print(f"  -> Device RESPONDED on channel {ch}")
                found_channels.append(ch)
            else:
                print(f"  -> No device on channel {ch}")

        print("Done.")
        print("Channels with response:", found_channels)
        return found_channels

    except Exception as e:
        print(f"Error during I2C scan: {e}")
        return []

if __name__ == "__main__":
    print("Starting I2C channel scan for DRV2605 devices...")
    responsive_channels = scan_i2c_channels()
    if responsive_channels:
        print(f"Responsive channels: {responsive_channels}")
    else:
        print("No responsive channels found.")