"""
mpf_bot.py — MRJ MPF Form Filling Software Dedicated Automation Engine
Specifically crafted for MPF Form Filling Software v7.3
Handles all 18 fields, Tab-based navigation, dropdowns, and Submit button.
"""

import time
import logging
import csv
import json
import os
import threading
from pathlib import Path
from typing import Callable

import pyautogui
import pyperclip

import vision

logger = logging.getLogger("MPF_Bot")

# ─── MPF Field Tab Order (exact order as in the form) ─────────────────────────
# Each entry: (field_key, label, field_type)
# field_type: "text" | "dropdown" | "date"

MPF_FIELD_ORDER = [
    ("name",            "Name",                 "text"),
    ("fathers_name",    "Father's Name",        "text"),
    ("mobile",          "Mobile Number",        "text"),
    ("email",           "Email Id",             "text"),
    ("dob",             "Date of Birth",        "date"),
    ("gender",           "Gender",              "dropdown"),
    ("address",         "Address",              "text"),
    ("landmark",        "Landmark",             "text"),
    ("area",            "Area",                 "text"),
    ("city",            "City",                 "text"),
    ("state",           "State",                "text"),
    ("pincode",         "Pincode",              "text"),
    ("occupation",      "Occupation",           "text"),
    ("income",          "Income (Per Annum)",   "text"),
    ("marital_status",  "Marital Status",       "dropdown"),
    ("nationality",     "Nationality",          "text"),
    ("identity_proof",  "Identity Proof",       "dropdown"),
    ("id_number",       "ID Number",            "text"),
]

# Map common source column names → MPF field keys
COLUMN_ALIASES = {
    # Name
    "name": "name", "full name": "name", "applicant name": "name",
    "customer name": "name",
    # Father
    "father": "fathers_name", "father's name": "fathers_name",
    "fathers name": "fathers_name", "father name": "fathers_name",
    # Mobile
    "mobile": "mobile", "phone": "mobile", "mobile number": "mobile",
    "contact": "mobile", "phone number": "mobile",
    # Email
    "email": "email", "email id": "email", "e-mail": "email",
    # DOB
    "dob": "dob", "date of birth": "dob", "birth date": "dob",
    "birthday": "dob", "d.o.b": "dob",
    # Gender
    "gender": "gender", "sex": "gender",
    # Address
    "address": "address", "street": "address", "residence": "address",
    # Landmark
    "landmark": "landmark", "near": "landmark",
    # Area
    "area": "area", "locality": "area", "colony": "area",
    # City
    "city": "city", "town": "city", "district": "city",
    # State
    "state": "state", "province": "state",
    # Pincode
    "pincode": "pincode", "pin": "pincode", "pin code": "pincode",
    "zip": "pincode", "postal code": "pincode", "zipcode": "pincode",
    # Occupation
    "occupation": "occupation", "job": "occupation", "profession": "occupation",
    "work": "occupation",
    # Income
    "income": "income", "salary": "income", "income per annum": "income",
    "annual income": "income", "ctc": "income",
    # Marital Status
    "marital status": "marital_status", "marital": "marital_status",
    "marriage status": "marital_status",
    # Nationality
    "nationality": "nationality", "citizen": "nationality",
    # Identity Proof
    "identity proof": "identity_proof", "id proof": "identity_proof",
    "id type": "identity_proof", "document": "identity_proof",
    # ID Number
    "id number": "id_number", "aadhar": "id_number", "pan": "id_number",
    "document number": "id_number", "id no": "id_number",
}

# Dropdown value normalizers
GENDER_VALUES     = {"m": "MALE", "male": "MALE", "f": "FEMALE", "female": "FEMALE"}
MARITAL_VALUES    = {"married": "MARRIED", "single": "SINGLE", "unmarried": "SINGLE",
                     "divorced": "DIVORCED", "widowed": "WIDOWED"}
ID_PROOF_VALUES   = {
    "aadhar": "AADHAR CARD", "aadhaar": "AADHAR CARD", "aadhar card": "AADHAR CARD",
    "pan": "PAN CARD", "pan card": "PAN CARD",
    "voter": "VOTER ID", "voter id": "VOTER ID",
    "passport": "PASSPORT",
    "driving": "DRIVING LICENSE", "dl": "DRIVING LICENSE",
}


class MPFBot:
    """
    Dedicated automation bot for MRJ MPF Form Filling Software v7.3.
    Navigates through fields using Tab key (fastest method for this app),
    handles dropdowns, and submits each form entry.
    """

    def __init__(
        self,
        data_file: str = "",
        log_cb: Callable[[str], None] | None = None,
        status_cb: Callable[[str], None] | None = None,
        record_done_cb: Callable[[int, int], None] | None = None,   # (done, total)
        stopped_cb: Callable[[], None] | None = None,
        fill_speed: float = 1.0,
        delay_between_fields: float = 0.25,
        delay_between_forms: float = 2.0,
        use_visual_sync: bool = True,
        end_sequence: dict | None = None,
    ):
        self.data_file = data_file
        self.log_cb = log_cb or (lambda m: print(m))
        self.status_cb = status_cb or (lambda s: None)
        self.record_done_cb = record_done_cb or (lambda d, t: None)
        self.stopped_cb = stopped_cb or (lambda: None)

        self.fill_speed = fill_speed
        self.field_delay = delay_between_fields / fill_speed
        self.form_delay = delay_between_forms
        self.use_visual_sync = use_visual_sync
        self.end_sequence = end_sequence or {}

        self._running = False
        self._pause = False
        self._thread: threading.Thread | None = None

    # ─── Control ─────────────────────────────────────────────────────────────

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
            records = self._load_data()
            if not records:
                self.log("❌ No data loaded. Please check your CSV/JSON data file.")
                self._running = False
                self.stopped_cb()
                return

            total = len(records)
            self.log(f"📋 Loaded {total} records from data file")
            self.status(f"Starting automation — {total} records to fill")

            # Countdown so user can switch to MPF window
            for i in range(5, 0, -1):
                if not self._running:
                    return
                self.status(f"⏳ Starting in {i}s — switch to MPF window NOW!")
                time.sleep(1)

            for idx, record in enumerate(records, start=1):
                if not self._running:
                    break
                while self._pause:
                    time.sleep(0.3)

                self.log(f"\n━━━ Record {idx}/{total} ━━━")
                self.status(f"📝 Filling record {idx}/{total}...")

                success = self._fill_form(record)

                if success:
                    self.record_done_cb(idx, total)
                    self.log(f"✅ Record {idx} submitted successfully")
                else:
                    self.log(f"⚠️ Record {idx} — some fields may have issues")

                if idx < total:
                    if self.use_visual_sync:
                        self.status("⏳ Waiting for MPF form ready state (Visual Sync)...")
                        # First, small buffer for the 'Downloading' modal to move into view/appear
                        time.sleep(1.0)
                        vision.wait_for_mpf_form()
                    else:
                        self.log(f"⏳ Waiting {self.form_delay}s for next form to load...")
                        time.sleep(self.form_delay)

            self.log(f"\n🎉 All {total} records processed!")
            self.status(f"✅ Complete — {total} records filled")

        except Exception as e:
            self.log(f"❌ Critical error: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            self._running = False
            self.stopped_cb()

    # ─── Form Filling ─────────────────────────────────────────────────────────

    def _fill_form(self, record: dict) -> bool:
        """
        Fill all fields in one MPF form entry using Tab navigation.
        The MPF app uses Tab to move between fields — fastest and most reliable.
        """
        try:
            # Click on the first field (Name field) to start
            # We use keyboard shortcut first, then Tab through fields
            time.sleep(0.5)

            for field_key, label, field_type in MPF_FIELD_ORDER:
                if not self._running:
                    return False
                while self._pause:
                    time.sleep(0.3)

                value = self._get_field_value(record, field_key, field_type)
                self.log(f"   ✏️ {label}: {value}")

                self._fill_field(value, field_type)
                time.sleep(self.field_delay)

            # Submit the form
            time.sleep(0.3)
            self._submit_form()
            return True

        except Exception as e:
            self.log(f"❌ Error filling form: {e}")
            return False

    def _fill_field(self, value: str, field_type: str):
        """Fill the currently active/focused field."""
        if not value:
            # Empty field — just Tab to next
            pyautogui.press("tab")
            return

        if field_type == "dropdown":
            self._fill_dropdown(value)
        elif field_type == "date":
            self._fill_date(value)
        else:
            self._fill_text(value)

        # Move to next field
        pyautogui.press("tab")
        time.sleep(0.08)

    def _fill_text(self, value: str):
        """Clear current field and type text."""
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.05)
        pyautogui.press("delete")
        time.sleep(0.05)
        self._type(value)

    def _fill_dropdown(self, value: str):
        """Handle dropdown: clear then type to filter, then select."""
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.05)
        pyautogui.press("delete")
        time.sleep(0.08)
        self._type(value)
        time.sleep(0.15)
        # Try to select the first matching option
        pyautogui.press("down")
        time.sleep(0.1)
        pyautogui.press("enter")
        time.sleep(0.1)

    def _fill_date(self, value: str):
        """Fill a date field."""
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.05)
        pyautogui.press("delete")
        time.sleep(0.05)
        # Type date character by character with small delays
        for ch in value:
            pyautogui.typewrite(ch, interval=0.04)
            time.sleep(0.02)

    def _type(self, text: str):
        """Type text using clipboard paste for speed and accuracy."""
        try:
            pyperclip.copy(str(text))
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.08)
        except Exception:
            # Fallback to typewrite
            pyautogui.typewrite(str(text), interval=0.04 / self.fill_speed)

    def _submit_form(self):
        """Execute the end of form sequence based on custom coordinates or default behavior."""
        if not self.end_sequence or not self.end_sequence.get("upload"):
            self.log("   🖱️ Submitting form (Fallback Enter)...")
            pyautogui.press("enter")
            time.sleep(0.5)
            return

        self.log("   🖱️ Executing custom end-of-form sequence...")
        
        # 1. Upload Details
        u_pos = self.end_sequence.get("upload")
        if u_pos:
            self.log("     👉 Clicking 'Upload Details'...")
            pyautogui.moveTo(u_pos[0], u_pos[1], duration=0.2)
            pyautogui.click()
            delay = self.end_sequence.get("upload_delay", 5)
            self.log(f"     ⏳ Waiting {delay}s for network...")
            time.sleep(delay)
            
        # 2. Take Screenshot
        s_pos = self.end_sequence.get("screenshot")
        if s_pos:
            self.log("     📸 Clicking 'Take Screenshot'...")
            pyautogui.moveTo(s_pos[0], s_pos[1], duration=0.2)
            pyautogui.click()
            delay = self.end_sequence.get("screenshot_delay", 1)
            self.log(f"     ⏳ Waiting {delay}s...")
            time.sleep(delay)
            
        # 3. Load Another Form
        n_pos = self.end_sequence.get("next")
        if n_pos:
            self.log("     🔄 Clicking 'Load Another Form'...")
            pyautogui.moveTo(n_pos[0], n_pos[1], duration=0.2)
            pyautogui.click()
            time.sleep(1.0)

    # ─── Data Mapping ─────────────────────────────────────────────────────────

    def _get_field_value(self, record: dict, field_key: str, field_type: str) -> str:
        """Get the value for a field from the record, normalizing as needed."""
        value = record.get(field_key, "")

        # Normalize dropdown values
        if field_type == "dropdown":
            if field_key == "gender":
                value = GENDER_VALUES.get(value.lower().strip(), value.upper())
            elif field_key == "marital_status":
                value = MARITAL_VALUES.get(value.lower().strip(), value.upper())
            elif field_key == "identity_proof":
                value = ID_PROOF_VALUES.get(value.lower().strip(), value.upper())

        return str(value).strip() if value else ""

    # ─── Data Loading ─────────────────────────────────────────────────────────

    def _load_data(self) -> list[dict]:
        """Load records from CSV or JSON file, mapping columns to MPF field keys."""
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
                self.log(f"❌ Unsupported file type: {ext}. Use .csv or .json")
                return []
        except Exception as e:
            self.log(f"❌ Failed to read data file: {e}")
            return []

        # Normalize column names → MPF field keys
        normalized = []
        for row in raw_records:
            norm_row = {}
            for col, val in row.items():
                alias = COLUMN_ALIASES.get(col.lower().strip(), col.lower().strip())
                norm_row[alias] = val
            normalized.append(norm_row)

        self.log(f"✅ Loaded {len(normalized)} records")
        return normalized

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def log(self, msg: str):
        logger.info(msg)
        self.log_cb(msg)

    def status(self, msg: str):
        self.status_cb(msg)


# ─── Sample Data Generator ────────────────────────────────────────────────────

def create_sample_csv(path: str = "sample_data.csv"):
    """Create a sample CSV file with MPF-compatible field headers."""
    import csv
    headers = [
        "name", "fathers_name", "mobile", "email", "dob",
        "gender", "address", "landmark", "area", "city",
        "state", "pincode", "occupation", "income",
        "marital_status", "nationality", "identity_proof", "id_number"
    ]
    sample_rows = [
        {
            "name": "REKHA RANI",
            "fathers_name": "RAMESH CHAND",
            "mobile": "9876543210",
            "email": "rekha@gmail.com",
            "dob": "10-05-1995",
            "gender": "FEMALE",
            "address": "H.NO 123, SECTOR 4",
            "landmark": "NEAR MARKET",
            "area": "GREEN PARK",
            "city": "CHANDIGARH",
            "state": "PUNJAB",
            "pincode": "140301",
            "occupation": "HOUSEWIFE",
            "income": "NIL",
            "marital_status": "MARRIED",
            "nationality": "INDIAN",
            "identity_proof": "AADHAR CARD",
            "id_number": "1234 5678 1234"
        },
        {
            "name": "AMIT KUMAR",
            "fathers_name": "SURESH KUMAR",
            "mobile": "9988776655",
            "email": "amit.kumar@gmail.com",
            "dob": "15-08-1988",
            "gender": "MALE",
            "address": "FLAT 45, SECTOR 22",
            "landmark": "OPP SCHOOL",
            "area": "SECTOR 22",
            "city": "LUDHIANA",
            "state": "PUNJAB",
            "pincode": "141001",
            "occupation": "BUSINESSMAN",
            "income": "350000",
            "marital_status": "MARRIED",
            "nationality": "INDIAN",
            "identity_proof": "PAN CARD",
            "id_number": "ABCDE1234F"
        },
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(sample_rows)

    print(f"✅ Sample CSV created: {path}")
    return path
