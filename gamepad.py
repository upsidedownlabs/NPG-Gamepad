# ViGEmBus driver check/install and vgamepad setup

import sys
import os


def resource_path(relative_path):
    """Get path to bundled resource. Works in both dev and PyInstaller exe."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


VIGEMBUS_FILENAME = 'ViGEmBus_1.22.0_x64_x86_arm64.exe'
VIGEMBUS_URL = f'https://github.com/nefarius/ViGEmBus/releases/download/v1.22.0/{VIGEMBUS_FILENAME}'


def _download_vigembus_installer(dest):
    import urllib.request
    print('Downloading ViGEmBus installer...')
    part_file = dest + '.part'
    try:
        urllib.request.urlretrieve(VIGEMBUS_URL, part_file)
        os.replace(part_file, dest)
    except Exception as e:
        print(f'ViGEmBus installer download failed: {e}')
        if os.path.exists(part_file):
            os.remove(part_file)


def ensure_vigembus():
    """Install ViGEmBus driver if not already installed and running."""
    import subprocess
    result = subprocess.run(['sc', 'query', 'ViGEmBus'], capture_output=True, text=True)
    if result.returncode == 0 and 'RUNNING' in result.stdout:
        return True
    installer = resource_path(VIGEMBUS_FILENAME)
    if not os.path.exists(installer) and not hasattr(sys, '_MEIPASS'):
        _download_vigembus_installer(installer)
    if not os.path.exists(installer):
        print('ViGEmBus installer not found')
        return False
    print('Installing ViGEmBus driver (admin required)...')
    try:
        import ctypes, time
        ctypes.windll.shell32.ShellExecuteW(None, "runas", installer, "/quiet /norestart", None, 1)
        # Poll for service availability (max ~30 seconds)
        for _ in range(30):
            time.sleep(1)
            result = subprocess.run(['sc', 'query', 'ViGEmBus'], capture_output=True, text=True)
            if result.returncode == 0:
                subprocess.run(['sc', 'start', 'ViGEmBus'], capture_output=True)
                time.sleep(1)
                # Verify running
                result = subprocess.run(['sc', 'query', 'ViGEmBus'], capture_output=True, text=True)
                if 'RUNNING' in result.stdout:
                    print('ViGEmBus installed and started successfully')
                    return True
        print('ViGEmBus installation timed out')
        return False
    except Exception as e:
        print(f'ViGEmBus install failed: {e}')
        return False


# Try to load vgamepad (needs ViGEmBus driver)
ensure_vigembus()
try:
    import vgamepad as vg
    HAS_VGAMEPAD = True
except Exception:
    HAS_VGAMEPAD = False
    print("vgamepad not available — virtual gamepad disabled")

# Map SNES button names to vgamepad constants
SNES_TO_XUSB = {}
if HAS_VGAMEPAD:
    SNES_TO_XUSB = {
        "A":          vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
        "B":          vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
        "X":          vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
        "Y":          vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
        "Dpad Up":    vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
        "Dpad Down":  vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
        "Dpad Left":  vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
        "Dpad Right": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
        "Start":      vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
        "L":          "LT",
        "R":          "RT",
    }
