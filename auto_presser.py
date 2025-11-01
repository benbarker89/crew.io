#!/usr/bin/env python3
"""
Auto Button Presser
Presses the down arrow key 150 times per minute with a 10 second delay.
Press Escape to stop.
"""

import time
from pynput.keyboard import Key, Controller, Listener
import threading

# Configuration
PRESSES_PER_MINUTE = 150
DELAY_BEFORE_START = 10  # seconds
INTERVAL = 60 / PRESSES_PER_MINUTE  # seconds between presses

# Global control flag
running = False
should_stop = False

keyboard = Controller()


def on_press(key):
    """Handle key press events."""
    global should_stop
    if key == Key.esc:
        print("\n[ESC pressed] Stopping auto-presser...")
        should_stop = True
        return False  # Stop listener


def press_down_key():
    """Continuously press the down arrow key."""
    global running, should_stop

    print(f"Starting in {DELAY_BEFORE_START} seconds...")
    print("Press ESC to stop at any time.")

    # Initial delay
    for i in range(DELAY_BEFORE_START, 0, -1):
        if should_stop:
            return
        print(f"{i}...", flush=True)
        time.sleep(1)

    print("\n[Started] Pressing down arrow key...")
    print(f"Rate: {PRESSES_PER_MINUTE} presses/minute (every {INTERVAL:.3f} seconds)")

    running = True
    press_count = 0

    while running and not should_stop:
        keyboard.press(Key.down)
        keyboard.release(Key.down)
        press_count += 1

        if press_count % 10 == 0:  # Update every 10 presses
            print(f"Presses: {press_count}", end='\r', flush=True)

        time.sleep(INTERVAL)

    print(f"\n[Stopped] Total presses: {press_count}")


def main():
    """Main function."""
    print("=" * 50)
    print("Auto Button Presser")
    print("=" * 50)

    # Start the key pressing in a separate thread
    press_thread = threading.Thread(target=press_down_key, daemon=True)
    press_thread.start()

    # Start listening for ESC key
    with Listener(on_press=on_press) as listener:
        listener.join()

    # Wait for press thread to finish
    press_thread.join(timeout=1)

    print("\nProgram exited.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[Ctrl+C detected] Exiting...")
    except Exception as e:
        print(f"\nError: {e}")
