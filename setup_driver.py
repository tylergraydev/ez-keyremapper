"""
Setup script for Interception driver.
Downloads the driver and provides installation instructions.
"""
import os
import sys
import zipfile
import tempfile
import urllib.request
import shutil
import subprocess

INTERCEPTION_RELEASE_URL = "https://github.com/oblitum/Interception/releases/download/v1.0.1/Interception.zip"


def main():
    print("=" * 60)
    print("EZ Key Remapper - Interception Driver Setup")
    print("=" * 60)
    print()

    project_dir = os.path.dirname(os.path.abspath(__file__))
    dll_path = os.path.join(project_dir, "interception.dll")
    driver_dir = os.path.join(project_dir, "interception_driver")

    # Check if DLL already exists
    if os.path.exists(dll_path):
        print(f"[OK] DLL already exists: {dll_path}")
    else:
        print("[...] DLL not found, downloading...")

    # Check if driver installer already exists
    installer_path = os.path.join(driver_dir, "install-interception.exe")
    if os.path.exists(installer_path):
        print(f"[OK] Driver installer already exists")
        print()
        print_install_instructions(driver_dir)
        return

    # Download and extract
    print()
    print("[...] Downloading Interception driver package...")
    print(f"      URL: {INTERCEPTION_RELEASE_URL}")
    print()

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "Interception.zip")

            # Download
            urllib.request.urlretrieve(INTERCEPTION_RELEASE_URL, zip_path)
            print("[OK] Download complete")

            # Extract
            print("[...] Extracting...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Find the extracted folder
            extracted_dir = os.path.join(temp_dir, "Interception")
            if not os.path.exists(extracted_dir):
                # Maybe it extracted directly
                extracted_dir = temp_dir

            # Copy DLL
            dll_source = os.path.join(extracted_dir, "library", "x64", "interception.dll")
            if os.path.exists(dll_source):
                shutil.copy2(dll_source, dll_path)
                print(f"[OK] DLL installed: {dll_path}")
            else:
                print(f"[!] Could not find DLL in archive")

            # Copy driver installer
            installer_source = os.path.join(extracted_dir, "command line installer")
            if os.path.exists(installer_source):
                if os.path.exists(driver_dir):
                    shutil.rmtree(driver_dir)
                shutil.copytree(installer_source, driver_dir)
                print(f"[OK] Driver installer extracted: {driver_dir}")
            else:
                print(f"[!] Could not find installer in archive")

        print()
        print("[OK] Setup complete!")
        print()
        print_install_instructions(driver_dir)

    except Exception as e:
        print(f"[ERROR] {e}")
        print()
        print("Please download manually from:")
        print(INTERCEPTION_RELEASE_URL)
        return 1

    return 0


def print_install_instructions(driver_dir):
    """Print instructions for installing the driver."""
    print("=" * 60)
    print("DRIVER INSTALLATION REQUIRED")
    print("=" * 60)
    print()
    print("The Interception kernel driver must be installed (one-time).")
    print("This requires Administrator privileges and a reboot.")
    print()
    print("To install:")
    print()
    print("  1. Open Command Prompt as Administrator")
    print("  2. Run this command:")
    print()
    print(f'     cd "{driver_dir}"')
    print(f'     install-interception.exe /install')
    print()
    print("  3. Reboot your computer")
    print()
    print("After reboot, run the app with: run.bat")
    print()
    print("=" * 60)

    # Offer to open admin prompt
    print()
    response = input("Would you like to open an Admin Command Prompt now? (y/n): ").strip().lower()
    if response == 'y':
        try:
            # Create a batch file that will run the installer
            batch_content = f'''@echo off
cd /d "{driver_dir}"
echo.
echo Current directory: %CD%
echo.
echo Run this command to install:
echo   install-interception.exe /install
echo.
echo After installation, reboot your computer.
echo.
cmd /k
'''
            batch_path = os.path.join(driver_dir, "install_driver.bat")
            with open(batch_path, 'w') as f:
                f.write(batch_content)

            # Run as admin
            subprocess.run([
                'powershell', '-Command',
                f'Start-Process cmd -ArgumentList "/k cd /d \\"{driver_dir}\\" && echo Ready to install. Run: install-interception.exe /install" -Verb RunAs'
            ], shell=True)
            print()
            print("Admin Command Prompt opened. Run the install command there.")
        except Exception as e:
            print(f"Could not open admin prompt: {e}")
            print("Please open Command Prompt as Administrator manually.")


if __name__ == "__main__":
    sys.exit(main() or 0)
