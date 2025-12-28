"""Simple test to check if keyboard library works."""
import keyboard
import sys

print("=" * 50)
print("Keyboard Hook Test")
print("=" * 50)
print()
print("Press any key to test detection...")
print("Press ESC to exit")
print()

def on_key(event):
    if event.event_type == 'down':
        print(f"Key pressed: {event.name} (scan_code={event.scan_code})")
        sys.stdout.flush()

    if event.name == 'esc':
        print("\nESC pressed, exiting...")
        keyboard.unhook_all()
        sys.exit(0)

keyboard.hook(on_key)
keyboard.wait()  # Wait forever until ESC
