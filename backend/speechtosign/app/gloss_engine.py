"""
gloss_engine.py — ISL grammar reordering + dictionary mapping.

Stage 1 — Grammar reordering:
  Rule 1: Time words  → move to front
  Rule 2: Negation words → move to end
  Rule 3: Question words → move to end
  (Combined rules apply in the correct order)

Stage 2 — Dictionary mapping:
  Each token is looked up in dictionary.json.
  Unknown tokens are silently dropped.
"""

import json
from pathlib import Path

# ── Word category lists ───────────────────────────────────────────────────────

TIME_WORDS: set[str] = {
    "today", "tomorrow", "yesterday", "now", "morning",
    "night", "later", "time", "then", "soon", "already",
}

NEGATION_WORDS: set[str] = {
    "not", "no", "never", "dont", "cant", "wont",
    "cannot", "nothing", "nobody", "nowhere",
}

QUESTION_WORDS: set[str] = {
    "where", "what", "when", "who", "why", "how", "which",
}

# Helper words dropped silently (not in dict — handled here explicitly)
HELPER_WORDS: set[str] = {
    "do", "did", "does", "will", "would", "could", "should",
    "shall", "may", "might", "must", "have", "has", "had",
}

# ── Load dictionary ───────────────────────────────────────────────────────────

_DICT_PATH = Path(__file__).parent / "dictionary.json"

def _load_dictionary() -> dict[str, str]:
    with open(_DICT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

_DICTIONARY: dict[str, str] = _load_dictionary()


# ── Stage 1: ISL Grammar Reordering ──────────────────────────────────────────

def _reorder(tokens: list[str]) -> list[str]:
    """
    Apply ISL grammar reordering rules to a token list.

    Final order: [time_words] + [subject/verb/object] + [negation] + [question]
    """
    time_tokens     = [t for t in tokens if t in TIME_WORDS]
    negation_tokens = [t for t in tokens if t in NEGATION_WORDS]
    question_tokens = [t for t in tokens if t in QUESTION_WORDS]

    # Body = everything that is NOT a time / negation / question word
    # and NOT a helper word
    body_tokens = [
        t for t in tokens
        if t not in TIME_WORDS
        and t not in NEGATION_WORDS
        and t not in QUESTION_WORDS
        and t not in HELPER_WORDS
    ]

    # ISL order: TIME → BODY → NEGATION → QUESTION
    reordered = time_tokens + body_tokens + negation_tokens + question_tokens
    return reordered


# ── Stage 2: Dictionary Mapping ───────────────────────────────────────────────

def _map_to_gloss(tokens: list[str]) -> list[str]:
    """
    Map each token to its ISL gloss via dictionary.json.
    Tokens not found in the dictionary are silently dropped.
    """
    gloss = []
    for token in tokens:
        mapped = _DICTIONARY.get(token)
        if mapped:
            gloss.append(mapped)
        # silently skip unknown tokens
    return gloss


# ── Public API ────────────────────────────────────────────────────────────────

def build_gloss(tokens: list[str]) -> list[str]:
    """
    Full gloss pipeline:
      normalized tokens → grammar reorder → dictionary mapping → ISL gloss list
    """
    reordered = _reorder(tokens)
    gloss     = _map_to_gloss(reordered)
    return gloss