"""
Build script for EZ Key Remapper.
Downloads dependencies and creates the executable.
"""
import os
import sys
import subprocess
import zipfile
import tempfile
import urllib.request
import shutil
from pathlib import Path

INTERCEPTION_RELEASE_URL = "https://github.com/oblitum/Interception/releases/download/v1.0.1/Interception.zip"


def main():
    project_dir = Path(__file__).parent
    driver_dir = project_dir / "interception_driver"
    dll_path = project_dir / "interception.dll"

    print("=" * 60)
    print("EZ Key Remapper - Build Script")
    print("=" * 60)
    print()

    # Step 1: Download Interception if needed
    if not driver_dir.exists() or not dll_path.exists():
        print("[1/3] Downloading Interception driver...")
        download_interception(project_dir)
    else:
        print("[1/3] Interception files already present")

    # Step 2: Install PyInstaller if needed
    print("[2/3] Checking PyInstaller...")
    try:
        import PyInstaller
        print("      PyInstaller is installed")
    except ImportError:
        print("      Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    # Step 3: Build the executable
    print("[3/3] Building executable...")
    print()

    result = subprocess.run([
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "ez_keyremapper.spec"
    ], cwd=project_dir)

    if result.returncode == 0:
        print()
        print("=" * 60)
        print("BUILD SUCCESSFUL!")
        print("=" * 60)
        print()
        print(f"Executable created at:")
        print(f"  {project_dir / 'dist' / 'EZ Key Remapper.exe'}")
        print()
        print("This single .exe file includes everything needed.")
        print("On first run, it will prompt to install the driver.")
    else:
        print()
        print("BUILD FAILED!")
        return 1

    return 0


def download_interception(project_dir: Path):
    """Download and extract Interception files."""
    driver_dir = project_dir / "interception_driver"
    dll_path = project_dir / "interception.dll"

    print(f"      Downloading from {INTERCEPTION_RELEASE_URL}")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "Interception.zip")

            # Download
            urllib.request.urlretrieve(INTERCEPTION_RELEASE_URL, zip_path)
            print("      Download complete")

            # Extract
            print("      Extracting...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            extracted_dir = Path(temp_dir) / "Interception"

            # Copy DLL
            dll_source = extracted_dir / "library" / "x64" / "interception.dll"
            if dll_source.exists():
                shutil.copy2(dll_source, dll_path)
                print(f"      DLL installed: {dll_path}")

            # Copy driver installer
            installer_source = extracted_dir / "command line installer"
            if installer_source.exists():
                if driver_dir.exists():
                    shutil.rmtree(driver_dir)
                shutil.copytree(installer_source, driver_dir)
                print(f"      Driver installer extracted: {driver_dir}")

        print("      Done!")

    except Exception as e:
        print(f"      ERROR: {e}")
        raise


if __name__ == "__main__":
    sys.exit(main() or 0)
