"""
Key interceptor module - uses Interception driver for device-specific key interception.
"""
import ctypes
from ctypes import wintypes
import threading
import os
import sys
import zipfile
import tempfile
import urllib.request
import shutil
from typing import Callable, Dict, Optional, List, Union
from dataclasses import dataclass


# URL for Interception release
INTERCEPTION_RELEASE_URL = "https://github.com/oblitum/Interception/releases/download/v1.0.1/Interception.zip"


# Interception constants
INTERCEPTION_MAX_KEYBOARD = 10
INTERCEPTION_MAX_MOUSE = 10
INTERCEPTION_MAX_DEVICE = INTERCEPTION_MAX_KEYBOARD + INTERCEPTION_MAX_MOUSE

# Key state flags
INTERCEPTION_KEY_DOWN = 0x00
INTERCEPTION_KEY_UP = 0x01
INTERCEPTION_KEY_E0 = 0x02  # Extended key
INTERCEPTION_KEY_E1 = 0x04

# Filter flags
INTERCEPTION_FILTER_KEY_NONE = 0x0000
INTERCEPTION_FILTER_KEY_ALL = 0xFFFF
INTERCEPTION_FILTER_KEY_DOWN = 0x01
INTERCEPTION_FILTER_KEY_UP = 0x02


class InterceptionKeyStroke(ctypes.Structure):
    """Structure for keyboard strokes."""
    _fields_ = [
        ("code", ctypes.c_ushort),      # Scan code
        ("state", ctypes.c_ushort),     # Key state flags
        ("information", ctypes.c_uint), # Extra info
    ]


@dataclass
class KeyEvent:
    """Represents a key event with device info."""
    scan_code: int
    vk_code: int
    is_key_up: bool
    device: int  # Interception device number (1-10 for keyboards)
    hardware_id: str


# Scan code to VK code mapping (common keys)
SCAN_TO_VK = {
    0x1E: 0x41,  # A
    0x30: 0x42,  # B
    0x2E: 0x43,  # C
    0x20: 0x44,  # D
    0x12: 0x45,  # E
    0x21: 0x46,  # F
    0x22: 0x47,  # G
    0x23: 0x48,  # H
    0x17: 0x49,  # I
    0x24: 0x4A,  # J
    0x25: 0x4B,  # K
    0x26: 0x4C,  # L
    0x32: 0x4D,  # M
    0x31: 0x4E,  # N
    0x18: 0x4F,  # O
    0x19: 0x50,  # P
    0x10: 0x51,  # Q
    0x13: 0x52,  # R
    0x1F: 0x53,  # S
    0x14: 0x54,  # T
    0x16: 0x55,  # U
    0x2F: 0x56,  # V
    0x11: 0x57,  # W
    0x2D: 0x58,  # X
    0x15: 0x59,  # Y
    0x2C: 0x5A,  # Z
    0x02: 0x31,  # 1
    0x03: 0x32,  # 2
    0x04: 0x33,  # 3
    0x05: 0x34,  # 4
    0x06: 0x35,  # 5
    0x07: 0x36,  # 6
    0x08: 0x37,  # 7
    0x09: 0x38,  # 8
    0x0A: 0x39,  # 9
    0x0B: 0x30,  # 0
    0x3B: 0x70,  # F1
    0x3C: 0x71,  # F2
    0x3D: 0x72,  # F3
    0x3E: 0x73,  # F4
    0x3F: 0x74,  # F5
    0x40: 0x75,  # F6
    0x41: 0x76,  # F7
    0x42: 0x77,  # F8
    0x43: 0x78,  # F9
    0x44: 0x79,  # F10
    0x57: 0x7A,  # F11
    0x58: 0x7B,  # F12
    0x01: 0x1B,  # Escape
    0x0E: 0x08,  # Backspace
    0x0F: 0x09,  # Tab
    0x1C: 0x0D,  # Enter
    0x39: 0x20,  # Space
    0x2A: 0x10,  # Left Shift
    0x36: 0x10,  # Right Shift
    0x1D: 0x11,  # Left Ctrl
    0x38: 0x12,  # Left Alt
    0x3A: 0x14,  # Caps Lock
}

# VK to scan code (reverse mapping)
VK_TO_SCAN = {v: k for k, v in SCAN_TO_VK.items()}


def get_project_dll_path() -> str:
    """Get the path where the DLL should be stored in the project."""
    return os.path.join(os.path.dirname(__file__), "..", "interception.dll")


def download_interception_dll(target_path: str) -> bool:
    """
    Download the Interception DLL from GitHub releases.

    Returns:
        True if successful, False otherwise
    """
    print("[SETUP] Downloading Interception driver...", flush=True)

    try:
        # Create temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "Interception.zip")

            # Download the zip file
            print(f"[SETUP] Fetching from {INTERCEPTION_RELEASE_URL}...", flush=True)
            urllib.request.urlretrieve(INTERCEPTION_RELEASE_URL, zip_path)

            # Extract the zip
            print("[SETUP] Extracting...", flush=True)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Find the x64 DLL
            # Structure is: Interception/library/x64/interception.dll
            dll_source = os.path.join(temp_dir, "Interception", "library", "x64", "interception.dll")

            if not os.path.exists(dll_source):
                # Try alternate structure
                dll_source = os.path.join(temp_dir, "library", "x64", "interception.dll")

            if not os.path.exists(dll_source):
                print(f"[SETUP] Could not find DLL in archive", flush=True)
                return False

            # Copy to target location
            print(f"[SETUP] Installing DLL to {target_path}...", flush=True)
            shutil.copy2(dll_source, target_path)

            print("[SETUP] DLL installed successfully!", flush=True)
            return True

    except Exception as e:
        print(f"[SETUP] Error downloading DLL: {e}", flush=True)
        return False


def check_driver_installed() -> bool:
    """Check if the Interception driver is installed in Windows."""
    try:
        # Try to open the driver device
        import ctypes
        kernel32 = ctypes.windll.kernel32
        INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
        GENERIC_READ = 0x80000000
        FILE_SHARE_READ = 0x00000001
        OPEN_EXISTING = 3

        handle = kernel32.CreateFileW(
            r"\\.\interception00",
            GENERIC_READ,
            FILE_SHARE_READ,
            None,
            OPEN_EXISTING,
            0,
            None
        )

        if handle != INVALID_HANDLE_VALUE:
            kernel32.CloseHandle(handle)
            return True
        return False
    except:
        return False


class InterceptionDriver:
    """Wrapper for the Interception driver DLL."""

    def __init__(self):
        self._dll = None
        self._context = None
        self._load_driver()

    def _load_driver(self):
        """Load the interception DLL."""
        project_dll = get_project_dll_path()

        # Try common locations
        dll_paths = [
            project_dll,
            "interception.dll",
            os.path.join(os.path.dirname(__file__), "interception.dll"),
            r"C:\Program Files\interception\library\x64\interception.dll",
            r"C:\interception\library\x64\interception.dll",
        ]

        for path in dll_paths:
            try:
                self._dll = ctypes.CDLL(path)
                print(f"[INTERCEPTOR] Loaded DLL from: {path}", flush=True)
                break
            except OSError:
                continue

        # If DLL not found, try to download it
        if self._dll is None:
            print("[INTERCEPTOR] DLL not found, attempting to download...", flush=True)
            if download_interception_dll(project_dll):
                try:
                    self._dll = ctypes.CDLL(project_dll)
                    print(f"[INTERCEPTOR] Loaded downloaded DLL", flush=True)
                except OSError as e:
                    pass

        if self._dll is None:
            raise RuntimeError(
                "Could not load interception.dll.\n\n"
                "Automatic download failed. Please manually download from:\n"
                "https://github.com/oblitum/Interception/releases\n\n"
                "Extract and copy library/x64/interception.dll to the project folder."
            )

        # Set up function signatures
        self._setup_functions()

        # Create context
        self._context = self._dll.interception_create_context()
        if not self._context:
            # Context creation failed - likely driver not installed
            if not check_driver_installed():
                raise RuntimeError(
                    "Interception driver is not installed.\n\n"
                    "The DLL is present but the kernel driver needs to be installed.\n\n"
                    "To install the driver:\n"
                    "1. Download from: https://github.com/oblitum/Interception/releases\n"
                    "2. Extract the zip file\n"
                    "3. Open Command Prompt as Administrator\n"
                    "4. Navigate to: Interception\\command line installer\n"
                    "5. Run: install-interception.exe /install\n"
                    "6. Reboot your computer\n\n"
                    "After reboot, run this app again."
                )
            else:
                raise RuntimeError("Failed to create Interception context")

    def _setup_functions(self):
        """Set up ctypes function signatures."""
        # interception_create_context
        self._dll.interception_create_context.restype = ctypes.c_void_p
        self._dll.interception_create_context.argtypes = []

        # interception_destroy_context
        self._dll.interception_destroy_context.restype = None
        self._dll.interception_destroy_context.argtypes = [ctypes.c_void_p]

        # interception_set_filter
        self._dll.interception_set_filter.restype = None
        self._dll.interception_set_filter.argtypes = [
            ctypes.c_void_p,  # context
            ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int),  # predicate
            ctypes.c_ushort,  # filter
        ]

        # interception_wait
        self._dll.interception_wait.restype = ctypes.c_int
        self._dll.interception_wait.argtypes = [ctypes.c_void_p]

        # interception_wait_with_timeout
        self._dll.interception_wait_with_timeout.restype = ctypes.c_int
        self._dll.interception_wait_with_timeout.argtypes = [
            ctypes.c_void_p,  # context
            ctypes.c_ulong,   # timeout in ms
        ]

        # interception_receive
        self._dll.interception_receive.restype = ctypes.c_int
        self._dll.interception_receive.argtypes = [
            ctypes.c_void_p,  # context
            ctypes.c_int,     # device
            ctypes.POINTER(InterceptionKeyStroke),  # stroke
            ctypes.c_uint,    # nstroke
        ]

        # interception_send
        self._dll.interception_send.restype = ctypes.c_int
        self._dll.interception_send.argtypes = [
            ctypes.c_void_p,  # context
            ctypes.c_int,     # device
            ctypes.POINTER(InterceptionKeyStroke),  # stroke
            ctypes.c_uint,    # nstroke
        ]

        # interception_get_hardware_id
        self._dll.interception_get_hardware_id.restype = ctypes.c_int
        self._dll.interception_get_hardware_id.argtypes = [
            ctypes.c_void_p,  # context
            ctypes.c_int,     # device
            ctypes.c_wchar_p, # hardware_id buffer
            ctypes.c_uint,    # buffer size
        ]

        # interception_is_keyboard
        self._dll.interception_is_keyboard.restype = ctypes.c_int
        self._dll.interception_is_keyboard.argtypes = [ctypes.c_int]

    def set_keyboard_filter(self, filter_flags: int = INTERCEPTION_FILTER_KEY_ALL):
        """Set filter to intercept keyboard events."""
        # Create predicate that returns 1 for keyboards
        PREDICATE = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int)
        predicate = PREDICATE(lambda device: self._dll.interception_is_keyboard(device))
        self._dll.interception_set_filter(self._context, predicate, filter_flags)

    def wait(self, timeout_ms: int = -1) -> int:
        """Wait for device input. Returns device number or 0 on timeout."""
        if timeout_ms < 0:
            return self._dll.interception_wait(self._context)
        else:
            return self._dll.interception_wait_with_timeout(self._context, timeout_ms)

    def receive(self, device: int) -> Optional[InterceptionKeyStroke]:
        """Receive a keystroke from device."""
        stroke = InterceptionKeyStroke()
        count = self._dll.interception_receive(
            self._context, device, ctypes.byref(stroke), 1
        )
        return stroke if count > 0 else None

    def send(self, device: int, stroke: InterceptionKeyStroke):
        """Send a keystroke to device."""
        self._dll.interception_send(self._context, device, ctypes.byref(stroke), 1)

    def get_hardware_id(self, device: int) -> str:
        """Get hardware ID for a device."""
        buffer = ctypes.create_unicode_buffer(500)
        length = self._dll.interception_get_hardware_id(
            self._context, device, buffer, 500
        )
        return buffer.value if length > 0 else ""

    def is_keyboard(self, device: int) -> bool:
        """Check if device is a keyboard."""
        return bool(self._dll.interception_is_keyboard(device))

    def destroy(self):
        """Destroy the context."""
        if self._context and self._dll:
            self._dll.interception_destroy_context(self._context)
            self._context = None


@dataclass
class KeyboardDevice:
    """Represents a detected keyboard device."""
    device_number: int
    hardware_id: str

    def get_display_name(self) -> str:
        """Get display name for the device."""
        # Extract VID/PID from hardware ID
        hw_upper = self.hardware_id.upper()
        vid = pid = ""
        if "VID_" in hw_upper:
            try:
                vid_start = hw_upper.index("VID_") + 4
                vid = hw_upper[vid_start:vid_start + 4]
            except (ValueError, IndexError):
                pass
        if "PID_" in hw_upper:
            try:
                pid_start = hw_upper.index("PID_") + 4
                pid = hw_upper[pid_start:pid_start + 4]
            except (ValueError, IndexError):
                pass

        if vid and pid:
            return f"Keyboard {self.device_number} (VID:{vid} PID:{pid})"
        elif self.hardware_id:
            return f"Keyboard {self.device_number} ({self.hardware_id[:30]}...)"
        else:
            return f"Keyboard {self.device_number}"


class KeyInterceptor:
    """
    Intercepts keyboard input using Interception driver.
    Can filter by device and remap keys.
    """

    def __init__(self):
        self._driver: Optional[InterceptionDriver] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Target device to intercept (device number 1-10)
        self._target_device: Optional[int] = None

        # Key mappings: input_vk -> output_vk or [vk1, vk2, ...] for combos
        self._mappings: Dict[int, Union[int, List[int]]] = {}

        # Callbacks
        self._on_key_event: Optional[Callable[[KeyEvent], None]] = None

        # Flag to enable/disable interception
        self._enabled = True

        # Cache of keyboard devices
        self._keyboards: List[KeyboardDevice] = []

    def _init_driver(self):
        """Initialize the Interception driver."""
        if self._driver is None:
            self._driver = InterceptionDriver()
            self._enumerate_keyboards()

    def _enumerate_keyboards(self):
        """Enumerate all keyboard devices."""
        self._keyboards = []
        for device in range(1, INTERCEPTION_MAX_KEYBOARD + 1):
            if self._driver.is_keyboard(device):
                hw_id = self._driver.get_hardware_id(device)
                if hw_id:  # Only add if device is connected
                    self._keyboards.append(KeyboardDevice(device, hw_id))

    def get_keyboards(self) -> List[KeyboardDevice]:
        """Get list of detected keyboards."""
        self._init_driver()
        self._enumerate_keyboards()
        return self._keyboards.copy()

    def set_target_device(self, device: Optional[int]):
        """Set the device to intercept keys from (1-10 for keyboards)."""
        self._target_device = device

    def set_target_device_by_hardware_id(self, hardware_id: str):
        """Set target device by hardware ID."""
        self._init_driver()
        for kb in self._keyboards:
            if kb.hardware_id == hardware_id:
                self._target_device = kb.device_number
                return
        self._target_device = None

    def set_mappings(self, mappings: Dict[int, Union[int, List[int]]]):
        """Set key mappings (input_vk -> output_vk or [vk1, vk2, ...])."""
        self._mappings = mappings.copy()

    def add_mapping(self, input_vk: int, output: Union[int, List[int]]):
        """Add a key mapping (single key or combo)."""
        self._mappings[input_vk] = output

    def remove_mapping(self, input_vk: int):
        """Remove a key mapping."""
        self._mappings.pop(input_vk, None)

    def clear_mappings(self):
        """Clear all mappings."""
        self._mappings.clear()

    def set_enabled(self, enabled: bool):
        """Enable or disable key interception."""
        self._enabled = enabled

    def set_key_event_callback(self, callback: Optional[Callable[[KeyEvent], None]]):
        """Set callback for key events (used during capture mode)."""
        self._on_key_event = callback

    def _scan_to_vk(self, scan_code: int, extended: bool = False) -> int:
        """Convert scan code to virtual key code."""
        # Handle extended keys
        if extended:
            # Extended scan codes (e.g., numpad enter, right ctrl, etc.)
            extended_map = {
                0x1C: 0x0D,  # Numpad Enter
                0x1D: 0x11,  # Right Ctrl
                0x38: 0x12,  # Right Alt
                0x47: 0x24,  # Home
                0x48: 0x26,  # Up
                0x49: 0x21,  # Page Up
                0x4B: 0x25,  # Left
                0x4D: 0x27,  # Right
                0x4F: 0x23,  # End
                0x50: 0x28,  # Down
                0x51: 0x22,  # Page Down
                0x52: 0x2D,  # Insert
                0x53: 0x2E,  # Delete
            }
            return extended_map.get(scan_code, scan_code)

        return SCAN_TO_VK.get(scan_code, scan_code)

    def _vk_to_scan(self, vk_code: int) -> int:
        """Convert virtual key code to scan code."""
        return VK_TO_SCAN.get(vk_code, vk_code)

    def _intercept_loop(self):
        """Main interception loop running in a thread."""
        print("[INTERCEPTOR] Loop started", flush=True)
        self._driver.set_keyboard_filter(INTERCEPTION_FILTER_KEY_ALL)

        while self._running:
            device = self._driver.wait(timeout_ms=100)
            if device == 0:
                continue  # Timeout

            stroke = self._driver.receive(device)
            if stroke is None:
                continue

            is_key_up = bool(stroke.state & INTERCEPTION_KEY_UP)
            is_extended = bool(stroke.state & INTERCEPTION_KEY_E0)
            scan_code = stroke.code
            vk_code = self._scan_to_vk(scan_code, is_extended)

            # Get hardware ID for this device
            hw_id = ""
            for kb in self._keyboards:
                if kb.device_number == device:
                    hw_id = kb.hardware_id
                    break

            # Notify callback if set
            if self._on_key_event:
                event = KeyEvent(
                    scan_code=scan_code,
                    vk_code=vk_code,
                    is_key_up=is_key_up,
                    device=device,
                    hardware_id=hw_id
                )
                self._on_key_event(event)

            # Check if we should remap this key
            should_remap = False
            if self._enabled and vk_code in self._mappings:
                # Check device match if target is set
                if self._target_device is None or device == self._target_device:
                    should_remap = True

            if should_remap:
                output = self._mappings[vk_code]

                if isinstance(output, list):
                    # Combo mapping - only trigger on key down, block key up
                    if not is_key_up:
                        # Import here to avoid circular imports
                        from core.key_sender import send_key_combo
                        send_key_combo(output)
                    # Don't send the original key (it's consumed)
                else:
                    # Single key mapping - send remapped key
                    output_scan = self._vk_to_scan(output)

                    new_stroke = InterceptionKeyStroke()
                    new_stroke.code = output_scan
                    new_stroke.state = stroke.state  # Preserve up/down state
                    new_stroke.information = stroke.information

                    self._driver.send(device, new_stroke)
            else:
                # Pass through original key
                self._driver.send(device, stroke)

        print("[INTERCEPTOR] Loop ended", flush=True)

    def start(self):
        """Start the key interceptor."""
        if self._running:
            return

        self._init_driver()
        self._running = True
        self._thread = threading.Thread(target=self._intercept_loop, daemon=True)
        self._thread.start()
        print("[INTERCEPTOR] Started", flush=True)

    def stop(self):
        """Stop the key interceptor."""
        if not self._running:
            return

        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

        if self._driver:
            self._driver.destroy()
            self._driver = None

        print("[INTERCEPTOR] Stopped", flush=True)


# Global interceptor instance
_interceptor: Optional[KeyInterceptor] = None


def get_interceptor() -> KeyInterceptor:
    """Get the global key interceptor instance."""
    global _interceptor
    if _interceptor is None:
        _interceptor = KeyInterceptor()
    return _interceptor
