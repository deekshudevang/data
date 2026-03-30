"""
actions.py — Human-like Automation Actions Module
Wraps PyAutoGUI with human-like delays, typing speed variation,
dropdown handling, date pickers, scroll detection, and error recovery.
"""

import pyautogui
import time
import random
import logging
import string
import pyperclip

logger = logging.getLogger("Actions")

# Disable PyAutoGUI fail-safe at corners (for production use)
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05  # Base pause between actions


# ─── Timing Utilities ──────────────────────────────────────────────────────────

def human_delay(base: float = 0.3, variance: float = 0.15):
    """Sleep for a randomized human-like delay."""
    time.sleep(max(0.05, base + random.uniform(-variance, variance)))


def typing_delay() -> float:
    """Return a randomized per-character typing delay."""
    return random.uniform(0.02, 0.09)


# ─── Mouse Actions ─────────────────────────────────────────────────────────────

def move_to(x: int, y: int, smooth: bool = True):
    """Move mouse to position with optional smooth movement."""
    if smooth:
        duration = random.uniform(0.15, 0.4)
        pyautogui.moveTo(x, y, duration=duration, tween=pyautogui.easeInOutQuad)
    else:
        pyautogui.moveTo(x, y)
    human_delay(0.1, 0.05)


def click(x: int, y: int, button: str = "left", double: bool = False):
    """Click at given coordinates."""
    move_to(x, y)
    if double:
        pyautogui.doubleClick(x, y, button=button)
    else:
        pyautogui.click(x, y, button=button)
    human_delay(0.2, 0.1)


def right_click(x: int, y: int):
    """Right-click at position."""
    click(x, y, button="right")


# ─── Keyboard Actions ──────────────────────────────────────────────────────────

def clear_field():
    """Select all and delete contents of current field."""
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.1)
    pyautogui.press("delete")
    time.sleep(0.1)


def type_text(text: str, delay_override: float | None = None):
    """
    Type text in a human-like manner, character by character.
    Falls back to clipboard paste for special characters or long strings.
    """
    if not text:
        return

    # Use clipboard paste for long or complex text
    if len(text) > 30 or any(c not in string.printable for c in text):
        _paste_text(text)
        return

    for char in text:
        pyautogui.typewrite(char, interval=delay_override or typing_delay())

    logger.debug(f"Typed: {text[:20]}{'...' if len(text) > 20 else ''}")


def _paste_text(text: str):
    """Copy text to clipboard and paste it."""
    try:
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.2)
    except Exception as e:
        logger.warning(f"Clipboard paste failed: {e}, falling back to typewrite")
        pyautogui.typewrite(text, interval=0.05)


def press_key(key: str):
    """Press a single keyboard key."""
    pyautogui.press(key)
    human_delay(0.1, 0.05)


def hotkey(*keys):
    """Execute a keyboard shortcut."""
    pyautogui.hotkey(*keys)
    human_delay(0.15, 0.05)


# ─── Field Interaction ─────────────────────────────────────────────────────────

def fill_text_field(x: int, y: int, value: str, speed: float = 1.0):
    """
    Click a text field and type a value with human-like behavior.
    speed: 1.0 = normal, 0.5 = slower, 2.0 = faster
    """
    logger.info(f"Filling text field at ({x},{y}) with: {value[:30]}")
    click(x, y)
    human_delay(0.15 / speed)
    clear_field()
    human_delay(0.1 / speed)
    delay = (typing_delay() / speed)
    type_text(value, delay_override=delay)
    human_delay(0.2 / speed)


def fill_dropdown(x: int, y: int, value: str):
    """
    Handle dropdown selection:
    1. Click dropdown
    2. Type value (for searchable dropdowns)
    3. Try arrow keys + Enter to select
    """
    logger.info(f"Filling dropdown at ({x},{y}) with: {value}")
    click(x, y)
    human_delay(0.3)

    # Try typing the value (works for searchable dropdowns)
    clear_field()
    type_text(value)
    human_delay(0.4)

    # Try pressing Down + Enter to select the first result
    pyautogui.press("down")
    human_delay(0.1)
    pyautogui.press("enter")
    human_delay(0.2)


def fill_checkbox(x: int, y: int, should_check: bool = True):
    """Toggle checkbox to desired state."""
    logger.info(f"{'Checking' if should_check else 'Unchecking'} checkbox at ({x},{y})")
    # Note: We assume the checkbox is currently unchecked
    if should_check:
        click(x, y)
    human_delay(0.15)


def fill_date_field(x: int, y: int, date_value: str):
    """
    Fill a date input field.
    Handles common date formats (MM/DD/YYYY, YYYY-MM-DD, etc.)
    """
    logger.info(f"Filling date field at ({x},{y}) with: {date_value}")
    click(x, y)
    human_delay(0.2)
    clear_field()
    type_text(date_value)
    human_delay(0.2)
    pyautogui.press("tab")  # Confirm date entry


# ─── Scroll & Navigation ───────────────────────────────────────────────────────

def scroll_down(clicks: int = 3, x: int | None = None, y: int | None = None):
    """Scroll down on the current screen or at a specific position."""
    if x and y:
        pyautogui.moveTo(x, y)
    pyautogui.scroll(-clicks)
    human_delay(0.5, 0.2)


def scroll_up(clicks: int = 3, x: int | None = None, y: int | None = None):
    """Scroll up on the current screen or at a specific position."""
    if x and y:
        pyautogui.moveTo(x, y)
    pyautogui.scroll(clicks)
    human_delay(0.5, 0.2)


def scroll_to_field(field_y: int, screen_h: int, margin: int = 100):
    """Scroll until field is visible on screen."""
    if field_y > screen_h - margin:
        scroll_down(3)
        human_delay(0.4)
    elif field_y < margin:
        scroll_up(3)
        human_delay(0.4)


def press_tab():
    """Tab to next field."""
    pyautogui.press("tab")
    human_delay(0.2)


def press_enter():
    """Press Enter (form submit / confirm)."""
    pyautogui.press("enter")
    human_delay(0.3)


# ─── Smart Fill Dispatcher ────────────────────────────────────────────────────

def smart_fill(field: dict, value: str, speed: float = 1.0):
    """
    Dispatch to the correct fill function based on field type.
    field: {x, y, w, h, type, center_x, center_y}
    """
    cx, cy = field["center_x"], field["center_y"]
    field_type = field.get("type", "text_input")

    if field_type == "dropdown":
        fill_dropdown(cx, cy, value)
    elif field_type == "checkbox":
        checked = value.lower() in ("yes", "true", "1", "checked", "on")
        fill_checkbox(cx, cy, checked)
    elif field_type == "date":
        fill_date_field(cx, cy, value)
    else:
        fill_text_field(cx, cy, value, speed=speed)
