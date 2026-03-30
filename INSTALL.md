# INSTALLATION GUIDE
# AI Smart Data Entry Automation Tool
# =====================================

## STEP 1 — Install Python 3.10 or newer

Download: https://www.python.org/downloads/

✅ During install, CHECK "Add Python to PATH"

Verify:
    python --version


## STEP 2 — Install Tesseract OCR (REQUIRED)

Download the Windows installer:
    https://github.com/UB-Mannheim/tesseract/wiki

Installation notes:
- Install to default location: C:\Program Files\Tesseract-OCR\
- During setup, select "Additional language data" if you need
  non-English OCR support (French, German, Spanish, etc.)

Verify:
    "C:\Program Files\Tesseract-OCR\tesseract.exe" --version


## STEP 3 — Install Python Dependencies

Open Command Prompt or PowerShell in the project folder:

    pip install -r requirements.txt

This installs:
  - PyQt5        — Desktop UI
  - opencv-python — Computer vision
  - pytesseract  — OCR wrapper
  - pyautogui    — Mouse/keyboard automation
  - scikit-learn — Semantic matching AI
  - Pillow       — Image processing
  - numpy        — Array operations
  - pywin32      — Windows API
  - psutil       — Process utilities


## STEP 4 — Run the Application

    python app.py

The main window will open immediately.


## STEP 5 (Optional) — Build Standalone .exe

Install PyInstaller:
    pip install pyinstaller

Then build:
    python build_exe.py

Output:
    dist\AI_DataEntry_Automation.exe

The .exe can be distributed to any Windows PC
(Tesseract must be installed on the target machine).


## TROUBLESHOOTING

Problem:  "tesseract is not installed or it's not in your PATH"
Fix:      Edit ocr.py line 17:
          TESSERACT_CMD = r"C:\Your\Custom\Path\tesseract.exe"

Problem:  "No module named PyQt5"
Fix:      pip install PyQt5

Problem:  pyautogui.FailSafeException
Fix:      Move mouse away from screen corners while automation runs

Problem:  Low OCR accuracy
Fix:      - Increase screen DPI/zoom in Windows Display Settings
          - Use "Fill Speed" slider to slow down automation

## REQUIREMENTS SUMMARY

  Software          Version
  ────────────────────────────────
  Python            3.10+
  Tesseract OCR     5.x (Windows)
  PyQt5             5.15+
  OpenCV            4.8+
  scikit-learn      1.3+
  PyInstaller       6.0+ (for .exe)
