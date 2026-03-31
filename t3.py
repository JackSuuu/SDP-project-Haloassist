import smbus
import time

DEVICE_BUS = 3          # /dev/i2c-1
MUX_ADDR = 0x70         # TCA9548A default address

bus = smbus.SMBus(DEVICE_BUS)

def select_channel(channel):
    """Select a single channel on the TCA9548A (0-7)."""
    if channel < 0 or channel > 7:
        raise ValueError("Channel must be 0-7")
    bus.write_byte(MUX_ADDR, 1 << channel)  # write 1<<channel to control register

def scan_i2c():
    """Scan the I2C bus and return addresses."""
    found = []
    for addr in range(0x03, 0x78):  # valid 7-bit I2C addresses
        try:
            bus.read_byte(addr)
            found.append(addr)
        except OSError:
            pass
    return found

# --- Scan root bus ---
print("Scanning root bus...")
root_devices = scan_i2c()
print("Found:", [hex(a) for a in root_devices])

if MUX_ADDR not in root_devices:
    print("ERROR: MUX not found")
    exit(1)

print("Initializing MUX and scanning channels...")
all_devices = {}

for ch in range(8):
    select_channel(ch)
    time.sleep(0.05)  # small delay after switching
    addresses = scan_i2c()
    # remove the mux address itself
    devices = [a for a in addresses if a != MUX_ADDR]
    all_devices[ch] = devices
    print(f"Channel {ch} devices:", [hex(d) for d in devices])

print("\nDone. All channel scan results:")
for ch, devs in all_devices.items():
    print(f"Channel {ch}: {[hex(d) for d in devs]}")
