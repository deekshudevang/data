"""
mapping.py — Semantic Field Matching Module
Uses TF-IDF + cosine similarity to match data labels to form field names/labels,
with fuzzy fallback for near-matches.
"""

import numpy as np
import logging
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger("Mapping")


# ─── Synonym Dictionary for Common Fields ──────────────────────────────────────

SYNONYMS: dict[str, list[str]] = {
    "full name": ["name", "applicant name", "customer name", "full name", "your name"],
    "first name": ["first name", "given name", "fname"],
    "last name": ["last name", "surname", "family name", "lname"],
    "email": ["email", "e-mail", "email address", "mail"],
    "phone": ["phone", "mobile", "telephone", "contact number", "cell", "phone number"],
    "address": ["address", "street", "location", "residence"],
    "city": ["city", "town", "district"],
    "state": ["state", "province", "region"],
    "zip": ["zip", "postal", "pin", "pin code", "zip code", "postal code"],
    "country": ["country", "nation"],
    "date of birth": ["dob", "birth date", "date of birth", "birthday"],
    "age": ["age", "years"],
    "gender": ["gender", "sex"],
    "company": ["company", "organization", "employer", "firm"],
    "job title": ["job title", "position", "designation", "role"],
    "salary": ["salary", "income", "pay", "compensation", "ctc"],
    "website": ["website", "url", "web", "site"],
    "username": ["username", "user name", "login", "user id"],
    "password": ["password", "pass", "secret"],
    "notes": ["notes", "remarks", "comments", "description", "message"],
}


def normalize(text: str) -> str:
    """Lowercase, strip punctuation, and trim text."""
    return re.sub(r"[^a-z0-9 ]", " ", text.lower()).strip()


def expand_with_synonyms(label: str) -> str:
    """Expand a label with its synonyms for better matching."""
    norm = normalize(label)
    for canonical, syns in SYNONYMS.items():
        if norm in [normalize(s) for s in syns]:
            return " ".join([canonical] + syns)
    return norm


class SemanticMatcher:
    """
    TF-IDF based semantic matcher.
    Given a source label and a list of target field names, returns the best match.
    """

    def __init__(self, threshold: float = 0.25):
        self.threshold = threshold
        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb", ngram_range=(2, 4), min_df=1
        )

    def match(self, source_label: str, target_labels: list[str]) -> dict | None:
        """
        Match source_label against list of target labels.
        Returns {target, score} or None if no good match.
        """
        if not target_labels:
            return None

        src_expanded = expand_with_synonyms(source_label)
        tgt_expanded = [expand_with_synonyms(t) for t in target_labels]

        corpus = [src_expanded] + tgt_expanded
        try:
            tfidf = self.vectorizer.fit_transform(corpus)
        except Exception as e:
            logger.error(f"TF-IDF fitting failed: {e}")
            return None

        src_vec = tfidf[0]
        tgt_vecs = tfidf[1:]
        scores = cosine_similarity(src_vec, tgt_vecs)[0]

        best_idx = int(np.argmax(scores))
        best_score = float(scores[best_idx])

        if best_score >= self.threshold:
            return {"target": target_labels[best_idx], "score": best_score}

        logger.debug(f"No match for '{source_label}' (best score: {best_score:.2f})")
        return None


def match_labels_to_fields(
    data_pairs: list[dict],
    detected_fields: list[dict],
    learned_mappings: dict | None = None,
    app_name: str = "default"
) -> list[dict]:
    """
    Match extracted label-value pairs to detected input fields.

    Args:
        data_pairs: [{"label": ..., "value": ...}]
        detected_fields: [{"label": ..., "field": {...}}] (from vision association)
        learned_mappings: app-specific memory from learning.py
        app_name: current app/window name

    Returns:
        List of {label, value, field, confidence, source}
    """
    matcher = SemanticMatcher(threshold=0.2)
    results = []

    field_labels = [f["label"] for f in detected_fields if "label" in f]

    for pair in data_pairs:
        src_label = pair.get("label", "")
        src_value = pair.get("value", "")

        best_match = None
        source = "ai"
        confidence = 0.0

        # 1. Check learned memory first
        if learned_mappings and app_name in learned_mappings:
            mem = learned_mappings[app_name]
            norm_src = normalize(src_label)
            for mem_label, mem_data in mem.items():
                if normalize(mem_label) == norm_src:
                    field_name = mem_data.get("field")
                    conf = mem_data.get("confidence", 0.5)
                    # Find field with matching label
                    target_field = next(
                        (f["field"] for f in detected_fields if f.get("label") == field_name),
                        None
                    )
                    if target_field:
                        best_match = target_field
                        confidence = conf
                        source = "memory"
                        break

        # 2. Fall back to semantic AI matching
        if not best_match and field_labels:
            match = matcher.match(src_label, field_labels)
            if match:
                target_label = match["target"]
                target_field = next(
                    (f["field"] for f in detected_fields if f.get("label") == target_label),
                    None
                )
                if target_field:
                    best_match = target_field
                    confidence = match["score"]
                    source = "ai"

        if best_match:
            results.append({
                "label": src_label,
                "value": src_value,
                "field": best_match,
                "confidence": confidence,
                "source": source
            })
        else:
            logger.warning(f"No field match found for label: '{src_label}'")

    logger.info(f"Matched {len(results)}/{len(data_pairs)} label-value pairs to fields")
    return results
