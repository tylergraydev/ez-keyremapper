"""
Key sender module - sends remapped keys using Windows SendInput API.
"""
import ctypes
from ctypes import wintypes
from typing import Dict, List

# Input type constants
INPUT_KEYBOARD = 1

# Key event flags
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

# Virtual key codes
VK_CODES: Dict[str, int] = {
    # Letters
    'A': 0x41, 'B': 0x42, 'C': 0x43, 'D': 0x44, 'E': 0x45,
    'F': 0x46, 'G': 0x47, 'H': 0x48, 'I': 0x49, 'J': 0x4A,
    'K': 0x4B, 'L': 0x4C, 'M': 0x4D, 'N': 0x4E, 'O': 0x4F,
    'P': 0x50, 'Q': 0x51, 'R': 0x52, 'S': 0x53, 'T': 0x54,
    'U': 0x55, 'V': 0x56, 'W': 0x57, 'X': 0x58, 'Y': 0x59,
    'Z': 0x5A,
    # Numbers
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
    '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
    # Function keys
    'F1': 0x70, 'F2': 0x71, 'F3': 0x72, 'F4': 0x73,
    'F5': 0x74, 'F6': 0x75, 'F7': 0x76, 'F8': 0x77,
    'F9': 0x78, 'F10': 0x79, 'F11': 0x7A, 'F12': 0x7B,
    'F13': 0x7C, 'F14': 0x7D, 'F15': 0x7E, 'F16': 0x7F,
    'F17': 0x80, 'F18': 0x81, 'F19': 0x82, 'F20': 0x83,
    'F21': 0x84, 'F22': 0x85, 'F23': 0x86, 'F24': 0x87,
    # Special keys
    'BACKSPACE': 0x08, 'TAB': 0x09, 'ENTER': 0x0D, 'SHIFT': 0x10,
    'CTRL': 0x11, 'ALT': 0x12, 'PAUSE': 0x13, 'CAPSLOCK': 0x14,
    'ESCAPE': 0x1B, 'SPACE': 0x20, 'PAGEUP': 0x21, 'PAGEDOWN': 0x22,
    'END': 0x23, 'HOME': 0x24, 'LEFT': 0x25, 'UP': 0x26,
    'RIGHT': 0x27, 'DOWN': 0x28, 'PRINTSCREEN': 0x2C, 'INSERT': 0x2D,
    'DELETE': 0x2E, 'LWIN': 0x5B, 'RWIN': 0x5C, 'APPS': 0x5D,
    'NUMLOCK': 0x90, 'SCROLLLOCK': 0x91,
    # Numpad
    'NUMPAD0': 0x60, 'NUMPAD1': 0x61, 'NUMPAD2': 0x62, 'NUMPAD3': 0x63,
    'NUMPAD4': 0x64, 'NUMPAD5': 0x65, 'NUMPAD6': 0x66, 'NUMPAD7': 0x67,
    'NUMPAD8': 0x68, 'NUMPAD9': 0x69, 'MULTIPLY': 0x6A, 'ADD': 0x6B,
    'SEPARATOR': 0x6C, 'SUBTRACT': 0x6D, 'DECIMAL': 0x6E, 'DIVIDE': 0x6F,
    # OEM keys
    'SEMICOLON': 0xBA, 'EQUALS': 0xBB, 'COMMA': 0xBC, 'MINUS': 0xBD,
    'PERIOD': 0xBE, 'SLASH': 0xBF, 'BACKTICK': 0xC0, 'LBRACKET': 0xDB,
    'BACKSLASH': 0xDC, 'RBRACKET': 0xDD, 'QUOTE': 0xDE,
    # Media keys
    'VOLUME_MUTE': 0xAD, 'VOLUME_DOWN': 0xAE, 'VOLUME_UP': 0xAF,
    'MEDIA_NEXT': 0xB0, 'MEDIA_PREV': 0xB1, 'MEDIA_STOP': 0xB2,
    'MEDIA_PLAY_PAUSE': 0xB3,
}

# Reverse mapping: VK code to name
VK_NAMES: Dict[int, str] = {v: k for k, v in VK_CODES.items()}

# Extended keys (need KEYEVENTF_EXTENDEDKEY flag)
EXTENDED_KEYS = {
    0x21, 0x22, 0x23, 0x24,  # PageUp, PageDown, End, Home
    0x25, 0x26, 0x27, 0x28,  # Arrow keys
    0x2D, 0x2E,              # Insert, Delete
    0x5B, 0x5C,              # Win keys
    0x6F,                    # Numpad divide
}


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]

    _anonymous_ = ("_input",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("_input", _INPUT),
    ]


def vk_to_name(vk_code: int) -> str:
    """Convert a virtual key code to a human-readable name."""
    if vk_code in VK_NAMES:
        return VK_NAMES[vk_code]
    # Handle unmapped codes
    if 0x41 <= vk_code <= 0x5A:
        return chr(vk_code)
    if 0x30 <= vk_code <= 0x39:
        return chr(vk_code)
    return f"VK_{vk_code:02X}"


def name_to_vk(name: str) -> int:
    """Convert a key name to virtual key code."""
    name_upper = name.upper()
    if name_upper in VK_CODES:
        return VK_CODES[name_upper]
    # Single character
    if len(name) == 1:
        return ord(name.upper())
    return 0


def send_key(vk_code: int, key_up: bool = False) -> bool:
    """
    Send a single key event.

    Args:
        vk_code: Virtual key code to send
        key_up: True for key up event, False for key down

    Returns:
        True if successful
    """
    user32 = ctypes.windll.user32

    flags = 0
    if key_up:
        flags |= KEYEVENTF_KEYUP
    if vk_code in EXTENDED_KEYS:
        flags |= KEYEVENTF_EXTENDEDKEY

    extra = ctypes.c_ulong(0)
    inp = INPUT(
        type=INPUT_KEYBOARD,
        ki=KEYBDINPUT(
            wVk=vk_code,
            wScan=0,
            dwFlags=flags,
            time=0,
            dwExtraInfo=ctypes.pointer(extra),
        ),
    )

    result = user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
    return result == 1


def send_key_press(vk_code: int) -> bool:
    """Send a complete key press (down + up)."""
    down_ok = send_key(vk_code, key_up=False)
    up_ok = send_key(vk_code, key_up=True)
    return down_ok and up_ok


# Modifier key VK codes
MODIFIER_KEYS = {
    0x10,  # VK_SHIFT
    0x11,  # VK_CONTROL
    0x12,  # VK_MENU (Alt)
    0xA0,  # VK_LSHIFT
    0xA1,  # VK_RSHIFT
    0xA2,  # VK_LCONTROL
    0xA3,  # VK_RCONTROL
    0xA4,  # VK_LMENU
    0xA5,  # VK_RMENU
    0x5B,  # VK_LWIN
    0x5C,  # VK_RWIN
}


def send_key_combo(vk_codes: List[int]) -> bool:
    """
    Send a key combination (e.g., Ctrl+Shift+V).

    Modifiers are held down while non-modifiers are pressed.
    Order: press modifiers down, press non-modifiers, release all.

    Args:
        vk_codes: List of virtual key codes in the combo

    Returns:
        True if all operations succeeded
    """
    if not vk_codes:
        return False

    # Separate modifiers from regular keys
    modifiers = [vk for vk in vk_codes if vk in MODIFIER_KEYS]
    regular_keys = [vk for vk in vk_codes if vk not in MODIFIER_KEYS]

    success = True

    # Press all modifiers down
    for vk in modifiers:
        if not send_key(vk, key_up=False):
            success = False

    # Press and release regular keys
    for vk in regular_keys:
        if not send_key(vk, key_up=False):
            success = False
        if not send_key(vk, key_up=True):
            success = False

    # Release modifiers in reverse order
    for vk in reversed(modifiers):
        if not send_key(vk, key_up=True):
            success = False

    return success


if __name__ == "__main__":
    import time
    print("Testing key sender...")
    print("Will send F1 key in 3 seconds...")
    time.sleep(3)
    send_key_press(VK_CODES['F1'])
    print("Sent F1!")
