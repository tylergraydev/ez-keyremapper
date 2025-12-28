"""
First-run setup - checks for driver and installs if needed.
"""
import os
import sys
import ctypes
import subprocess
import tempfile
import zipfile
import urllib.request
import shutil
from pathlib import Path


INTERCEPTION_RELEASE_URL = "https://github.com/oblitum/Interception/releases/download/v1.0.1/Interception.zip"


def is_admin() -> bool:
    """Check if running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def check_driver_installed() -> bool:
    """Check if the Interception driver is installed."""
    try:
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


def get_app_data_dir() -> Path:
    """Get the app data directory."""
    app_data = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
    return Path(app_data) / "EZKeyRemapper"


def get_driver_installer_path() -> Path:
    """Get path to the bundled driver installer."""
    # When running as PyInstaller exe, files are in _MEIPASS
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).parent.parent

    return base_dir / "driver" / "install-interception.exe"


def download_driver_installer() -> Path:
    """Download and extract the driver installer."""
    app_data = get_app_data_dir()
    driver_dir = app_data / "driver"
    installer_path = driver_dir / "install-interception.exe"

    if installer_path.exists():
        return installer_path

    print("Downloading Interception driver...", flush=True)

    try:
        driver_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "Interception.zip")

            # Download
            urllib.request.urlretrieve(INTERCEPTION_RELEASE_URL, zip_path)

            # Extract
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Copy installer files
            installer_source = Path(temp_dir) / "Interception" / "command line installer"
            if installer_source.exists():
                for f in installer_source.iterdir():
                    shutil.copy2(f, driver_dir / f.name)

        return installer_path

    except Exception as e:
        print(f"Error downloading driver: {e}", flush=True)
        return None


def install_driver_with_elevation(installer_path: Path) -> bool:
    """Run the driver installer with admin elevation."""
    try:
        # Use ShellExecute to run with elevation
        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",  # Run as admin
            str(installer_path),
            "/install",
            str(installer_path.parent),
            1  # SW_SHOWNORMAL
        )
        # ShellExecute returns > 32 on success
        return result > 32
    except Exception as e:
        print(f"Error running installer: {e}", flush=True)
        return False


def show_driver_setup_dialog() -> bool:
    """Show a dialog asking to install the driver. Returns True if user agrees."""
    try:
        from PyQt5.QtWidgets import QApplication, QMessageBox

        # Create app if needed
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Driver Installation Required")
        msg.setText("EZ Key Remapper needs to install the Interception driver.")
        msg.setInformativeText(
            "This is required for device-specific key remapping.\n\n"
            "• One-time installation\n"
            "• Requires administrator privileges\n"
            "• Requires a system reboot after installation\n\n"
            "Click 'Install' to proceed."
        )
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.button(QMessageBox.Ok).setText("Install Driver")
        msg.setDefaultButton(QMessageBox.Ok)

        return msg.exec_() == QMessageBox.Ok

    except ImportError:
        # Fallback to console
        print("\n" + "=" * 50)
        print("DRIVER INSTALLATION REQUIRED")
        print("=" * 50)
        print("\nThe Interception driver needs to be installed.")
        print("This requires admin privileges and a reboot.")
        response = input("\nInstall now? (y/n): ").strip().lower()
        return response == 'y'


def show_reboot_dialog():
    """Show a dialog asking to reboot."""
    try:
        from PyQt5.QtWidgets import QApplication, QMessageBox

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Reboot Required")
        msg.setText("Driver installation complete!")
        msg.setInformativeText(
            "You need to reboot your computer for the driver to work.\n\n"
            "After rebooting, run EZ Key Remapper again."
        )
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    except ImportError:
        print("\n" + "=" * 50)
        print("REBOOT REQUIRED")
        print("=" * 50)
        print("\nPlease reboot your computer, then run the app again.")
        input("\nPress Enter to exit...")


def run_first_time_setup(skip_check: bool = False) -> bool:
    """
    Run first-time setup if needed.

    Args:
        skip_check: If True, skip the driver check and always show install dialog

    Returns:
        True if setup completed (user should reboot), False if user cancelled
    """
    # Check if driver is already installed (unless we're told to skip)
    if not skip_check and check_driver_installed():
        return True

    # Show dialog asking to install
    if not show_driver_setup_dialog():
        return False  # User cancelled

    # Get or download the installer
    installer_path = get_driver_installer_path()
    if not installer_path.exists():
        installer_path = download_driver_installer()

    if not installer_path or not installer_path.exists():
        try:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                None,
                "Setup Error",
                "Could not download the driver installer.\n\n"
                "Please download manually from:\n"
                "https://github.com/oblitum/Interception/releases"
            )
        except:
            print("ERROR: Could not download driver installer")
        return False

    # Run the installer with elevation
    print("Installing driver (you may see a UAC prompt)...", flush=True)
    if install_driver_with_elevation(installer_path):
        # Wait a moment for the installer to complete
        import time
        time.sleep(2)

        # Check if it worked
        if check_driver_installed():
            return True
        else:
            # Driver installed but needs reboot
            show_reboot_dialog()
            return False
    else:
        try:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                None,
                "Installation Cancelled",
                "Driver installation was cancelled.\n\n"
                "The app requires the Interception driver to function."
            )
        except:
            print("Driver installation cancelled.")
        return False


if __name__ == "__main__":
    # Test the setup
    if check_driver_installed():
        print("Driver is already installed!")
    else:
        print("Driver not installed. Running setup...")
        run_first_time_setup()
