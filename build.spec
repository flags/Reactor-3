# -*- mode: python ; coding: utf-8 -*-

import os.path
import subprocess
import tempfile

# Create a temporary file with version info.
version_file = os.path.join(tempfile.gettempdir(), "git-version.txt")
with open(version_file, "w") as f:
    f.write(subprocess.check_output(["git", "describe", "--tags"], text=True).strip())

block_cipher = None

a = Analysis(
    ["reactor-3.py"],
    binaries=[],
    datas=[("readme.md", "."), ("license.txt", "."), (version_file, ".")],
    hiddenimports=[
        "alife.action",
        "alife.snapshots",
        "alife.judgement",
        "alife.chunks",
        "alife.brain",
        "alife.speech",
        "alife.stances",
        "alife.jobs",
        "alife.groups",
        "alife.factions",
        "alife.camps",
        "alife.sight",
        "alife.rawparse",
        "alife.noise",
        "alife.planner",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="reactor-3",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    Tree("data", prefix="data", excludes=["maps"]),  # Include data directory.
    strip=False,
    upx=True,
    upx_exclude=[],
    name="reactor-3",
)
