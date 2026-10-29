"""Conservative rule-based Yorùbá grapheme-to-phoneme converter.

This is a transparent baseline, not a complete lexical pronunciation dictionary.
It preserves written tone on vowel nuclei and never guesses missing tone marks.
"""
from __future__ import annotations
import unicodedata

VOWELS = {
    "a": ("a", "a"), "e": ("e", "e"), "ẹ": ("ɛ", "ẹ"),
    "i": ("i", "i"), "o": ("o", "o"), "ọ": ("ɔ", "ọ"), "u": ("u", "u"),
}
CONSONANTS = {
    "b": "b", "d": "d", "f": "f", "g": "ɡ", "gb": "ɡ͡b",
    "h": "h", "j": "d͡ʒ", "k": "k", "l": "l", "m": "m",
    "n": "n", "p": "p", "r": "ɾ", "s": "s", "ṣ": "ʃ",
    "t": "t", "w": "w", "y": "j",
}
TONE_MARKS = {"\u0301": "H", "\u0300": "L"}
IPA_TONE = {"H": "˥", "M": "˧", "L": "˩"}

class ConversionError(ValueError):
    pass

def _clusters(text: str) -> list[str]:
    """Group combining diacritics with the preceding Unicode character."""
    out: list[str] = []
    for ch in unicodedata.normalize("NFD", text.lower()):
        if unicodedata.combining(ch) and out:
            out[-1] += ch
        else:
            out.append(ch)
    return out

def _base(cluster: str) -> str:
    return unicodedata.normalize("NFC", "".join(c for c in cluster if c not in TONE_MARKS))

def _tone(cluster: str) -> str:
    marks = [TONE_MARKS[c] for c in cluster if c in TONE_MARKS]
    if len(marks) > 1:
        raise ConversionError(f"Conflicting tone marks in grapheme: {unicodedata.normalize('NFC', cluster)}")
    return marks[0] if marks else "M"

def _is_vowel(cluster: str) -> bool:
    return _base(cluster) in VOWELS

def convert_word(word: str) -> dict:
    """Convert one alphabetic Yorùbá word to phoneme tokens and IPA-style output.

    Output phoneme tokens attach tone labels to vowel nuclei, e.g. a_H. Mid tone
    is assigned only where tone is unmarked in the input; this is an orthographic
    default, not lexical disambiguation. `n` is treated as /n/ unless part of a
    syllabic-nasal pattern requiring a dictionary/context decision.
    """
    normalized = unicodedata.normalize("NFC", word.strip().lower())
    if not normalized:
        raise ConversionError("Enter a word.")
    if any(ch.isspace() for ch in normalized):
        raise ConversionError("Pass one word at a time; use convert_text for phrases.")
    gs = _clusters(normalized)
    tokens: list[str] = []
    ipa: list[str] = []
    i = 0
    while i < len(gs):
        g = gs[i]
        base = _base(g)
        if base == "g" and i + 1 < len(gs) and _base(gs[i + 1]) == "b":
            # A tone mark on a consonant is not a valid way to mark the digraph.
            if any(unicodedata.combining(c) for c in g + gs[i + 1]):
                raise ConversionError("Unexpected diacritic on the gb digraph.")
            tokens.append("ɡ͡b")
            ipa.append("ɡ͡b")
            i += 2
            continue
        if base in VOWELS:
            phone, _ = VOWELS[base]
            tone = _tone(g)
            tokens.append(f"{phone}_{tone}")
            ipa.append(phone + IPA_TONE[tone])
        elif base in CONSONANTS:
            if any(unicodedata.combining(c) for c in g if c not in TONE_MARKS and c != "\u0323"):
                raise ConversionError(f"Unsupported diacritic in {unicodedata.normalize('NFC', g)}")
            # Acute/grave marks on n can indicate a syllabic nasal; preserve its tone.
            if base == "n" and any(c in TONE_MARKS for c in g):
                tone = _tone(g)
                tokens.append(f"n̩_{tone}")
                ipa.append("n̩" + IPA_TONE[tone])
            else:
                tokens.append(CONSONANTS[base])
                ipa.append(CONSONANTS[base])
        else:
            raise ConversionError(f"Unsupported character: {unicodedata.normalize('NFC', g)}")
        i += 1
    return {"input": word, "normalized": normalized, "phonemes": tokens, "ipa": " ".join(ipa), "engine": "rule-based-baseline", "warning": "Experimental grapheme mapping; lexical/contextual pronunciations and missing tone marks are not resolved."}

def convert_text(text: str) -> dict:
    """Convert whitespace-separated words, preserving whitespace/punctuation lightly."""
    import re
    if not text or not text.strip():
        raise ConversionError("Enter Yorùbá text.")
    words = re.findall(r"[^\W\d_]+(?:['’][^\W\d_]+)*", text, flags=re.UNICODE)
    results = [convert_word(w) for w in words]
    return {"input": text, "words": results, "engine": "rule-based-baseline", "warning": "Experimental grapheme mapping; lexical/contextual pronunciations and missing tone marks are not resolved."}
