"""
Device manager for enumerating keyboard devices using Windows Raw Input API.
"""
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from typing import List, Optional

# Windows API constants
RIM_TYPEKEYBOARD = 1
RIDI_DEVICENAME = 0x20000007
RIDI_DEVICEINFO = 0x2000000b

# Structures
class RAWINPUTDEVICELIST(ctypes.Structure):
    _fields_ = [
        ("hDevice", wintypes.HANDLE),
        ("dwType", wintypes.DWORD),
    ]

class RID_DEVICE_INFO_KEYBOARD(ctypes.Structure):
    _fields_ = [
        ("dwType", wintypes.DWORD),
        ("dwSubType", wintypes.DWORD),
        ("dwKeyboardMode", wintypes.DWORD),
        ("dwNumberOfFunctionKeys", wintypes.DWORD),
        ("dwNumberOfIndicators", wintypes.DWORD),
        ("dwNumberOfKeysTotal", wintypes.DWORD),
    ]

class RID_DEVICE_INFO(ctypes.Structure):
    class _INFO(ctypes.Union):
        _fields_ = [
            ("keyboard", RID_DEVICE_INFO_KEYBOARD),
        ]
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("dwType", wintypes.DWORD),
        ("_info", _INFO),
    ]

@dataclass
class KeyboardDevice:
    """Represents a keyboard device."""
    handle: int
    name: str
    device_path: str
    num_keys: int = 0

    def __str__(self) -> str:
        return self.name

    def get_display_name(self) -> str:
        """Get a user-friendly display name."""
        return self.name

    def get_identifier(self) -> str:
        """Get a unique identifier for this device (path or handle-based)."""
        if self.device_path:
            return self.device_path
        return f"handle:{self.handle}"


def _extract_device_name(device_path: str, handle: int, num_keys: int, index: int) -> str:
    """Extract a friendly name from the device path or generate one."""
    if device_path:
        path_upper = device_path.upper()

        vid = ""
        pid = ""

        if "VID_" in path_upper:
            try:
                vid_start = path_upper.index("VID_") + 4
                vid = path_upper[vid_start:vid_start + 4]
            except (ValueError, IndexError):
                pass

        if "PID_" in path_upper:
            try:
                pid_start = path_upper.index("PID_") + 4
                pid = path_upper[pid_start:pid_start + 4]
            except (ValueError, IndexError):
                pass

        if vid and pid:
            return f"Keyboard (VID:{vid} PID:{pid})"

        # Fallback: use last part of path
        parts = device_path.replace("\\", "/").split("/")
        for part in reversed(parts):
            if part and len(part) > 4:
                clean = part.split("&")[0] if "&" in part else part
                clean = clean.split("#")[0] if "#" in clean else clean
                if clean:
                    return f"Keyboard ({clean[:20]})"

    # Generate name from handle and key count
    return f"Keyboard #{index + 1} ({num_keys} keys)"


def get_keyboard_devices() -> List[KeyboardDevice]:
    """
    Enumerate all keyboard devices connected to the system.
    Returns a list of KeyboardDevice objects.
    """
    user32 = ctypes.windll.user32

    # Get number of devices
    num_devices = ctypes.c_uint()
    result = user32.GetRawInputDeviceList(
        None,
        ctypes.byref(num_devices),
        ctypes.sizeof(RAWINPUTDEVICELIST)
    )

    if result == -1 or num_devices.value == 0:
        return []

    # Get device list
    devices_array = (RAWINPUTDEVICELIST * num_devices.value)()
    result = user32.GetRawInputDeviceList(
        devices_array,
        ctypes.byref(num_devices),
        ctypes.sizeof(RAWINPUTDEVICELIST)
    )

    if result == -1:
        return []

    keyboards = []
    keyboard_index = 0

    for device in devices_array:
        # Only interested in keyboards
        if device.dwType != RIM_TYPEKEYBOARD:
            continue

        device_path = ""
        num_keys = 0

        # Try to get device name (path)
        name_size = ctypes.c_uint(0)
        user32.GetRawInputDeviceInfoW(
            device.hDevice,
            RIDI_DEVICENAME,
            None,
            ctypes.byref(name_size)
        )

        if name_size.value > 1:  # More than just null terminator
            name_buffer = ctypes.create_unicode_buffer(name_size.value)
            result = user32.GetRawInputDeviceInfoW(
                device.hDevice,
                RIDI_DEVICENAME,
                name_buffer,
                ctypes.byref(name_size)
            )
            if result > 0:
                device_path = name_buffer.value

        # Get device info for key count
        info = RID_DEVICE_INFO()
        info.cbSize = ctypes.sizeof(RID_DEVICE_INFO)
        info_size = ctypes.c_uint(ctypes.sizeof(RID_DEVICE_INFO))

        result = user32.GetRawInputDeviceInfoW(
            device.hDevice,
            RIDI_DEVICEINFO,
            ctypes.byref(info),
            ctypes.byref(info_size)
        )

        if result > 0:
            num_keys = info._info.keyboard.dwNumberOfKeysTotal

        # Create keyboard device object
        friendly_name = _extract_device_name(device_path, device.hDevice, num_keys, keyboard_index)

        kbd = KeyboardDevice(
            handle=device.hDevice,
            name=friendly_name,
            device_path=device_path,
            num_keys=num_keys
        )
        keyboards.append(kbd)
        keyboard_index += 1

    return keyboards


def find_device_by_identifier(identifier: str) -> Optional[KeyboardDevice]:
    """Find a keyboard device by its identifier (path or handle-based)."""
    for device in get_keyboard_devices():
        if device.get_identifier() == identifier:
            return device
    return None


def find_device_by_handle(handle: int) -> Optional[KeyboardDevice]:
    """Find a keyboard device by its handle."""
    for device in get_keyboard_devices():
        if device.handle == handle:
            return device
    return None


if __name__ == "__main__":
    # Test enumeration
    print("Detected keyboard devices:")
    print("-" * 50)
    devices = get_keyboard_devices()
    print(f"Found {len(devices)} keyboard(s)")
    for kbd in devices:
        print(f"Name: {kbd.name}")
        print(f"  Handle: {kbd.handle:#x}")
        print(f"  Path: {kbd.device_path[:60] if kbd.device_path else '(none)'}...")
        print(f"  Keys: {kbd.num_keys}")
        print(f"  ID: {kbd.get_identifier()}")
        print()
