"""
vision.py — Computer Vision UI Field Detection Module
Uses OpenCV to detect interactive form fields (input boxes, dropdowns, checkboxes)
without relying on fixed coordinates.
"""

import cv2
import numpy as np
import logging
from typing import Optional
import pyautogui
import time

logger = logging.getLogger("Vision")


# ─── Screen Capture ────────────────────────────────────────────────────────────

def capture_screen(region: Optional[tuple] = None) -> np.ndarray:
    """
    Capture full screen or a specific region.
    region: (x, y, width, height) or None for full screen.
    Returns BGR numpy array.
    """
    screenshot = pyautogui.screenshot(region=region)
    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)


def capture_window(window_title: str) -> Optional[np.ndarray]:
    """Try to bring window to foreground and capture it."""
    try:
        import pygetwindow as gw
        wins = gw.getWindowsWithTitle(window_title)
        if wins:
            win = wins[0]
            win.activate()
            time.sleep(0.3)
            region = (win.left, win.top, win.width, win.height)
            return capture_screen(region)
    except Exception as e:
        logger.warning(f"Window capture failed: {e}")
    return capture_screen()


# ─── Field Detection ────────────────────────────────────────────────────────────

def detect_input_fields(img: np.ndarray) -> list[dict]:
    """
    Detect input text fields in the image using contour analysis.
    Returns list of {x, y, w, h, type, center_x, center_y}.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blurred, 50, 150)

    # Dilate to close gaps in field borders
    kernel = np.ones((2, 5), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    fields = []
    img_h, img_w = img.shape[:2]

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        aspect = w / h if h > 0 else 0

        # Filter: input fields are typically wide rectangles
        if (20 < w < img_w * 0.8) and (10 < h < 60) and (2.5 < aspect < 30):
            field_type = _classify_field(img, x, y, w, h)
            fields.append({
                "x": x, "y": y, "w": w, "h": h,
                "type": field_type,
                "center_x": x + w // 2,
                "center_y": y + h // 2
            })

    # Remove duplicate/overlapping fields
    fields = _deduplicate_fields(fields)
    logger.info(f"Detected {len(fields)} input fields")
    return fields


def _classify_field(img: np.ndarray, x: int, y: int, w: int, h: int) -> str:
    """Classify a detected field as text_input, dropdown, checkbox, or radio."""
    region = img[y:y+h, x:x+w]
    gray_region = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    mean_val = np.mean(gray_region)

    # Very small square-ish regions → checkbox or radio
    if w < 30 and h < 30 and abs(w - h) < 10:
        return "checkbox"

    # Check for dropdown arrow (dark triangle on right side)
    right_strip = region[:, -20:] if w > 30 else region
    right_gray = cv2.cvtColor(right_strip, cv2.COLOR_BGR2GRAY)
    _, right_thresh = cv2.threshold(right_gray, 100, 255, cv2.THRESH_BINARY_INV)
    if np.sum(right_thresh) > 500:
        return "dropdown"

    # Light interior → likely an input field
    if mean_val > 200:
        return "text_input"

    return "text_input"


def _deduplicate_fields(fields: list[dict], iou_threshold: float = 0.3) -> list[dict]:
    """Remove overlapping duplicate detections."""
    if not fields:
        return []
    fields = sorted(fields, key=lambda f: f["w"] * f["h"], reverse=True)
    kept = []
    for f in fields:
        overlaps = False
        for k in kept:
            if _iou(f, k) > iou_threshold:
                overlaps = True
                break
        if not overlaps:
            kept.append(f)
    return kept


def _iou(a: dict, b: dict) -> float:
    """Intersection over Union for two bounding boxes."""
    ax1, ay1, ax2, ay2 = a["x"], a["y"], a["x"] + a["w"], a["y"] + a["h"]
    bx1, by1, bx2, by2 = b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"]
    inter_x = max(0, min(ax2, bx2) - max(ax1, bx1))
    inter_y = max(0, min(ay2, by2) - max(ay1, by1))
    inter = inter_x * inter_y
    union = (a["w"] * a["h"]) + (b["w"] * b["h"]) - inter
    return inter / union if union > 0 else 0


# ─── Label-Field Association ────────────────────────────────────────────────────

def associate_labels_to_fields(labels: list[dict], fields: list[dict]) -> list[dict]:
    """
    Associate OCR text labels to nearby detected fields.
    Each label block: {text, x, y, w, h}
    Each field: {x, y, w, h, type, center_x, center_y}
    Returns list of {label, field, distance}.
    """
    associations = []
    for field in fields:
        best_label = None
        best_dist = float("inf")

        fx, fy = field["center_x"], field["center_y"]

        for lbl in labels:
            lx = lbl["x"] + lbl["w"] // 2
            ly = lbl["y"] + lbl["h"] // 2

            # Labels are usually to the left or above the field
            dx = fx - lx
            dy = fy - ly

            # Prefer labels to the left within same row
            if -20 < dy < field["h"] * 2 and 0 < dx < 400:
                dist = dx + abs(dy) * 2
                if dist < best_dist:
                    best_dist = dist
                    best_label = lbl["text"]

        if best_label:
            associations.append({
                "label": best_label,
                "field": field,
                "distance": best_dist
            })

    logger.info(f"Associated {len(associations)} label-field pairs")
    return associations


def is_mpf_loading(img: np.ndarray) -> bool:
    """
    Detect if the 'Downloading Form' loading screen is visible in the MPF software.
    Uses contour analysis to find the distinct central modal box.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Threshold to find white backgrounds / blue borders
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    img_h, img_w = img.shape[:2]
    cx, cy = img_w // 2, img_h // 2

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # The loading modal is usually central and has specific dimensions
        # approx 400x120 on 1080p, so we'll be flexible
        if (300 < w < 800) and (100 < h < 300):
            # Check if it's near center
            if abs(x + w//2 - cx) < 200 and abs(y + h//2 - cy) < 200:
                # Crop and check for the blue/green header or MRJ text area
                header = img[y:y+30, x:x+w]
                h_gray = cv2.cvtColor(header, cv2.COLOR_BGR2GRAY)
                # Check for dark header (typical for these old-style Win32 apps)
                if np.mean(h_gray) < 150: 
                    return True
    return False


def wait_for_mpf_form(timeout: int = 45, interval: float = 0.5) -> bool:
    """
    Monitors screen for the MPF loading modal.
    Returns True when the modal was detected AND then disappeared (form ready).
    Returns False if timeout reached.
    """
    start_time = time.time()
    detected_loading = False
    
    logger.info("⏳ Visual Sync: Waiting for MPF form...")
    
    while time.time() - start_time < timeout:
        img = capture_screen()
        is_loading = is_mpf_loading(img)
        
        if is_loading:
            if not detected_loading:
                logger.info("📡 MPF Loading detected — waiting for completion...")
                detected_loading = True
        else:
            if detected_loading:
                logger.info("✅ MPF Form ready! (Loading screen disappeared)")
                return True
            # If after 5s we haven't even seen a loading screen,
            # it might have loaded instantly or already be showing the form.
            if time.time() - start_time > 5:
                return True
                
        time.sleep(interval)
        
    logger.warning("⚠️ Visual Sync: Timed out waiting for MPF form")
    return False


def highlight_fields(img: np.ndarray, fields: list[dict]) -> np.ndarray:
    """Draw bounding boxes on detected fields for debug visualization."""
    vis = img.copy()
    colors = {"text_input": (0, 255, 0), "dropdown": (255, 165, 0),
              "checkbox": (0, 0, 255), "radio": (255, 0, 255)}
    for f in fields:
        color = colors.get(f["type"], (0, 255, 0))
        cv2.rectangle(vis, (f["x"], f["y"]), (f["x"] + f["w"], f["y"] + f["h"]), color, 2)
        cv2.putText(vis, f["type"], (f["x"], f["y"] - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    return vis
