
import unicodedata
from .hybrid import HybridConverter

def normalize(s):
    return unicodedata.normalize("NFC", s.strip())

REVIEWED = {
    normalize("ẹran"): ["ɛ_M", "r", "ã_M"],
    normalize("ọrùn"): ["ɔ_M", "r", "ũ_L"],
    normalize("ọ̀run"): ["ɔ_L", "r", "ũ_M"],
    normalize("iyán"): ["i_M", "j", "ã_H"],
    normalize("ǹkan"): ["n_L", "k", "ã_M"],
}

VOWEL_TO_IPA = {
    "a": "a", "e": "e", "ẹ": "ɛ",
    "i": "i", "o": "o", "ọ": "ɔ",
    "u": "u",
}

NASAL_IPA = {
    "a": "ã", "e": "ẽ", "ɛ": "ɛ̃",
    "i": "ĩ", "o": "õ", "ɔ": "ɔ̃",
    "u": "ũ",
}

TONES = {"H", "M", "L"}

def tone_of(char):
    decomposed = unicodedata.normalize("NFD", char)
    if "\u0301" in decomposed:
        return "H"
    if "\u0300" in decomposed:
        return "L"
    return "M"

def repair_gb(tokens):
    out = []
    i = 0
    while i < len(tokens):
        if (
            i + 1 < len(tokens)
            and tokens[i] in ("ɡ", "g")
            and tokens[i + 1] == "b"
        ):
            out.append("gb")
            i += 2
        else:
            out.append(tokens[i])
            i += 1
    return out

def nasalize_from_spelling(word, tokens):
    """
    Align written vowels with their corresponding
    vowel tokens in sequence.

    Convert V+n to a nasal vowel only when n is
    word-final or followed by a consonant.

    This is a provisional orthographic heuristic.
    """
    word = normalize(word)
    tokens = list(tokens)

    written_vowels = []

    for i, char in enumerate(word):
        base = unicodedata.normalize("NFD", char)[0]

        if base not in VOWEL_TO_IPA:
            continue

        next_char = word[i + 1] if i + 1 < len(word) else ""

        nasal_candidate = (
            next_char == "n"
            and (
                i + 2 == len(word)
                or (
                    i + 2 < len(word)
                    and unicodedata.normalize(
                        "NFD", word[i + 2]
                    )[0] not in VOWEL_TO_IPA
                )
            )
        )

        written_vowels.append((
            VOWEL_TO_IPA[base],
            tone_of(char),
            nasal_candidate
        ))

    out = []
    vowel_index = 0
    i = 0

    while i < len(tokens):
        token = tokens[i]
        parts = token.rsplit("_", 1)

        if (
            len(parts) == 2
            and parts[1] in TONES
            and parts[0] in NASAL_IPA
        ):
            if vowel_index < len(written_vowels):
                expected_ipa, expected_tone, nasal = (
                    written_vowels[vowel_index]
                )

                if (
                    nasal
                    and parts[0] == expected_ipa
                    and parts[1] == expected_tone
                    and i + 1 < len(tokens)
                    and tokens[i + 1] == "n"
                ):
                    out.append(
                        NASAL_IPA[parts[0]] + "_" + parts[1]
                    )
                    i += 2
                    vowel_index += 1
                    continue

            vowel_index += 1

        out.append(token)
        i += 1

    return out

class ReviewedConverter:
    def __init__(self, checkpoint_path):
        self.base = HybridConverter(str(checkpoint_path))

    def word(self, word):
        word = normalize(word)

        if not word:
            return []

        if word in REVIEWED:
            return REVIEWED[word].copy()

        tokens = repair_gb(list(self.base.word(word)))

        if word.startswith("ǹ") and (
            not tokens or tokens[0] != "n_L"
        ):
            tokens.insert(0, "n_L")

        elif word.startswith("ń") and (
            not tokens or tokens[0] != "n_H"
        ):
            tokens.insert(0, "n_H")

        return nasalize_from_spelling(word, tokens)


import unicodedata as _unicode_case

_original_reviewed_word = ReviewedConverter.word

def _case_normalized_word(self, word):
    normalized = _unicode_case.normalize("NFC", word).lower()
    return _original_reviewed_word(self, normalized)

ReviewedConverter.word = _case_normalized_word
