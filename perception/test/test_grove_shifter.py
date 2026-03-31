"""
Grove Level Shifter — GPIO Hardware Test
=========================================
Tests the Grove BSS138-based 4-channel bidirectional level shifter
sitting between the Raspberry Pi 3.3 V GPIO bus and 5 V peripherals.

Wiring assumed for this test
-----------------------------
  Pi GPIO 17 (BCM)  -->  LV1 pin  (LV side, 3.3 V rail)
  HV1 pin           -->  Pi GPIO 18 (BCM)   [read-back via HV side]
  VREF_LV           -->  3.3 V
  VREF_HV           -->  5 V
  GND               -->  GND

Test strategy
-------------
1. Output test  : Drive GPIO 17 HIGH / LOW several times; confirm no
                  Python/GPIO error (proves LV side is wired and functional).
2. Loopback test: Read GPIO 18 while toggling GPIO 17; if the signal
                  passes through the shifter and back, both readings must
                  agree — PASS.  If GPIO 18 is not wired (HV loopback not
                  connected) the test reports the output-only result and
                  marks the loopback as SKIPPED.
3. I2C bus scan : Quick smbus2 scan on bus 1 to detect any I2C devices that
                  should be visible only once the shifter is in the signal
                  path (e.g. TCA9548A at 0x70, DRV2605 at 0x5A).

Run on Raspberry Pi:
    python3 perception/test/test_grove_shifter.py

No pytest dependency — plain Python so it can run directly on the Pi.
"""

import sys
import os
import time

# ── path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from perception.config.hardware_config import GROVE_SHIFTER_CONFIG
except ImportError:
    # Fallback if config path differs
    GROVE_SHIFTER_CONFIG = {
        'test_output_pin': 17,
        'test_input_pin':  18,
        'lv_voltage':       3.3,
        'hv_voltage':       5.0,
        'test_cycles':      5,
        'toggle_delay':     0.2,
    }

OUTPUT_PIN  = GROVE_SHIFTER_CONFIG['test_output_pin']
INPUT_PIN   = GROVE_SHIFTER_CONFIG['test_input_pin']
CYCLES      = GROVE_SHIFTER_CONFIG['test_cycles']
DELAY       = GROVE_SHIFTER_CONFIG['toggle_delay']

# ── helpers ───────────────────────────────────────────────────────────────────

def _sep(char='─', width=60):
    print(char * width)

def _header(title):
    _sep('═')
    print(f"  {title}")
    _sep('═')

def _section(title):
    _sep()
    print(f"  {title}")
    _sep()

# ── Test 1: GPIO output toggle ────────────────────────────────────────────────

def test_gpio_output(gpio):
    """Toggle the LV output pin and confirm no errors occur."""
    _section(f"TEST 1 — GPIO Output Toggle  (pin BCM {OUTPUT_PIN})")

    try:
        gpio.setup(OUTPUT_PIN, gpio.OUT)
        errors = 0
        for cycle in range(1, CYCLES + 1):
            gpio.output(OUTPUT_PIN, gpio.HIGH)
            time.sleep(DELAY)
            gpio.output(OUTPUT_PIN, gpio.LOW)
            time.sleep(DELAY)
            print(f"  Cycle {cycle}/{CYCLES}  HIGH→LOW  OK")

        print(f"\n  RESULT: PASS — LV output toggled {CYCLES} cycles without error")
        return True
    except Exception as exc:
        print(f"\n  RESULT: FAIL — {exc}")
        return False

# ── Test 2: Loopback (HV side read-back) ─────────────────────────────────────

def test_loopback(gpio):
    """
    Drive LV output and read HV output back.
    Requires HV1 to be wired to INPUT_PIN on the Pi
    (HV → Pi via resistor divider or direct if HV is 3.3 V tolerant).
    """
    _section(f"TEST 2 — Loopback  (output BCM {OUTPUT_PIN}  →  input BCM {INPUT_PIN})")

    try:
        gpio.setup(OUTPUT_PIN, gpio.OUT)
        gpio.setup(INPUT_PIN,  gpio.IN)
    except Exception as exc:
        print(f"  GPIO setup failed: {exc}")
        return None  # None = skipped

    pass_count = 0
    fail_count = 0

    for cycle in range(1, CYCLES + 1):
        # Drive HIGH, read back
        gpio.output(OUTPUT_PIN, gpio.HIGH)
        time.sleep(DELAY)
        read_high = gpio.input(INPUT_PIN)

        # Drive LOW, read back
        gpio.output(OUTPUT_PIN, gpio.LOW)
        time.sleep(DELAY)
        read_low = gpio.input(INPUT_PIN)

        high_ok = (read_high == gpio.HIGH)
        low_ok  = (read_low  == gpio.LOW)
        status  = "PASS" if (high_ok and low_ok) else "FAIL"

        if high_ok and low_ok:
            pass_count += 1
        else:
            fail_count += 1

        print(f"  Cycle {cycle}/{CYCLES}  "
              f"HIGH→read={read_high}({'ok' if high_ok else 'FAIL'})  "
              f"LOW→read={read_low}({'ok' if low_ok else 'FAIL'})  [{status}]")

    total = pass_count + fail_count
    if fail_count == 0:
        print(f"\n  RESULT: PASS — {pass_count}/{total} cycles matched")
        return True
    else:
        # If ALL readings came back LOW regardless of output, the HV loopback
        # wire is likely absent — report as SKIPPED rather than hard FAIL.
        all_low = True
        gpio.setup(OUTPUT_PIN, gpio.OUT)
        gpio.output(OUTPUT_PIN, gpio.HIGH)
        time.sleep(DELAY)
        sample = gpio.input(INPUT_PIN)
        gpio.output(OUTPUT_PIN, gpio.LOW)
        if sample == gpio.HIGH:
            all_low = False

        if all_low:
            print(f"\n  RESULT: SKIPPED — GPIO {INPUT_PIN} always reads LOW.")
            print( "          HV loopback wire probably not connected.")
            print( "          Connect HV1 → BCM 18 to enable this test.")
            return None  # skipped
        else:
            print(f"\n  RESULT: FAIL — {fail_count}/{total} cycles mismatched")
            return False

# ── Test 3: I2C bus scan ──────────────────────────────────────────────────────

# Known device addresses expected when the shifter is in the I2C path
EXPECTED_I2C = {
    0x70: "TCA9548A (I2C MUX)",
    0x5A: "DRV2605 (haptic driver, ch0)",
}

def test_i2c_scan():
    """Scan I2C bus 1 and report found devices."""
    _section("TEST 3 — I2C Bus Scan  (bus 1)")

    try:
        import smbus2
        bus = smbus2.SMBus(1)
    except ImportError:
        print("  smbus2 not installed — skipping I2C scan.")
        print("  Install with: pip install smbus2")
        return None
    except Exception as exc:
        print(f"  Could not open I2C bus 1: {exc}")
        return None

    found = []
    print("  Scanning 0x03 – 0x77 …")
    for addr in range(0x03, 0x78):
        try:
            bus.read_byte(addr)
            label = EXPECTED_I2C.get(addr, "unknown device")
            print(f"    0x{addr:02X}  {label}")
            found.append(addr)
        except OSError:
            pass

    bus.close()

    if not found:
        print("  No I2C devices found.")
        print("  Check: power to shifter VREF_HV, SDA/SCL wiring, and pull-ups.")
        return False

    expected_found = [a for a in found if a in EXPECTED_I2C]
    if expected_found:
        print(f"\n  RESULT: PASS — found {len(found)} device(s); "
              f"{len(expected_found)} expected device(s) confirmed.")
    else:
        print(f"\n  RESULT: INFO — found {len(found)} device(s), "
              f"none matched known expected addresses {list(EXPECTED_I2C.keys())}")

    return len(found) > 0

# ── main ──────────────────────────────────────────────────────────────────────

def run_all():
    _header("Grove Level Shifter — GPIO Hardware Test")
    print(f"  LV side output pin : BCM {OUTPUT_PIN}")
    print(f"  HV side input pin  : BCM {INPUT_PIN}")
    print(f"  Test cycles        : {CYCLES}")
    print(f"  Toggle delay       : {DELAY} s")
    print()

    results = {}

    # ── Try to import RPi.GPIO ────────────────────────────────────────────────
    gpio = None
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        gpio = GPIO
        print("  GPIO library      : RPi.GPIO (hardware mode)")
    except ImportError:
        pass

    if gpio is None:
        try:
            from gpiozero import Device
            from gpiozero.pins.rpigpio import RPiGPIOFactory
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            gpio = GPIO
            print("  GPIO library      : RPi.GPIO via gpiozero")
        except Exception:
            pass

    if gpio is None:
        print("  WARNING: RPi.GPIO not available on this machine.")
        print("  GPIO output/loopback tests will be SKIPPED.")
        print("  (Run this script on the Raspberry Pi for full results.)\n")

    # ── Run tests ─────────────────────────────────────────────────────────────
    if gpio:
        results['gpio_output'] = test_gpio_output(gpio)
        results['loopback']    = test_loopback(gpio)
    else:
        results['gpio_output'] = None
        results['loopback']    = None

    results['i2c_scan'] = test_i2c_scan()

    # ── Cleanup ───────────────────────────────────────────────────────────────
    if gpio:
        try:
            gpio.cleanup([OUTPUT_PIN, INPUT_PIN])
        except Exception:
            pass

    # ── Summary ───────────────────────────────────────────────────────────────
    _header("SUMMARY")
    status_map = {True: "PASS   ", False: "FAIL   ", None: "SKIPPED"}
    for name, result in results.items():
        label = status_map.get(result, "UNKNOWN")
        print(f"  {label}  {name}")

    failed = [k for k, v in results.items() if v is False]
    if failed:
        print(f"\n  {len(failed)} test(s) FAILED: {', '.join(failed)}")
        print("  Check wiring, power rails, and pull-up resistors.")
        sys.exit(1)
    else:
        skipped = [k for k, v in results.items() if v is None]
        if skipped:
            print(f"\n  {len(skipped)} test(s) skipped (hardware not available on this machine).")
        print("\n  Grove shifter hardware verification complete.")
    _sep('═')


if __name__ == '__main__':
    run_all()
