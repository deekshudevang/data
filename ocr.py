"""
ocr.py — OCR Text Extraction Module
Uses Tesseract + OpenCV for robust text and label-value extraction from screen captures.
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image
import re
import logging
import os

logger = logging.getLogger("OCR")

# --- Tesseract path: search common locations ---
_TESS_CANDIDATES = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Users\deeks\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
]
TESSERACT_CMD = next((p for p in _TESS_CANDIDATES if os.path.exists(p)), "tesseract")
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
logger.info(f"Tesseract path: {TESSERACT_CMD}")


def preprocess_image(img: np.ndarray) -> np.ndarray:
    """Preprocess image for optimal OCR accuracy."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Upscale for better OCR
    scale = 2.0
    gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    # Adaptive threshold
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    # Denoise
    denoised = cv2.fastNlMeansDenoising(thresh, h=10)
    return denoised


def extract_text_blocks(img: np.ndarray, lang: str = "eng") -> list[dict]:
    """
    Extract all text blocks with bounding boxes using Tesseract.
    Returns list of {text, x, y, w, h, conf}.
    """
    processed = preprocess_image(img)
    pil_img = Image.fromarray(processed)

    data = pytesseract.image_to_data(
        pil_img, lang=lang,
        output_type=pytesseract.Output.DICT,
        config="--psm 6"
    )

    blocks = []
    n = len(data["text"])
    for i in range(n):
        text = data["text"][i].strip()
        conf = int(data["conf"][i])
        if text and conf > 30:
            blocks.append({
                "text": text,
                "x": data["left"][i],
                "y": data["top"][i],
                "w": data["width"][i],
                "h": data["height"][i],
                "conf": conf
            })
    return blocks


def extract_full_text(img: np.ndarray, lang: str = "eng") -> str:
    """Extract full raw text from image."""
    processed = preprocess_image(img)
    pil_img = Image.fromarray(processed)
    return pytesseract.image_to_string(pil_img, lang=lang, config="--psm 6")


def parse_label_value_pairs(text: str) -> list[dict]:
    """
    Parse raw OCR text into label-value pairs.
    Handles patterns like:
      - 'Label: Value'
      - 'Label    Value' (tab/space separated)
      - 'Label\nValue' (next-line value)
    """
    pairs = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    colon_pattern = re.compile(r"^(.+?)\s*:\s*(.*)$")

    i = 0
    while i < len(lines):
        line = lines[i]
        m = colon_pattern.match(line)
        if m:
            label = m.group(1).strip()
            value = m.group(2).strip()
            # If value is empty, look at next line
            if not value and i + 1 < len(lines):
                next_line = lines[i + 1]
                if not colon_pattern.match(next_line):
                    value = next_line
                    i += 1
            pairs.append({"label": label, "value": value})
        else:
            # Tab/space split
            parts = re.split(r"\s{2,}|\t", line)
            if len(parts) == 2:
                pairs.append({"label": parts[0].strip(), "value": parts[1].strip()})
        i += 1

    logger.info(f"Parsed {len(pairs)} label-value pairs from OCR text")
    return pairs


def extract_from_region(img: np.ndarray, x: int, y: int, w: int, h: int,
                         lang: str = "eng") -> str:
    """Extract text from a specific region of the image."""
    region = img[y:y+h, x:x+w]
    return extract_full_text(region, lang)
