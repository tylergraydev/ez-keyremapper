# EZ Key Remapper

A simple Windows tool to remap keys from a specific keyboard device (like a macro pad) to different keys, without affecting your main keyboard.

## Features

- **Device-specific remapping** - Only remaps keys from your selected keyboard/macro pad
- **Auto-detect device** - Press any key on your macro pad to identify it
- **Simple GUI** - Easy to add/remove key mappings
- **Persistent config** - Saves your settings automatically
- **System tray** - Runs quietly in the background

## Installation

1. Download the latest `EZ-Key-Remapper-*.exe` from [Releases](../../releases)
2. Run the executable
3. On first run, click "Install Driver" when prompted (requires admin privileges)
4. Reboot your computer
5. Run the app again - you're ready to go!

## Usage

1. Click **Detect** and press any key on your macro pad to select it
2. Click **Add Mapping** to create a new key remapping:
   - First, press the key on your macro pad (e.g., `A`)
   - Then, press the desired output key (e.g., `F1`)
3. Enable remapping with the checkbox
4. Close the window to minimize to system tray

## Example Use Case

You have a cheap 3-key macro pad that types `A`, `B`, `C` but you want it to send `F1`, `F2`, `F3`:

1. Detect your macro pad
2. Add mapping: `A` → `F1`
3. Add mapping: `B` → `F2`
4. Add mapping: `C` → `F3`

Now your macro pad sends function keys while your main keyboard still types normally!

## How It Works

Uses the [Interception driver](https://github.com/oblitum/Interception) to intercept keyboard input at the driver level, allowing device-specific filtering and key remapping.

## Requirements

- Windows 10/11 (64-bit)
- Administrator privileges (for driver installation only)
- One-time reboot after driver installation

## Building from Source

```bash
# Install dependencies
pip install PyQt5 pyinstaller

# Build
python build.py
```

The executable will be in `dist/EZ Key Remapper.exe`

## License

MIT
