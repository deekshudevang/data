# ⚡ MRJ MPF Data Entry Automation Bot

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-windows-lightgray.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-green.svg)

> **Top-Grade, production-ready form filling automation engineered specifically for the MRJ MPF Form Filling Software (v7.3).**

This dedicated application mimics a human data entry operator by reading bulk data (CSV/JSON), visually synchronizing with the software's load states, typing records with randomized human delays, and executing precise mouse clicks to complete the submission sequence.

---

## 🚀 Key Features

- **🎯 Custom Coordinate Mapping:** Map exact mouse clicks for "Upload Details", "Take Screenshot", and "Load Another Form" buttons.
- **👁️ Visual Synchronization (Smart Wait):** Uses OpenCV computer vision to detect the MRJ "Downloading Form" modal, ensuring the bot *never* types outside the active form.
- **⏱️ Dynamic Network Delays:** Fully configurable wait times post-upload to account for varying internet speeds.
- **⌨️ Human-like Actuation:** Randomized typing delays and `PyAutoGUI` interactions prevent detection and crashes.
- **📦 Zero-Setup Executable:** Provided as a standalone Windows `.exe`—no Python installation required for end-users.

---

## 🖥️ How to Use (End-User)

If you are a data entry operator receiving this tool, you do not need to deal with code. 

1. **Launch the Bot**
   - Double-click `AI_DataEntry_Automation.exe` (located in the `dist` folder or your Desktop shortcut).
2. **Setup your Data**
   - In the **📂 Data File** section, click `Browse...` and select your CSV or JSON data source.
3. **Calibrate for your Screen**
   - In the **📌 End-of-Form Custom Clicks** panel, click `🎯 Pick Coords`. 
   - You have 3 seconds to move your mouse over the corresponding button on the MRJ software (e.g., "Upload"). The exact screen coordinates will lock in automatically.
   - Set your **Wait** times (e.g., 5s for internet upload delay).
4. **Start Automation**
   - Click the massive **▶ Start Automation** button at the top of the interface.
   - Quickly switch to the MRJ MPF software window.
   - Let the bot do the work!

> **💡 Tip:** If you resize or move the MRJ application window, just re-calibrate the coordinates using the `Pick Coords` buttons.

---

## 🛠️ Developer Setup & Build Instructions

If you are modifying the source code, follow these steps to run and build the application from scratch.

### Prerequisites

- **Python 3.10+**
- **Tesseract OCR**: Download from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) and install to `C:\Program Files\Tesseract-OCR\`.

### Installation

```bash
git clone https://github.com/deekshudevang/data.git
cd data
pip install -r requirements.txt
```

### Running Locally

```bash
python app.py
```

### Building the Executable

To compile the application into a standalone `.exe`:

```bash
python build_exe.py
```

*The output will be placed in the `dist/` directory as `AI_DataEntry_Automation.exe`.*

---

## 📁 Project Structure

```text
data entry/
├── app.py              # Main PyQt5 graphical interface
├── mpf_bot.py          # Core logic for navigating the 18-field MRJ form
├── actions.py          # PyAutoGUI human-like fill and click automation
├── vision.py           # OpenCV modal detection (Smart Wait)
├── build_exe.py        # PyInstaller packaging script
├── requirements.txt    # Python dependency tree
└── dist/
    └── AI_DataEntry_Automation.exe  # The final compiled application
```

---

## 📄 License
MIT License.
