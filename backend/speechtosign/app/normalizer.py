"""
normalizer.py — Text preprocessing pipeline for ISL gloss conversion.

Pipeline:
  1. Lowercase
  2. Remove punctuation
  3. Tokenize
  4. Remove filler words
  5. Rule-based stemming (longest-suffix-first) + double-consonant collapse
"""

import re
import string

# ── Filler words removed before stemming ─────────────────────────────────────
FILLER_WORDS: set[str] = {
    "am", "is", "are", "the", "a", "an", "to", "of", "was", "were",
    "do", "did", "does",
}

# ── Words that must NOT be stemmed ───────────────────────────────────────────
PROTECTED_WORDS: set[str] = {
    "tired", "teacher", "computer", "water", "mother", "sister",
    "better", "letter", "matter", "butter", "after", "center",
}

# ── Suffix rules — longest suffix checked first ───────────────────────────────
# Each entry: (suffix_to_remove, replacement_string)
SUFFIX_RULES: list[tuple[str, str]] = [
    ("oing", "o"),    # going → go
    ("tion", ""),     # education → educa  (then dict handles it)
    ("sion", ""),     # permission → permi
    ("ing",  ""),     # walking → walk
    ("ed",   ""),     # walked → walk
    ("er",   ""),     # runner → runn → run (after consonant collapse)
    ("est",  ""),     # fastest → fast
    ("ly",   ""),     # quickly → quick
    ("es",   ""),     # goes → go
    ("s",    ""),     # runs → run
]

# Minimum stem length — don't trim words shorter than this
MIN_STEM_LEN = 2

# Explicit word corrections applied before suffix rules
EXPLICIT_STEMS: dict[str, str] = {
    "going":   "go",
    "doing":   "do",
    "being":   "be",
    "having":  "have",
    "saying":  "say",
    "getting": "get",
    "letting": "let",
    "putting": "put",
    "sitting": "sit",
    "running": "run",
    "coming":  "come",
    "seeing":  "see",
}

CONSONANTS = set("bcdfghjklmnpqrstvwxyz")


def _collapse_double_consonants(word: str) -> str:
    """
    Collapse trailing double consonants produced by suffix removal.
    Example: runn → run,  walll → wall (only one pair collapsed)
    """
    if len(word) >= 2 and word[-1] == word[-2] and word[-1] in CONSONANTS:
        return word[:-1]
    return word


def _stem(word: str) -> str:
    """
    Apply rule-based suffix removal (longest match first),
    then collapse double consonants.
    """
    if word in PROTECTED_WORDS:
        return word

    # Check explicit corrections first (handles irregular forms like going→go)
    if word in EXPLICIT_STEMS:
        return EXPLICIT_STEMS[word]

    for suffix, replacement in SUFFIX_RULES:
        if word.endswith(suffix):
            stem = word[: len(word) - len(suffix)] + replacement
            if len(stem) >= MIN_STEM_LEN:
                stem = _collapse_double_consonants(stem)
                return stem
            # stem too short — skip this rule
            break

    return word


def normalize(text: str) -> list[str]:
    """
    Full normalization pipeline.
    Returns a list of cleaned, stemmed tokens.
    """
    # Step 1 — Lowercase
    text = text.lower()

    # Step 2 — Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))

    # Step 3 — Tokenize (split on whitespace)
    tokens = text.split()

    # Step 4 — Remove filler words
    tokens = [t for t in tokens if t not in FILLER_WORDS]

    # Step 5 — Stem each remaining token
    tokens = [_stem(t) for t in tokens]

    return tokens