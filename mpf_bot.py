"""
mpf_bot.py — MRJ MPF Form Filling Software Dedicated Automation Engine
Rebuilt for MPF Form Filling Software v7.3 (real field mapping from screen).

The left pane shows data as:   Label:Value   (colon-separated on same line)
The right pane has the input fields to fill — we Tab through them in order.

This version reads data DIRECTLY from the screen via OCR and fills the form.
"""

import time
import logging
import csv
import json
import os
import re
import threading
from pathlib import Path
from typing import Callable

import pyautogui
import pyperclip

import vision
import ocr

logger = logging.getLogger("MPF_Bot")

# ─── Real MPF Field Tab Order ─────────────────────────────────────────────────
# Matches the actual Tab order inside MPF Form Filling Software v7.3
# Each entry: (field_key, display_label, field_type)
# field_type: "text" | "dropdown" | "date" | "skip"

MPF_FIELD_ORDER = [
    # ── Member Basic Information ──────────────────────────────────────────────
    ("app_no",          "App No",               "text"),
    ("mbi_code",        "MBI Code",             "text"),
    ("full_name",       "Full Name",            "text"),
    ("gender",          "Gender",               "dropdown"),
    ("dob",             "Date Of Birth",        "date"),
    ("marital_status",  "Marital Status",       "dropdown"),
    ("state",           "State",                "dropdown"),
    ("district",        "District",             "dropdown"),
    ("taluk",           "Taluk",                "text"),
    ("pincode",         "Pincode",              "text"),
    ("house_type",      "House Type",           "dropdown"),

    # ── Religious and Astro Information ───────────────────────────────────────
    ("rai_code",        "RAI Code",             "text"),
    ("mother_tongue",   "Mother Tongue",        "dropdown"),
    ("religion",        "Religion",             "dropdown"),
    ("cast",            "Cast",                 "dropdown"),
    ("sub_cast",        "Sub Cast",             "text"),
    ("nakshatra",       "Nakshatra",            "dropdown"),
    ("rashi",           "Rashi",                "dropdown"),
    ("pada",            "Pada",                 "dropdown"),

    # ── Physical and Habits Information ───────────────────────────────────────
    ("phi_code",        "PHI Code",             "text"),
    ("health_info",     "Health Info",          "dropdown"),
    ("any_disability",  "Any Disability",       "dropdown"),
    ("diet",            "Diet",                 "dropdown"),
    ("height",          "Height",               "dropdown"),
    ("weight",          "Weight",               "dropdown"),

    # ── Family Information ────────────────────────────────────────────────────
    ("fai_code",        "FAI Code",             "text"),
    ("father_status",   "Father Status",        "dropdown"),
    ("father_name",     "Father Name",          "text"),
    ("mother_status",   "Mother Status",        "dropdown"),
    ("mother_name",     "Mother Name",          "text"),
    ("sister",          "Sister",               "dropdown"),
    ("brother",         "Brother",              "dropdown"),
    ("children_boy",    "Children Boy",         "dropdown"),
    ("children_girl",   "Children Girl",        "dropdown"),

    # ── Education and Career Information ──────────────────────────────────────
    ("eci_code",        "ECI Code",             "text"),
    ("education",       "Education",            "dropdown"),
    ("emp_status",      "Emp Status",           "dropdown"),
    ("annual_income",   "Annual Income",        "dropdown"),
]

# ─── OCR Label → Field Key Aliases ────────────────────────────────────────────
# Maps what OCR reads from the left pane → field_key above
COLUMN_ALIASES = {
    # App No
    "app no": "app_no", "appno": "app_no", "app number": "app_no",
    "app no.": "app_no",

    # MBI Code
    "mbi code": "mbi_code", "mbicode": "mbi_code", "mbi": "mbi_code",

    # Full Name
    "full name": "full_name", "name": "full_name", "fullname": "full_name",
    "applicant name": "full_name",

    # Gender
    "gender": "gender", "sex": "gender", "gend": "gender",

    # DOB
    "dob": "dob", "date of birth": "dob", "dateofbirth": "dob",
    "birth date": "dob", "d.o.b": "dob", "d.o.b.": "dob",

    # Marital Status
    "marital status": "marital_status", "maritalstatus": "marital_status",
    "marital": "marital_status",

    # State
    "state": "state",

    # District
    "district": "district", "dist": "district",

    # Taluk
    "taluk": "taluk", "taluka": "taluk",

    # Pincode
    "pincode": "pincode", "pin code": "pincode", "pin": "pincode",
    "postal code": "pincode",

    # House Type
    "house type": "house_type", "housetype": "house_type",
    "residence type": "house_type",

    # RAI Code
    "rai code": "rai_code", "raicode": "rai_code",

    # Mother Tongue
    "mother tongue": "mother_tongue", "mothertongue": "mother_tongue",
    "lang": "mother_tongue", "language": "mother_tongue",

    # Religion
    "religion": "religion", "relig": "religion",

    # Cast / Caste
    "cast": "cast", "caste": "cast",

    # Sub Cast
    "sub cast": "sub_cast", "subcast": "sub_cast", "sub caste": "sub_cast",
    "subcaste": "sub_cast",

    # Nakshatra
    "nakshatra": "nakshatra",

    # Rashi
    "rashi": "rashi", "rasi": "rashi",

    # Pada
    "pada": "pada",

    # PHI Code
    "phi code": "phi_code", "phicode": "phi_code",

    # Health Info
    "health info": "health_info", "healthinfo": "health_info",
    "health": "health_info",

    # Any Disability
    "any disability": "any_disability", "anydisability": "any_disability",
    "disability": "any_disability",

    # Diet
    "diet": "diet",

    # Height
    "height": "height",

    # Weight
    "weight": "weight",

    # FAI Code
    "fai code": "fai_code", "faicode": "fai_code",

    # Father Status
    "father status": "father_status", "fatherstatus": "father_status",

    # Father Name
    "father name": "father_name", "fathername": "father_name",
    "father's name": "father_name", "fathers name": "father_name",

    # Mother Status
    "mother status": "mother_status", "motherstatus": "mother_status",

    # Mother Name
    "mother name": "mother_name", "mothername": "mother_name",
    "mother's name": "mother_name",

    # Sister
    "sister": "sister",

    # Brother
    "brother": "brother",

    # Children Boy
    "children boy": "children_boy", "childrenboy": "children_boy",

    # Children Girl
    "children girl": "children_girl", "childrengirl": "children_girl",

    # ECI Code
    "eci code": "eci_code", "ecicode": "eci_code",

    # Education
    "education": "education", "edu": "education",
    "qualification": "education",

    # Emp Status
    "emp status": "emp_status", "empstatus": "emp_status",
    "employment status": "emp_status", "employment": "emp_status",

    # Annual Income
    "annual income": "annual_income", "annualincome": "annual_income",
    "income": "annual_income", "yearly income": "annual_income",
}

# ─── Value Normalizers for dropdowns ──────────────────────────────────────────
GENDER_MAP = {
    "male": "Male", "m": "Male",
    "female": "Female", "f": "Female",
}
MARITAL_MAP = {
    "never married": "Never Married",
    "single": "Never Married", "unmarried": "Never Married",
    "married": "Married",
    "divorced": "Divorced",
    "widowed": "Widowed",
}


class MPFBot:
    """
    Dedicated automation bot for MRJ MPF Form Filling Software v7.3.
    Reads data from screen (OCR Vision Mode) or CSV, then fills form via Tab.
    """

    def __init__(
        self,
        data_file: str = "",
        log_cb: Callable[[str], None] | None = None,
        status_cb: Callable[[str], None] | None = None,
        record_done_cb: Callable[[int, int], None] | None = None,
        stopped_cb: Callable[[], None] | None = None,
        fill_speed: float = 1.0,
        delay_between_fields: float = 0.25,
        delay_between_forms: float = 2.0,
        use_visual_sync: bool = True,
        end_sequence: dict | None = None,
        source_mode: str = "csv",       # "csv" or "screen"
        source_region: tuple | None = None,  # (x, y, w, h)
    ):
        self.data_file = data_file
        self.log_cb = log_cb or (lambda m: print(m))
        self.status_cb = status_cb or (lambda s: None)
        self.record_done_cb = record_done_cb or (lambda d, t: None)
        self.stopped_cb = stopped_cb or (lambda: None)

        self.fill_speed = max(fill_speed, 0.1)
        self.field_delay = delay_between_fields / self.fill_speed
        self.form_delay = delay_between_forms
        self.use_visual_sync = use_visual_sync
        self.end_sequence = end_sequence or {}

        self.source_mode = source_mode
        self.source_region = source_region

        self._running = False
        self._pause = False
        self._thread: threading.Thread | None = None

    # ─── Control ──────────────────────────────────────────────────────────────

    def start(self):
        self._running = True
        self._pause = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        self.log("⏹ Bot stopped")
        self.stopped_cb()

    def pause(self):
        self._pause = True
        self.log("⏸ Paused")

    def resume(self):
        self._pause = False
        self.log("▶ Resumed")

    @property
    def is_running(self):
        return self._running

    # ─── Main Loop ────────────────────────────────────────────────────────────

    def _run(self):
        try:
            for i in range(3, 0, -1):
                if not self._running:
                    return
                self.status(f"⏳ Starting in {i}s — switch to MPF window NOW!")
                time.sleep(1)

            if self.source_mode == "screen":
                self.log("👁️  Running in Live Vision Mode (Reading Screen)")
                self._run_vision_loop()
            else:
                self.log("📁 Running in CSV Data Mode")
                self._run_csv_loop()

        except Exception as e:
            self.log(f"❌ Critical error: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            self._running = False
            self.stopped_cb()

    # ─── CSV Loop ─────────────────────────────────────────────────────────────

    def _run_csv_loop(self):
        records = self._load_data()
        if not records:
            self.log("❌ No data loaded. Check your CSV/JSON file.")
            return

        total = len(records)
        self.status(f"Starting CSV automation — {total} records")

        for idx, record in enumerate(records, start=1):
            if not self._running:
                break
            while self._pause:
                time.sleep(0.3)

            self.log(f"\n━━━ Record {idx}/{total} ━━━")
            success = self._fill_form(record)
            if success:
                self.record_done_cb(idx, total)
                self.log(f"✅ Record {idx} submitted")

            if idx < total:
                self._wait_for_next_form()

        self.log(f"\n🎉 All {total} records processed!")

    # ─── Vision Loop ──────────────────────────────────────────────────────────

    def _run_vision_loop(self):
        if not self.source_region:
            self.log("❌ No Source Region defined! Calibrate first.")
            return

        idx = 1
        while self._running:
            while self._pause:
                time.sleep(0.3)

            self.log(f"\n━━━ Vision Record {idx} ━━━")
            self.status("👁️  Scraping data from screen...")

            record = self._scrape_from_screen()
            if not record:
                self.log("⚠️ No data extracted. Retrying in 3s...")
                time.sleep(3)
                continue

            self.log(f"📊 Extracted {len(record)} fields:")
            for k, v in record.items():
                self.log(f"   {k}: {v}")

            self.status(f"📝 Filling record {idx}...")
            
            # Ensure the app is in foreground
            self._focus_mpf_window()
            time.sleep(0.5)
            
            # Fully AI-automated focus logic: Find and click first input box
            self._find_and_click_first_field()
            
            success = self._fill_form(record)

            if success:
                self.record_done_cb(idx, idx)
                self.log(f"✅ Record {idx} done")

            idx += 1
            self._wait_for_next_form()

    # ─── Screen Scraping ──────────────────────────────────────────────────────

    def _scrape_from_screen(self) -> dict:
        """
        Capture the left data pane in multiple passes (scroll down to see all data),
        OCR each capture, and merge all label:value pairs.
        """
        if not self.source_region:
            return {}

        all_data = {}

        # Scroll back to top first
        self._scroll_pane(direction="top")
        time.sleep(0.3)

        # Capture multiple passes by scrolling down
        passes = 3  # Reduced from 5 for much faster "fraction of a second" speed
        for i in range(passes):
            if not self._running:
                break

            self.status(f"👁️  OCR scan {i+1}/{passes}...")
            img = vision.capture_screen(self.source_region)
            raw_text = ocr.extract_full_text(img)

            pairs = self._parse_mpf_left_pane(raw_text)
            for k, v in pairs.items():
                if v and k not in all_data:  # Prioritize first capture for overlapping text
                    all_data[k] = v

            if i < passes - 1:
                # Scroll down for next pass
                self._scroll_pane(direction="down")
                time.sleep(0.3)

        # Map all keys through aliases
        normalized = {}
        for raw_key, val in all_data.items():
            alias = COLUMN_ALIASES.get(raw_key.lower().strip(), None)
            if alias:
                normalized[alias] = val
            else:
                # Try partial match
                for alias_key, field_key in COLUMN_ALIASES.items():
                    if alias_key in raw_key.lower():
                        normalized[field_key] = val
                        break

        self.log(f"📊 Total mapped fields: {len(normalized)}")
        return normalized

    def _parse_mpf_left_pane(self, raw_text: str) -> dict:
        """
        Parse OCR text from the MRJ left pane.
        Handles the format:  Label:Value  or  Label: Value  (colon-joined)
        Also handles section headers like 'Member Basic Information'.
        """
        pairs = {}
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

        for line in lines:
            # Skip section headers (no colon, title-case long text)
            if not ":" in line:
                continue

            # Split on FIRST colon only
            colon_idx = line.index(":")
            label = line[:colon_idx].strip()
            value = line[colon_idx + 1:].strip()

            # Clean up OCR artifacts
            label = re.sub(r"[^a-zA-Z0-9\s/\(\)\.\-']", "", label).strip()
            value = re.sub(r"\s+", " ", value).strip()

            if label and len(label) > 1:
                pairs[label] = value

        return pairs

    def _scroll_pane(self, direction: str = "down"):
        """Scroll the source region pane up or down."""
        if not self.source_region:
            return
        x, y, w, h = self.source_region
        cx, cy = x + w // 2, y + h // 2
        # Move mouse to pane center
        pyautogui.moveTo(cx, cy, duration=0.05)
        if direction == "top":
            # Scroll all the way up (large number for Windows)
            pyautogui.scroll(3000)
        else:
            # Scroll down one screen
            pyautogui.scroll(-500)

    # ─── Form Filling ─────────────────────────────────────────────────────────

    def _fill_form(self, record: dict) -> bool:
        """
        Fill all MPF form fields by tabbing through in order.
        Clicks the first field to focus, then Tabs through all.
        """
        try:
            time.sleep(0.5)

            for field_key, label, field_type in MPF_FIELD_ORDER:
                if not self._running:
                    return False
                while self._pause:
                    time.sleep(0.3)

                value = self._get_field_value(record, field_key, field_type)

                if value:
                    self.log(f"   ✏️  {label}: {value}")
                else:
                    self.log(f"   ⬜ {label}: (empty — skipping)")

                self._fill_field(value, field_type)
                time.sleep(self.field_delay)
                
                # Human-like pane scrolling after major sections!
                if field_key == "house_type":
                    self._human_scroll_right_pane()
                elif field_key == "weight":
                    self._human_scroll_right_pane()

            # End-of-form sequence
            time.sleep(0.3)
            self._submit_form()
            return True

        except Exception as e:
            self.log(f"❌ Form fill error: {e}")
            logger.exception("Form fill error")
            return False

    def _fill_field(self, value: str, field_type: str):
        """Fill the currently focused form field."""
        if not value:
            pyautogui.press("tab")
            return

        if field_type == "dropdown":
            self._fill_dropdown(value)
        elif field_type == "date":
            self._fill_date(value)
        elif field_type == "skip":
            pass  # Don't Tab — just skip
        else:
            self._fill_text(value)

        pyautogui.press("tab")
        time.sleep(0.08)

    def _fill_text(self, value: str):
        """Clear field and type text via clipboard (fast & accurate)."""
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.04)
        pyautogui.press("delete")
        time.sleep(0.04)
        self._type(value)

    def _fill_dropdown(self, value: str):
        """Open dropdown, type to filter, then select with Enter."""
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.04)
        pyautogui.press("delete")
        time.sleep(0.06)
        self._type(value)
        time.sleep(0.2)
        pyautogui.press("down")
        time.sleep(0.08)
        pyautogui.press("enter")
        time.sleep(0.1)

    def _fill_date(self, value: str):
        """Fill a date field (DD Month YYYY or DD-MM-YYYY)."""
        # Normalize date format if needed
        value = self._normalize_date(value)
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.04)
        pyautogui.press("delete")
        time.sleep(0.04)
        # Type char by char with small delay for date spinners
        for ch in str(value):
            pyautogui.typewrite(ch, interval=0.05)
            time.sleep(0.02)

    def _normalize_date(self, val: str) -> str:
        """Try to convert '30 January 1991' → '30-01-1991' or keep as-is."""
        months = {
            "january": "01", "february": "02", "march": "03",
            "april": "04", "may": "05", "june": "06",
            "july": "07", "august": "08", "september": "09",
            "october": "10", "november": "11", "december": "12"
        }
        v = val.strip()
        for name, num in months.items():
            if name in v.lower():
                v = re.sub(name, num, v, flags=re.IGNORECASE)
        # Remove extra spaces
        v = re.sub(r"\s+", "-", v.strip())
        return v

    def _focus_mpf_window(self):
        """Bring the MRJ MPF application to the foreground for full control."""
        try:
            import win32gui
            import win32con

            def callback(hwnd, extra):
                if win32gui.IsWindowVisible(hwnd) and "Form Filling Software" in win32gui.GetWindowText(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    win32gui.SetForegroundWindow(hwnd)
                    return False
                return True
            try:
                win32gui.EnumWindows(callback, None)
            except Exception:
                pass
        except ImportError:
            pass

    def _human_scroll_right_pane(self):
        """Move mouse to the right form pane and scroll it down to reveal lower fields."""
        import pyautogui
        sw, sh = pyautogui.size()
        cx = int(sw * 0.75)
        cy = int(sh * 0.5)
        self.log("   🖱️  Scrolling right panel down...")
        pyautogui.moveTo(cx, cy, duration=0.1)
        pyautogui.scroll(-600)  # Scroll down the form
        time.sleep(0.3)

    def _find_and_click_first_field(self):
        """Use OCR to find the 'App No' label on the right side and click the input next to it."""
        try:
            import pytesseract
            from pytesseract import Output
            import pyautogui
            
            sw, sh = pyautogui.size()
            # Capture roughly the top-right quadrant where 'App No' resides
            r_x = int(sw * 0.45)
            r_y = 0
            r_w = int(sw * 0.55)
            r_h = int(sh * 0.50)
            img = vision.capture_screen((r_x, r_y, r_w, r_h))
            
            # Using pytesseract image_to_data for bounding boxes
            data = pytesseract.image_to_data(img, output_type=Output.DICT)
            for i in range(len(data['text'])):
                txt = data['text'][i].lower()
                next_txt = data['text'][i+1].lower() if i + 1 < len(data['text']) else ""
                
                if txt == 'app' and 'no' in next_txt:
                    x = r_x + data['left'][i]
                    y = r_y + data['top'][i]
                    h = data['height'][i]
                    
                    # Click approx 160px to the right of 'App' to hit the text box
                    target_x = x + 160
                    target_y = y + (h // 2)
                    
                    self.log(f"   🎯 AI Target Locked: 'App No' found. Clicking ({target_x}, {target_y})")
                    pyautogui.click(target_x, target_y)
                    time.sleep(0.4)
                    return True
            
            # Fallback if OCR fails to read it exactly
            click_x, click_y = int(sw * 0.65), int(sh * 0.25)
            self.log(f"   ⚠️ 'App No' label not identified, using AI fallback click ({click_x}, {click_y})")
            pyautogui.click(click_x, click_y)
            time.sleep(0.4)
        except Exception as e:
            self.log(f"   ❌ Vision targeting error: {e}")

    def _type(self, text: str):
        """Type out text character-by-character like a human, avoiding instant pasting."""
        # Calculate typing speed based on the slider (0.01 to 0.08 interval)
        interval = max(0.01, 0.05 / max(self.fill_speed, 0.1))
        # Type the text naturally
        pyautogui.typewrite(str(text), interval=interval)

    def _submit_form(self):
        """Execute the end-of-form sequence (Upload Details → Screenshot → Next)."""
        seq = self.end_sequence
        if not seq or not seq.get("upload"):
            self.log("   🖱️  Submitting (fallback Enter)...")
            pyautogui.press("enter")
            time.sleep(0.5)
            return

        self.log("   🖱️  Executing end-of-form sequence...")

        u_pos = seq.get("upload")
        if u_pos:
            self.log("     👉 Upload Details...")
            pyautogui.moveTo(u_pos[0], u_pos[1], duration=0.2)
            pyautogui.click()
            delay = seq.get("upload_delay", 5)
            self.log(f"     ⏳ Waiting {delay}s for upload...")
            time.sleep(delay)

        s_pos = seq.get("screenshot")
        if s_pos:
            self.log("     📸 Taking Screenshot...")
            pyautogui.moveTo(s_pos[0], s_pos[1], duration=0.2)
            pyautogui.click()
            delay = seq.get("screenshot_delay", 1)
            time.sleep(delay)

        n_pos = seq.get("next")
        if n_pos:
            self.log("     🔄 Loading Next Form...")
            pyautogui.moveTo(n_pos[0], n_pos[1], duration=0.2)
            pyautogui.click()
            time.sleep(1.0)

    def _wait_for_next_form(self):
        """Wait for the next form to be ready."""
        if self.use_visual_sync:
            self.status("⏳ Waiting for form to load (Vision Sync)...")
            time.sleep(1.0)
            vision.wait_for_mpf_form()
        else:
            self.log(f"⏳ Waiting {self.form_delay}s...")
            time.sleep(self.form_delay)

    # ─── Data Mapping ─────────────────────────────────────────────────────────

    def _get_field_value(self, record: dict, field_key: str, field_type: str) -> str:
        """Get value from record, normalize dropdowns."""
        value = str(record.get(field_key, "")).strip()

        if field_type == "dropdown" and value:
            if field_key == "gender":
                value = GENDER_MAP.get(value.lower(), value)
            elif field_key == "marital_status":
                value = MARITAL_MAP.get(value.lower(), value)

        return value

    # ─── CSV/JSON Loading ─────────────────────────────────────────────────────

    def _load_data(self) -> list[dict]:
        if not self.data_file or not os.path.exists(self.data_file):
            self.log(f"⚠️ Data file not found: {self.data_file}")
            return []

        ext = Path(self.data_file).suffix.lower()
        raw_records = []

        try:
            if ext == ".csv":
                with open(self.data_file, "r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    raw_records = list(reader)
            elif ext == ".json":
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    raw_records = data if isinstance(data, list) else [data]
            else:
                self.log(f"❌ Unsupported type: {ext}")
                return []
        except Exception as e:
            self.log(f"❌ Failed to read file: {e}")
            return []

        # Normalize column headers via aliases
        normalized = []
        for row in raw_records:
            norm_row = {}
            for col, val in row.items():
                if not col:
                    continue
                alias = COLUMN_ALIASES.get(col.lower().strip(), col.lower().strip())
                norm_row[alias] = val
            normalized.append(norm_row)

        self.log(f"✅ Loaded {len(normalized)} records")
        return normalized

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def log(self, msg: str):
        logger.info(msg)
        self.log_cb(msg)

    def status(self, msg: str):
        self.status_cb(msg)


# ─── Sample CSV Generator ─────────────────────────────────────────────────────

def create_sample_csv(path: str = "sample_mpf_data.csv"):
    """Create a sample CSV with real MPF field headers."""
    headers = [
        "app_no", "mbi_code", "full_name", "gender", "dob",
        "marital_status", "state", "district", "taluk", "pincode",
        "house_type", "rai_code", "mother_tongue", "religion",
        "cast", "sub_cast", "nakshatra", "rashi", "pada",
        "phi_code", "health_info", "any_disability", "diet",
        "height", "weight", "fai_code", "father_status",
        "father_name", "mother_status", "mother_name",
        "sister", "brother", "children_boy", "children_girl",
        "eci_code", "education", "emp_status", "annual_income",
    ]
    sample_rows = [
        {
            "app_no": "31760240",
            "mbi_code": "MBI1033189930",
            "full_name": "VIKASH RANJAN",
            "gender": "Male",
            "dob": "30-01-1991",
            "marital_status": "Never Married",
            "state": "Bihar",
            "district": "Rohtas",
            "taluk": "KARGHAR",
            "pincode": "821107",
            "house_type": "Own",
            "rai_code": "RAI1114399407",
            "mother_tongue": "Hindi",
            "religion": "Hindu",
            "cast": "Barhai",
            "sub_cast": "Sharma",
            "nakshatra": "Dhanishta / Avittam",
            "rashi": "Makara / Capricorn",
            "pada": "2nd Pada",
            "phi_code": "PHI1686515471",
            "health_info": "No Health Problems",
            "any_disability": "None",
            "diet": "Non-Veg",
            "height": "4.08 / 56 in / 142.2 cm",
            "weight": "90 Kgs",
            "fai_code": "FAI1686515471",
            "father_status": "Passed Away",
            "father_name": "RAMKESHWAR RAM",
            "mother_status": "Alive",
            "mother_name": "LAKSHMINA DEVI",
            "sister": "No Sister",
            "brother": "1 Brother",
            "children_boy": "Not Applicable",
            "children_girl": "Not Applicable",
            "eci_code": "ECI5022195898",
            "education": "B.M",
            "emp_status": "Government / Public Sector",
            "annual_income": "4 Lakh to 7 Lakh Annually",
        }
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(sample_rows)

    print(f"✅ Sample CSV created: {path}")
    return path
