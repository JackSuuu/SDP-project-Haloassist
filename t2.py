import time
from adafruit_extended_bus import ExtendedI2C
from adafruit_tca9548a import TCA9548A
import smbus

DEVICE_BUS = 3
DEVICE_ADDRESS = 0X70
print("Opening I2C bus 3...")
i2cbus = smbus.SMBus(DEVICE_BUS)
#i2cbus.write_byte_data(DEVICE_ADDRESS, 0x1B, 0x16)

# Force correct bus
#i2c = ExtendedI2C(3)
print(i2cbus)

print(i2cbus.read_byte_data(0x70, 0x03 ))
#print
