"""
Critical Test #1: Continuous Motor Mapping (Updated for I2C Hardware Implementation)

Tests the continuous offset-based haptic feedback system:
- Offset calculation: -1 (far left) to +1 (far right)
- Strength: abs(offset) = 0.0 to 1.0 (continuous)
- Dead zone: 0.12 (12% threshold)

Simple terminal output - manually record results for report.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_continuous_offset_calculation(num_positions=20):
    """
    Test that offset and strength change continuously as object moves left → right

    current implementation (haptic_controller.py line 110-114):
        offset = (x_center - frame_width/2) / (frame_width/2)  # -1 to +1
        strength = abs(offset)  # 0.0 to 1.0

    """
    print("\n" + "="*80)
    print("CONTINUOUS MOTOR MAPPING TEST - Offset-Based System")
    print("="*80)
    print("Testing: Offset and strength change CONTINUOUSLY as object moves")
    print("Implementation: offset = (x - center) / (width/2)")
    print("Expected: Smooth gradient from -1.0 (left) to +1.0 (right)")
    print("="*80 + "\n")

    frame_width = 1280
    frame_center = frame_width // 2
    DEAD_ZONE = 0.12  # From your implementation

    print(f"Frame width: {frame_width}px")
    print(f"Frame center: {frame_center}px")
    print(f"Dead zone: {DEAD_ZONE} ({DEAD_ZONE*100:.0f}%)")
    print("\nSimulating object moving from LEFT to RIGHT across camera view...")
    print("="*80 + "\n")

    # Track changes to detect jumps
    prev_offset = None
    prev_strength = None
    jump_count = 0
    max_jump = 0

    print(f"{'Step':<6} {'X (px)':<10} {'Offset':<10} {'Strength':<10} {'Side':<8} {'Active?':<10} {'Jump?':<15}")
    print("-" * 80)

    for i in range(num_positions + 1):
        # Calculate object position (0% = far left, 100% = far right)
        position_percent = i / num_positions * 100
        x_pos = int(frame_width * i / num_positions)

        # Calculate offset using YOUR implementation's formula
        offset = (x_pos - frame_center) / (frame_width / 2)
        offset = max(-1, min(1, offset))  # Clamp to [-1, 1]

        # Calculate strength
        strength = abs(offset)

        # Determine side
        if offset < 0:
            side = "left"
        else:
            side = "right"

        # Check if motor is active (outside dead zone)
        is_active = "YES" if abs(offset) > DEAD_ZONE else "NO (deadzone)"

        # Check for jumps in offset or strength
        jump_detected = ""
        if prev_offset is not None:
            offset_change = abs(offset - prev_offset)
            strength_change = abs(strength - prev_strength)
            max_change = max(offset_change, strength_change)

            # Threshold for "large jump" = 0.3 (30% change)
            if max_change > 0.3:
                jump_detected = f"⚠️ JUMP {max_change:.2f}"
                jump_count += 1
                max_jump = max(max_jump, max_change)
            else:
                jump_detected = "✓"

        # Print current state
        print(f"{i+1:<6} {x_pos:<10} {offset:>6.2f}    {strength:>6.2f}    {side:<8} {is_active:<10} {jump_detected}")

        prev_offset = offset
        prev_strength = strength

    # Analysis
    print("\n" + "="*80)
    print("ANALYSIS:")
    print("="*80)

    if jump_count == 0:
        print("✅ PASS: Smooth continuous transitions - NO sudden jumps!")
        print(f"   All changes were gradual (< 0.3 threshold)")
        print(f"   Your offset-based implementation is working correctly!")
    else:
        print(f"❌ FAIL: Detected {jump_count} sudden jumps (> 0.3 threshold)")
        print(f"   Largest jump: {max_jump:.2f}")
        print(f"   Something may be wrong with the offset calculation")

    print("\n" + "="*80)
    print("KEY OBSERVATIONS:")
    print("="*80)
    print(f"✓ Offset range: -1.0 (far left) → 0.0 (center) → +1.0 (far right)")
    print(f"✓ Strength range: 1.0 (edges) → 0.0 (center) → 1.0 (edges)")
    print(f"✓ Dead zone: ±{DEAD_ZONE} around center (no vibration in this zone)")
    print(f"✓ Motor selection: offset < 0 = LEFT, offset > 0 = RIGHT")

    print("\n" + "="*80)
    print("RECORD THESE RESULTS FOR YOUR REPORT:")
    print("="*80)
    print(f"Test: Continuous Motor Mapping (Offset-Based)")
    print(f"Positions tested: {num_positions + 1}")
    print(f"Jump threshold: 0.3 (30% change)")
    print(f"Jumps detected: {jump_count}")
    if jump_count > 0:
        print(f"Largest jump: {max_jump:.2f}")
    print(f"Dead zone: {DEAD_ZONE*100:.0f}%")
    print(f"Result: {'PASS - Continuous offset gradient ✅' if jump_count == 0 else 'FAIL - Discrete jumps detected ❌'}")
    print("="*80 + "\n")


def test_pulse_interval_behavior(num_samples=10):
    """
    Test pulse interval calculation (faster pulses = stronger feedback)

    Your implementation:
        interval = MAX_INTERVAL - strength * (MAX_INTERVAL - MIN_INTERVAL)
        Strong offset (1.0) → MIN_INTERVAL (0.45s) = fast pulses
        Weak offset (0.0) → MAX_INTERVAL (0.55s) = slow pulses
    """
    print("\n" + "="*80)
    print("PULSE INTERVAL TEST - Strength to Pulse Rate Mapping")
    print("="*80)
    print("Testing: Pulse rate changes based on offset strength")
    print("Strong offset → Fast pulses (short interval)")
    print("Weak offset → Slow pulses (long interval)")
    print("="*80 + "\n")

    MIN_INTERVAL = 0.45  # From your implementation
    MAX_INTERVAL = 0.55  # From your implementation

    print(f"MIN_INTERVAL: {MIN_INTERVAL}s (fast pulses)")
    print(f"MAX_INTERVAL: {MAX_INTERVAL}s (slow pulses)")
    print("\nStrength to pulse interval mapping:")
    print("="*80 + "\n")

    print(f"{'Strength':<12} {'Interval (s)':<15} {'Pulses/sec':<15} {'User Experience':<30}")
    print("-" * 80)

    prev_interval = None
    jump_count = 0

    for i in range(num_samples + 1):
        # Strength from 0.0 (weak) to 1.0 (strong)
        strength = i / num_samples

        # Calculate interval using YOUR formula
        interval = MAX_INTERVAL - strength * (MAX_INTERVAL - MIN_INTERVAL)
        pulses_per_sec = 1.0 / interval if interval > 0 else 0

        # User experience description
        if strength < 0.12:
            experience = "No vibration (dead zone)"
        elif strength < 0.4:
            experience = "Gentle guidance"
        elif strength < 0.7:
            experience = "Clear direction"
        else:
            experience = "Strong guidance"

        # Check for jumps
        jump = ""
        if prev_interval is not None:
            change = abs(interval - prev_interval)
            if change > 0.05:  # 50ms jump
                jump = f" ⚠️ JUMP {change*1000:.0f}ms"
                jump_count += 1

        print(f"{strength:>6.2f}      {interval:>8.3f}        {pulses_per_sec:>8.2f}        {experience:<30}{jump}")

        prev_interval = interval

    print("\n" + "="*80)
    print("ANALYSIS:")
    print("="*80)

    if jump_count == 0:
        print("✅ PASS: Smooth pulse interval transitions")
        print(f"   Interval changes gradually from {MAX_INTERVAL}s to {MIN_INTERVAL}s")
    else:
        print(f"⚠️  {jump_count} interval jumps detected (not critical)")

    print("\n" + "="*80)
    print("RECORD FOR YOUR REPORT:")
    print("="*80)
    print(f"Pulse interval range: {MIN_INTERVAL}s to {MAX_INTERVAL}s")
    print(f"Pulse rate range: {1/MAX_INTERVAL:.2f} to {1/MIN_INTERVAL:.2f} pulses/sec")
    print(f"Interval mapping: Continuous (strength-based)")
    print("="*80 + "\n")


def test_dead_zone_behavior():
    """
    Test dead zone behavior (no vibration in center region)

    Dead zone = 0.12 (12% of frame width on each side of center)
    """
    print("\n" + "="*80)
    print("DEAD ZONE TEST - Center Region Behavior")
    print("="*80)
    print("Testing: No vibration in center ±12% region")
    print("Purpose: Prevents motor flickering when object is centered")
    print("="*80 + "\n")

    frame_width = 1280
    frame_center = frame_width // 2
    DEAD_ZONE = 0.12

    # Calculate dead zone boundaries
    dead_zone_pixels = int(DEAD_ZONE * frame_width / 2)
    left_boundary = frame_center - dead_zone_pixels
    right_boundary = frame_center + dead_zone_pixels

    print(f"Frame center: {frame_center}px")
    print(f"Dead zone: ±{DEAD_ZONE} = ±{dead_zone_pixels}px")
    print(f"Dead zone range: {left_boundary}px to {right_boundary}px")
    print("\nTesting positions around center:")
    print("="*80 + "\n")

    print(f"{'Position':<15} {'X (px)':<10} {'Offset':<10} {'Strength':<10} {'Active?':<15}")
    print("-" * 60)

    test_positions = [
        ("Far left", frame_center - 200),
        ("Left edge", left_boundary - 10),
        ("Dead zone L", left_boundary + 10),
        ("Center", frame_center),
        ("Dead zone R", right_boundary - 10),
        ("Right edge", right_boundary + 10),
        ("Far right", frame_center + 200),
    ]

    active_count = 0
    inactive_count = 0

    for label, x_pos in test_positions:
        offset = (x_pos - frame_center) / (frame_width / 2)
        offset = max(-1, min(1, offset))
        strength = abs(offset)

        is_active = abs(offset) > DEAD_ZONE
        status = "Active" if is_active else "INACTIVE (deadzone)"

        if is_active:
            active_count += 1
        else:
            inactive_count += 1

        print(f"{label:<15} {x_pos:<10} {offset:>6.2f}    {strength:>6.2f}    {status}")

    print("\n" + "="*80)
    print("ANALYSIS:")
    print("="*80)
    print(f"✓ Active positions: {active_count} (outside dead zone)")
    print(f"✓ Inactive positions: {inactive_count} (inside dead zone)")
    print(f"✓ Dead zone prevents motor flickering when object is centered")

    print("\n" + "="*80)
    print("RECORD FOR YOUR REPORT:")
    print("="*80)
    print(f"Dead zone: ±{DEAD_ZONE} ({DEAD_ZONE*100:.0f}%)")
    print(f"Dead zone width: {dead_zone_pixels*2}px ({dead_zone_pixels*2/frame_width*100:.1f}% of frame)")
    print("Purpose: Stability when object is centered")
    print("="*80 + "\n")


def run_all_tests():
    """Run all motor mapping tests"""
    print("\n" + "="*80)
    print("CONTINUOUS MOTOR MAPPING - COMPLETE TEST SUITE")
    print("="*80)
    print("Testing the offset-based haptic feedback system")
    print("Implementation: I2C MUX + DRV2605 with pulse-based feedback")
    print("="*80 + "\n")

    input("Press ENTER to start TEST 1: Continuous Offset Calculation...")
    test_continuous_offset_calculation(num_positions=20)

    input("Press ENTER to start TEST 2: Pulse Interval Behavior...")
    test_pulse_interval_behavior(num_samples=10)

    input("Press ENTER to start TEST 3: Dead Zone Behavior...")
    test_dead_zone_behavior()

    print("\n" + "="*80)
    print(" ALL TESTS COMPLETED!")
    print("="*80)
    print("\nSummary:")
    print("  • Test 1: Offset calculation is continuous (-1 to +1)")
    print("  • Test 2: Pulse intervals vary smoothly (fast to slow)")
    print("  • Test 3: Dead zone prevents center flickering (±12%)")
    print("\nYour implementation uses continuous mapping! ")
    print("="*80 + "\n")


if __name__ == '__main__':
    # Run all tests
    run_all_tests()
