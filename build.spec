import os
from pathlib import Path
import vgamepad

vgamepad_pkg_path = Path(vgamepad.__file__).parent
vgamepad_path = vgamepad_pkg_path / 'win' / 'vigem' / 'client'

if not vgamepad_path.exists():
    raise FileNotFoundError(f"vgamepad DLL directory not found: {vgamepad_path}")

site_packages_path = vgamepad_pkg_path.parent
vgamepad_dlls = []
for dll in vgamepad_path.rglob('*.dll'):
    dest = str(dll.parent.relative_to(site_packages_path))
    vgamepad_dlls.append((str(dll), dest))

vigem_installers = sorted(Path('.').glob('ViGEmBus_*.exe'))
if not vigem_installers:
    raise FileNotFoundError("No ViGEmBus_*.exe found in project root")
vigem_installer = str(vigem_installers[-1])

a = Analysis(
    ['main.py'],
    binaries=vgamepad_dlls,
    datas=[
        ('NPG-Controller.ui', '.'),
        ('Controller-Keybinds.ui', '.'),
        ('icons', 'icons'),
        (vigem_installer, '.'),
    ],
    hiddenimports=['vgamepad', 'bleak', 'PySide6.QtSvg'],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name='NPG Lite SNES',
    console=True,
    icon='icons/app_icon.ico',
)
