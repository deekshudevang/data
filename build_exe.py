# build_exe.py — Build Windows .exe with PyInstaller
"""
Run this script to package the app into a standalone .exe:
    python build_exe.py
Output will be in the /dist folder.
"""

import subprocess
import sys
import os

APP_NAME = "AI_DataEntry_Automation"
ENTRY_POINT = "app.py"
ICON_FILE = "icon.ico"  # Place your .ico file here (optional)

# Extra data files to bundle
datas = [
    ("memory.json", ".") if os.path.exists("memory.json") else None,
]
datas = [d for d in datas if d]

hidden_imports = [
    "sklearn.feature_extraction.text",
    "sklearn.metrics.pairwise",
    "pytesseract",
    "cv2",
    "pyautogui",
    "PIL",
    "pyperclip",
    "psutil",
]

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    "--windowed",
    f"--name={APP_NAME}",
    "--clean",
    "--noconfirm",
]

if os.path.exists(ICON_FILE):
    cmd.append(f"--icon={ICON_FILE}")

for imp in hidden_imports:
    cmd += ["--hidden-import", imp]

for src, dst in datas:
    cmd += ["--add-data", f"{src};{dst}"]

cmd.append(ENTRY_POINT)

print("=" * 60)
print(f"Building {APP_NAME}.exe ...")
print("=" * 60)
print("Command:", " ".join(cmd))
print()

result = subprocess.run(cmd, check=False)

if result.returncode == 0:
    print()
    print("=" * 60)
    print(f"✅ SUCCESS! Executable: dist/{APP_NAME}.exe")
    print("=" * 60)
else:
    print()
    print("❌ Build failed. Check PyInstaller output above.")
    sys.exit(1)
