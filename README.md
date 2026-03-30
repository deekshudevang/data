# AI Smart Data Entry Automation Tool

> **Production-ready intelligent form-filling desktop software with self-learning AI.**

---

## 🚀 Features

| Feature | Description |
|---|---|
| 🔤 OCR Extraction | Tesseract reads text from any visible app |
| 🔎 Vision Detection | OpenCV finds input fields without selectors |
| 🤖 Semantic Matching | TF-IDF cosine similarity matches labels to fields |
| 🧠 Self-Learning AI | Learns from every run; confidence improves over time |
| ⌨️ Human-like Typing | Randomized delays, clipboard paste, tab navigation |
| 📊 Live Dashboard | Real-time logs, filled-field tracker, memory stats |
| ⚙️ Configurable | Speed, OCR language, confidence threshold, retry count |
| 🗂️ MPF Bot Mode | Dedicated high-speed automation for MRJ MPF Software |
| 📦 Distributable | Build to `.exe` with one command |

---

## 📁 Project Structure

```
data entry/
├── app.py              # Main PyQt5 desktop application
├── bot_engine.py       # Automation orchestration engine
├── ocr.py              # Tesseract OCR text extraction
├── vision.py           # OpenCV field detection & screen capture
├── mapping.py          # Semantic field matching (scikit-learn)
├── actions.py          # PyAutoGUI human-like fill automation
├── learning.py         # Self-learning memory + confidence engine
├── memory.json         # Auto-created: learned mappings database
├── automation.log      # Auto-created: run logs
├── requirements.txt    # Python dependencies
├── build_exe.py        # PyInstaller .exe builder
└── README.md
```

---

## ⚡ Quick Start

### 1. Install Prerequisites

**Python 3.10+** required.

```bash
pip install -r requirements.txt
```

**Tesseract OCR** (required):
- Download installer: https://github.com/UB-Mannheim/tesseract/wiki
- Install to: `C:\Program Files\Tesseract-OCR\`
- During install, select additional languages if needed

### 2. Run the App

```bash
python app.py
```

---

## 🖥️ How to Use

1. **Open your source data** (spreadsheet, document, or any app) on screen
2. **Open the target form** (web browser, desktop app) on screen
3. Click **▶ Start Automation** in the tool
4. The AI will:
   - Capture the screen
   - Extract text via OCR
   - Detect form fields visually
   - Match labels to fields using AI
   - Fill fields with human-like typing
   - Learn from the session for next time

> **Tip:** Place your data source on the left half and the form on the right half of the screen for best results.

### 🗂️ Using the MPF Bot Mode
1. Click the **🗂️ MPF Bot** tab.
2. Select your CSV or JSON data file (or click **Create Sample CSV**).
3. Open the **MRJ MPF Form Filling Software** and ensure it's on the first field (Name).
4. Click **▶ Start MPF Bot**.
5. Switch to the MPF software window immediately.
6. The bot will automatically fill each record and progress through the file.

---

## 🧠 Self-Learning System

The tool automatically learns from every automation run:

- **First run**: Uses AI semantic matching
- **After corrections**: Saves improved mappings
- **Later runs**: Uses memory-first with high confidence
- **Storage**: `memory.json` in the project folder

To view learned mappings, go to the **🧠 AI Memory** tab.

---

## 📦 Build .exe (Windows)

```bash
pip install pyinstaller
python build_exe.py
```

Output: `dist/AI_DataEntry_Automation.exe`

---

## ⚙️ Settings Guide

| Setting | Description |
|---|---|
| Fill Speed | 1–10 slider. Lower = slower + more reliable |
| OCR Language | Select language of your source data |
| Confidence Threshold | Min % confidence before auto-fill (default 30%) |
| Continuous Mode | Automatically handles multi-page forms |
| Max Retries | How many times to retry a failed field fill |

---

## 🔧 Troubleshooting

| Issue | Fix |
|---|---|
| "No data pairs extracted" | Make sure source data is visible on screen |
| "No input fields detected" | Ensure the form window is in focus |
| OCR errors | Increase screen resolution or zoom |
| Tesseract not found | Check install path in `ocr.py` |

---

## 📄 License

MIT License — Free for personal and commercial use.
