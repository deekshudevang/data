"""
bot_engine.py — Main Automation Orchestration Engine
Coordinates: Screen Capture → OCR → Field Detection → Matching → Filling → Learning
Runs in a background thread; communicates with UI via Qt signals.
"""

import time
import logging
import traceback
from typing import Callable

import cv2

import ocr
import vision
import mapping
import actions
import learning

logger = logging.getLogger("BotEngine")


class AutomationEngine:
    """
    Core automation engine that orchestrates the full data-entry pipeline.

    Signals (callbacks):
        log_callback(str)              — emit a log message
        status_callback(str)           — emit a status/state message
        field_filled_callback(dict)    — emitted when a field is filled
        stopped_callback()             — emitted when automation stops
    """

    def __init__(
        self,
        log_cb: Callable[[str], None] | None = None,
        status_cb: Callable[[str], None] | None = None,
        field_filled_cb: Callable[[dict], None] | None = None,
        stopped_cb: Callable[[], None] | None = None,
    ):
        self.log_cb = log_cb or (lambda m: logger.info(m))
        self.status_cb = status_cb or (lambda s: None)
        self.field_filled_cb = field_filled_cb or (lambda d: None)
        self.stopped_cb = stopped_cb or (lambda: None)

        self._running = False
        self._pause = False

        # Settings
        self.fill_speed: float = 1.0        # 0.5 = slow, 1.0 = normal, 2.0 = fast
        self.ocr_lang: str = "eng"
        self.confidence_threshold: float = 0.3
        self.continuous_mode: bool = False
        self.max_retries: int = 3

    # ─── Control ──────────────────────────────────────────────────────────────

    def start(self):
        """Start the automation loop."""
        self._running = True
        self._pause = False
        self._run_loop()

    def stop(self):
        """Signal the engine to stop."""
        self._running = False
        self.log("⏹ Automation stopped by user.")
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

    def _run_loop(self):
        """
        Main automation cycle:
        1. Capture screen
        2. Extract text via OCR
        3. Detect fields visually
        4. Match labels → fields
        5. Fill fields
        6. Log & learn
        """
        try:
            self.status("🔍 Detecting active window...")
            app_name = self._get_active_app_name()
            self.log(f"📌 Active App: {app_name}")

            iteration = 0
            while self._running:
                if self._pause:
                    time.sleep(0.2)
                    continue

                iteration += 1
                self.log(f"\n━━━ Iteration #{iteration} ━━━")

                success = self._run_cycle(app_name)

                if not self.continuous_mode or not success:
                    break

                self.log("🔄 Continuous mode: waiting for next page...")
                time.sleep(2.0)

                # Check if page changed
                new_app = self._get_active_app_name()
                if new_app != app_name:
                    app_name = new_app
                    self.log(f"📌 App changed to: {app_name}")

        except Exception as e:
            self.log(f"❌ Engine error: {e}")
            logger.error(traceback.format_exc())
        finally:
            self._running = False
            self.stopped_cb()

    def _run_cycle(self, app_name: str) -> bool:
        """Execute one full automation cycle. Returns True if fields were filled."""

        # ── Step 1: Screen Capture ─────────────────────────────────────────
        self.status("📷 Capturing screen...")
        self.log("📷 Capturing screen...")
        screen = vision.capture_screen()

        # ── Step 2: OCR ────────────────────────────────────────────────────
        self.status("🔤 Extracting text via OCR...")
        self.log("🔤 Running OCR...")
        raw_text = ocr.extract_full_text(screen, lang=self.ocr_lang)
        text_blocks = ocr.extract_text_blocks(screen, lang=self.ocr_lang)

        data_pairs = ocr.parse_label_value_pairs(raw_text)
        self.log(f"📋 Found {len(data_pairs)} label-value pairs")

        if not data_pairs:
            self.log("⚠️ No data pairs extracted. Is the source window visible?")
            return False

        for pair in data_pairs[:8]:  # Log first 8
            self.log(f"   • {pair['label']}: {pair['value']}")

        # ── Step 3: Field Detection ────────────────────────────────────────
        self.status("🔎 Detecting input fields...")
        self.log("🔎 Detecting form fields...")
        detected_fields = vision.detect_input_fields(screen)
        self.log(f"🧩 Detected {len(detected_fields)} input fields")

        if not detected_fields:
            self.log("⚠️ No input fields detected. Ensure the form is visible.")
            return False

        # ── Step 4: Associate Labels to Fields ─────────────────────────────
        label_blocks = [b for b in text_blocks if len(b["text"]) > 2]
        associations = vision.associate_labels_to_fields(label_blocks, detected_fields)
        self.log(f"🔗 Associated {len(associations)} label-field pairs")

        # ── Step 5: Semantic Matching ──────────────────────────────────────
        self.status("🤖 Matching fields with AI...")
        self.log("🤖 Running semantic field matching...")
        mem = learning.get_app_memory(app_name)
        # Convert memory to format expected by mapping module
        learned = {app_name: mem} if mem else None

        matched = mapping.match_labels_to_fields(
            data_pairs, associations, learned_mappings=learned, app_name=app_name
        )
        self.log(f"✅ Matched {len(matched)} fields")

        if not matched:
            self.log("⚠️ No fields matched. Will retry or try learning from scratch.")
            return False

        # ── Step 6: Fill Fields ────────────────────────────────────────────
        self.status("⌨️ Filling form fields...")
        screen_h = screen.shape[0]
        filled_count = 0

        for item in matched:
            if not self._running:
                break

            label = item["label"]
            value = item["value"]
            field = item["field"]
            confidence = item["confidence"]
            source = item["source"]

            conf_str = f"{confidence:.0%}"
            self.log(f"   ✏️ '{label}' → '{value}' [{conf_str} via {source}]")

            # Cautious mode for low confidence
            cautious = confidence < self.confidence_threshold

            retry_count = 0
            while retry_count <= self.max_retries:
                try:
                    # Scroll field into view if needed
                    vision.capture_screen()  # Re-check screen for scroll
                    actions.scroll_to_field(field["center_y"], screen_h)
                    time.sleep(0.1)

                    actions.smart_fill(field, value, speed=self.fill_speed)
                    filled_count += 1

                    # Notify UI
                    self.field_filled_cb({
                        "label": label, "value": value,
                        "confidence": confidence, "source": source
                    })

                    # Save successful mapping to memory
                    mapping_key = item.get("matched_label", label)
                    learning.save_mapping(app_name, label, mapping_key)
                    learning.record_use(app_name, label, success=True)
                    break

                except Exception as e:
                    retry_count += 1
                    self.log(f"   ⚠️ Retry {retry_count}/{self.max_retries} for '{label}': {e}")
                    time.sleep(0.5 * retry_count)
                    if retry_count > self.max_retries:
                        self.log(f"   ❌ Failed to fill '{label}' after retries")
                        learning.record_use(app_name, label, success=False)

            if not cautious:
                actions.press_tab()

            time.sleep(0.15 / self.fill_speed)

        self.log(f"\n🎉 Automation complete! Filled {filled_count}/{len(matched)} fields.")
        self.status(f"✅ Done — {filled_count} fields filled")
        return filled_count > 0

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _get_active_app_name(self) -> str:
        """Get the title of the currently active window."""
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            buf = ctypes.create_unicode_buffer(512)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, 512)
            title = buf.value.strip()
            if title:
                # Normalize: take first meaningful word for app identification
                return title.split(" - ")[-1].strip() or title
        except Exception:
            pass
        return "unknown_app"

    def log(self, msg: str):
        logger.info(msg)
        self.log_cb(msg)

    def status(self, msg: str):
        self.status_cb(msg)
