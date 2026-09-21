import os
from pathlib import Path
from importlib.util import find_spec

vgamepad_pkg_path = Path(find_spec('vgamepad').submodule_search_locations[0])
vgamepad_path = vgamepad_pkg_path / 'win' / 'vigem' / 'client'

if not vgamepad_path.exists():
    raise FileNotFoundError(f"vgamepad DLL directory not found: {vgamepad_path}")

site_packages_path = vgamepad_pkg_path.parent
vgamepad_dlls = []
for dll in vgamepad_path.rglob('*.dll'):
    dest = str(dll.parent.relative_to(site_packages_path))
    vgamepad_dlls.append((str(dll), dest))

VIGEM_FILENAME = 'ViGEmBus_1.22.0_x64_x86_arm64.exe'
VIGEM_URL = f'https://github.com/nefarius/ViGEmBus/releases/download/v1.22.0/{VIGEM_FILENAME}'

project_root = Path(SPECPATH)
vigem_installer = project_root / VIGEM_FILENAME
if not vigem_installer.exists():
    import urllib.request
    print(f'Downloading {VIGEM_FILENAME} ...')
    part_file = project_root / (VIGEM_FILENAME + '.part')
    urllib.request.urlretrieve(VIGEM_URL, part_file)
    part_file.replace(vigem_installer)

a = Analysis(
    ['main.py'],
    binaries=vgamepad_dlls,
    datas=[
        ('NPG-Controller.ui', '.'),
        ('Controller-Keybinds.ui', '.'),
        ('icons', 'icons'),
        (str(vigem_installer), '.'),
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
