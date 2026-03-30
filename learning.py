"""
learning.py — Self-Learning AI Memory & Confidence Engine
Stores app-specific label→field mappings with confidence scores.
Learns from user corrections and improves over time.
"""

import json
import os
import time
import logging
from pathlib import Path

logger = logging.getLogger("Learning")

MEMORY_FILE = Path(__file__).parent / "memory.json"
CONFIDENCE_DECAY = 0.02       # How much confidence drops if a mapping is corrected
CONFIDENCE_BOOST = 0.05       # How much confidence rises on successful use
MIN_CONFIDENCE = 0.1
MAX_CONFIDENCE = 1.0
AUTO_FILL_THRESHOLD = 0.65    # Confidence required to auto-fill without caution


# ─── Core Memory I/O ──────────────────────────────────────────────────────────

def load_memory() -> dict:
    """Load all learned mappings from disk."""
    if not MEMORY_FILE.exists():
        return {}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load memory: {e}")
        return {}


def save_memory(data: dict):
    """Persist memory to disk safely (atomic write)."""
    tmp = MEMORY_FILE.with_suffix(".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        tmp.replace(MEMORY_FILE)
        logger.debug("Memory saved successfully")
    except IOError as e:
        logger.error(f"Failed to save memory: {e}")
        if tmp.exists():
            tmp.unlink()


# ─── Mapping Operations ───────────────────────────────────────────────────────

def save_mapping(app: str, label: str, field: str, initial_confidence: float = 0.75):
    """
    Save a new label→field mapping for a specific app.
    If mapping already exists, update confidence.
    """
    data = load_memory()
    label_lower = label.lower().strip()

    if app not in data:
        data[app] = {}

    if label_lower in data[app]:
        # Update existing mapping
        existing = data[app][label_lower]
        if existing["field"] == field:
            # Same field → boost confidence
            existing["confidence"] = min(
                MAX_CONFIDENCE,
                existing["confidence"] + CONFIDENCE_BOOST
            )
        else:
            # Different field → this is a correction
            existing["field"] = field
            existing["confidence"] = initial_confidence
            existing["corrections"] = existing.get("corrections", 0) + 1
        existing["last_used"] = time.time()
    else:
        # New mapping
        data[app][label_lower] = {
            "field": field,
            "confidence": initial_confidence,
            "uses": 0,
            "corrections": 0,
            "created": time.time(),
            "last_used": time.time()
        }

    save_memory(data)
    logger.info(f"[{app}] Saved mapping: '{label}' → '{field}' "
                f"(conf={data[app][label_lower]['confidence']:.2f})")


def get_mapping(app: str, label: str) -> dict | None:
    """
    Retrieve best matching field for a label in a specific app.
    Returns {field, confidence} or None if not found.
    """
    data = load_memory()
    label_lower = label.lower().strip()

    if app not in data:
        return None

    # Exact match
    if label_lower in data[app]:
        entry = data[app][label_lower]
        return {"field": entry["field"], "confidence": entry["confidence"]}

    # Fuzzy match within app memory
    best = None
    best_score = 0.0
    for mem_label, mem_data in data[app].items():
        score = _label_similarity(label_lower, mem_label)
        if score > 0.8 and score > best_score:
            best = mem_data
            best_score = score

    if best:
        return {"field": best["field"], "confidence": best["confidence"] * best_score}

    return None


def record_use(app: str, label: str, success: bool = True):
    """Record successful or failed use of a mapping to update confidence."""
    data = load_memory()
    label_lower = label.lower().strip()

    if app in data and label_lower in data[app]:
        entry = data[app][label_lower]
        entry["uses"] = entry.get("uses", 0) + 1
        entry["last_used"] = time.time()

        if success:
            entry["confidence"] = min(MAX_CONFIDENCE,
                                      entry["confidence"] + CONFIDENCE_BOOST * 0.5)
        else:
            entry["confidence"] = max(MIN_CONFIDENCE,
                                      entry["confidence"] - CONFIDENCE_DECAY)
        save_memory(data)


def update_confidence(app: str, label: str, delta: float):
    """Directly adjust confidence for a mapping by a delta value."""
    data = load_memory()
    label_lower = label.lower().strip()

    if app in data and label_lower in data[app]:
        old = data[app][label_lower]["confidence"]
        data[app][label_lower]["confidence"] = max(
            MIN_CONFIDENCE, min(MAX_CONFIDENCE, old + delta)
        )
        save_memory(data)
        logger.info(f"[{app}] Updated confidence for '{label}': "
                    f"{old:.2f} → {data[app][label_lower]['confidence']:.2f}")


def record_correction(app: str, label: str, correct_field: str):
    """
    Called when user manually corrects a filled field.
    Decreases confidence of old mapping and saves new correct mapping.
    """
    logger.info(f"[{app}] User correction: '{label}' should map to '{correct_field}'")
    update_confidence(app, label, -CONFIDENCE_DECAY * 3)
    save_mapping(app, label, correct_field, initial_confidence=0.7)


# ─── App Profile Helpers ──────────────────────────────────────────────────────

def get_app_memory(app: str) -> dict:
    """Get all learned mappings for a specific app."""
    data = load_memory()
    return data.get(app, {})


def list_known_apps() -> list[str]:
    """Return list of apps the system has learned about."""
    data = load_memory()
    return list(data.keys())


def should_auto_fill(confidence: float) -> bool:
    """Return True if confidence is high enough for automatic filling."""
    return confidence >= AUTO_FILL_THRESHOLD


def reset_app_memory(app: str):
    """Clear all learned mappings for a specific app."""
    data = load_memory()
    if app in data:
        del data[app]
        save_memory(data)
        logger.info(f"Reset memory for app: {app}")


def get_memory_stats() -> dict:
    """Return summary statistics of the memory database."""
    data = load_memory()
    total_mappings = sum(len(v) for v in data.values())
    avg_confidence = 0.0
    all_confs = [
        entry["confidence"]
        for app_data in data.values()
        for entry in app_data.values()
    ]
    if all_confs:
        avg_confidence = sum(all_confs) / len(all_confs)
    return {
        "apps": len(data),
        "total_mappings": total_mappings,
        "avg_confidence": round(avg_confidence, 3),
        "known_apps": list(data.keys())
    }


# ─── Utility ──────────────────────────────────────────────────────────────────

def _label_similarity(a: str, b: str) -> float:
    """Simple Jaccard character-bigram similarity for fuzzy label matching."""
    def bigrams(s):
        return set(s[i:i+2] for i in range(len(s) - 1))
    ba, bb = bigrams(a), bigrams(b)
    if not ba or not bb:
        return 0.0
    return len(ba & bb) / len(ba | bb)
