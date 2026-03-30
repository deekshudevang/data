import sys
import os
import time
import subprocess
import pyautogui
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Launch the app in a separate process
proc = subprocess.Popen(["python", "app.py"])

# Give it 4 seconds to fully load
time.sleep(4.0)

# Capture the full screen (the app window should be visible)
screenshot_path = os.path.join(os.getcwd(), "app_new_ui.png")
pyautogui.screenshot(screenshot_path)

# Kill the process
proc.terminate()

print(f"✅ Screenshot captured: {screenshot_path}")
