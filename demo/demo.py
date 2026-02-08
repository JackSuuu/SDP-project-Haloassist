#!/usr/bin/env python3
"""
Main demo script for Raspberry Pi
Full workflow: Button → Speech → Detection → Haptic Guidance
Includes web visualization server
"""
import sys
import os
import subprocess
import time
import threading
import signal

# Add perception/src to path
perception_src = os.path.join(os.path.dirname(__file__), '..', 'perception', 'src')
sys.path.insert(0, perception_src)

# Add visualization to path
visualization_dir = os.path.join(os.path.dirname(__file__), '..', 'visualization')
sys.path.insert(0, visualization_dir)

from main import PerceptionSystem

# Global variable for server process
viz_server_process = None


def start_visualization_server():
    """Start the FastAPI visualization server in a background thread"""
    global viz_server_process
    
    server_path = os.path.join(visualization_dir, 'server.py')
    static_dir = os.path.join(visualization_dir, 'static')
    
    # Ensure static directory exists
    os.makedirs(static_dir, exist_ok=True)
    
    try:
        # Start uvicorn server
        viz_server_process = subprocess.Popen(
            [sys.executable, server_path],
            cwd=visualization_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("🌐 Visualization server starting at http://localhost:8000")
        time.sleep(2)  # Give server time to start
        return True
    except Exception as e:
        print(f"⚠️  Could not start visualization server: {e}")
        return False


def stop_visualization_server():
    """Stop the visualization server"""
    global viz_server_process
    if viz_server_process:
        viz_server_process.terminate()
        viz_server_process.wait()
        print("🌐 Visualization server stopped")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n🛑 Shutting down...")
    stop_visualization_server()
    sys.exit(0)


def main():
    # Register signal handler for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 60)
    print("  Perception System - Full Demo")
    print("=" * 60)
    print()
    print("  Pipeline:")
    print("  1. 🔘 Press button (GPIO 5)")
    print("  2. 🎤 Say object name (e.g., 'bottle', 'cup', 'phone')")
    print("  3. 🎯 Camera detects ONLY that specific object")
    print("  4. 📳 Haptic feedback guides you to it")
    print()
    print("  Hardware:")
    print("  - Button: GPIO 5 → GND")
    print("  - Left Motor: GPIO 22")
    print("  - Right Motor: GPIO 26")
    print("  - Camera: CSI port")
    print()
    print("  Press Ctrl+C to quit")
    print("=" * 60)
    print()
    
    # ── Step 1: Start visualization server ──
    print("🚀 Starting services...")
    print()
    viz_started = start_visualization_server()
    if viz_started:
        print("   ✅ Web visualizer:  http://localhost:8000")
    else:
        print("   ⚠️  Web visualizer:  failed (continuing without it)")
    
    # ── Step 2: Choose display mode ──
    show_display = True  # Change to False for headless mode
    
    # ── Step 3: Initialize perception system ──
    print()
    print("🔧 Initializing perception system...")
    system = PerceptionSystem(
        model_name='yolo26n',  # yolov26n.pt - tested on Pi3
        show_display=show_display,
        enable_speech=True
    )
    
    print()
    print(f"   💡 Display: {'ON' if show_display else 'OFF'}")
    print(f"   💡 Speech:  ON (press button to start)")
    if viz_started:
        print(f"   💡 Web UI:  http://localhost:8000")
    print()
    
    # ── Step 4: Run the system ──
    try:
        system.run()
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
        print("\nTroubleshooting:")
        print("- Check if camera is enabled: vcgencmd get_camera")
        print("- Check if model file exists: ls perception/*.pt")
        print("- Check dependencies: pip list | grep ultralytics")
    finally:
        stop_visualization_server()


if __name__ == '__main__':
    main()
