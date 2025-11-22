from __future__ import annotations
import os
import re
from typing import Any, Dict, List, Optional, Literal
import asyncio
import spacy
import random
from spacy.tokens import Doc, Token
from mcp.server.fastmcp import FastMCP




# ---- Load Spacy Model ----
SPACY_model = "en_core_web_sm"
try:
    nlp = spacy.load(SPACY_model)
except OSError:
    from spacy.cli import download
    download(SPACY_model)
    nlp = spacy.load(SPACY_model)


# ---- Exceptions based on prononciation types (normalised to lowercase)----
_VOWEL_EXC = {"honest", "hour", "heir", "mba", "fbi", "mri", "sos","honour","heir","honor","heirloom","hourglass","honestly","honorary","honorable","honouring",
              "heirship","herb","herbal","herbs","honesty","honours","honored"}
_CONS_EXC = {"university", "unicorn", "euro", "one", "use", "user", "ubiquity","unilateral","unison","united","uniform","unique","unit","union","universe",
              "university","eulogy","euphemism","euphoria","eucalyptus","eugenics","euphonium","eureka","european","eurovision"}

_ACRONYM_VOWEL_INITIALS = set("AEFHILMNORSX")

def _starts_with_vowel_sound(word: str) -> bool:
    """Heuristic for choosing 'a' vs 'an'."""
    if not word:
        return False
    w = word.lower()

    if w in _VOWEL_EXC:
        return True
    if w in _CONS_EXC:
        return False
    
    # ALL-CAPS acronym handling (e.g., "FBI", "MVP")
    if word.isupper() and word.isalpha():
        return word[0] in _ACRONYM_VOWEL_INITIALS
    # Default: first character vowel?
    return w[0] in "aeiou"

def _choose_article(next_word: str, original_article: str) -> str:
    correct = "an" if _starts_with_vowel_sound(next_word) else "a"
    return correct.capitalize() if original_article and original_article[0].isupper() else correct

def correct_a_an_spacy(sentence: str) -> str:
    """Correct 'a' vs 'an' in a sentence using spaCy for tokenization."""
    doc = nlp(sentence)
    corrected_tokens = []
    for i, token in enumerate(doc):
        if token.text.lower() in {"a", "an"} and i + 1 < len(doc):
            next_token = doc[i + 1]
            correct_article = _choose_article(next_token.text, token.text)
            corrected_tokens.append(correct_article)
        else:
            corrected_tokens.append(token.text)
    # Join tokens with the original whitespace by reconstructing a Doc and using text_with_ws
    new_doc = spacy.tokens.Doc(doc.vocab, words=corrected_tokens)
    # As we don't have whitespace info preserved here, return a simple joined string
    return " ".join(corrected_tokens)

# Replace "absent the" tool
def replace_absent_the(text: str) -> str:
    """Replace 'absent the' with 'without the' (case-insensitive),
    preserving sentence initial capitalization."""
    def _replacement(match: re.Match) -> str:
        matched_text = match.group(0)
        if matched_text[0].isupper():
            return "Without the"
        else:
            return "without the"

    pattern = re.compile(r'\babsent the\b', re.IGNORECASE)
    return pattern.sub(_replacement, text)

# Example additional rule: expand "Abu Dhabi" to "Abu Dhabi Sovereign" only if you want
def replace_abu_dhabi_expand(text: str) -> str:
    """Replace the phrase 'Abu Dhabi' with 'Abu Dhabi Sovereign' (word-boundary, case-preserving)."""
    def _repl(match: re.Match) -> str:
        matched = match.group(0)
        # preserve capitalization of first letter
        if matched[0].isupper():
            return "Abu Dhabi Sovereign"
        else:
            return "abu dhabi sovereign"
    return re.sub(r'\bAbu\s+Dhabi\b', _repl, text, flags=re.IGNORECASE)

# Initialize FastMCP server instance
mcp = FastMCP("CopyEditingMCP")

# ---- FastMCP tool wrappers ----
@mcp.tool(
    name="correct_a_an_spacy",
    description="Correct 'a' vs 'an' in a given sentence.",
)
async def correct_a_an_spacy_tool(sentence: str) -> str:
    return await asyncio.to_thread(correct_a_an_spacy, sentence)

@mcp.tool(
    name="replace_absent_the",
    description="Replace 'absent the' with 'without the' in a given text.",
)
async def replace_absent_the_tool(text: str) -> str:
    return await asyncio.to_thread(replace_absent_the, text)

@mcp.tool(
    name="replace_abu_dhabi_expand",
    description="Replace 'Abu Dhabi' with 'Abu Dhabi Sovereign'."
)
async def replace_abu_dhabi_expand_tool(text: str) -> str:
    return await asyncio.to_thread(replace_abu_dhabi_expand, text)

# If executed directly, run the FastMCP server (if available)
if __name__ == "__main__":
    try:
        mcp.run()
    except Exception:
        # If FastMCP isn't installed or run fails, just print a message and exit
        print("FastMCP run failed or not installed — module exports tools as async functions for import/use by other apps.")