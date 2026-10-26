"""Conservative, explicit postprocessing of standard Yorùbá orthography.

Word-final unmarked n after a vowel can mark nasalization, rather than an
independent coda consonant. This is not a general V+n rewrite: intervocalic
onsets, tone-bearing syllabic nasals and medial/preconsonantal cases are left
alone. Lexical exceptions/loanword pronunciation require separate review.
"""
import unicodedata

VOWELS = {'a': 'a', 'e': 'e', 'ẹ': 'ɛ', 'i': 'i', 'o': 'o', 'ọ': 'ɔ', 'u': 'u'}
# Standard contrastive nasal vowel qualities; do not invent nasal /e/ or /o/.
NASALS = {'a': 'ã', 'ɛ': 'ɛ̃', 'i': 'ĩ', 'ɔ': 'ɔ̃', 'u': 'ũ'}
POSTPROCESSING = 'word-final-nasal-v1'


def _graphemes(word):
    clusters = []
    for ch in unicodedata.normalize('NFD', word.lower()):
        if unicodedata.combining(ch) and clusters:
            clusters[-1] += ch
        else:
            clusters.append(ch)
    return clusters


def _vowel(cluster):
    tone = 'H' if '\u0301' in cluster else 'L' if '\u0300' in cluster else 'M'
    quality = unicodedata.normalize('NFC', cluster.replace('\u0301', '').replace('\u0300', ''))
    return (VOWELS[quality], tone) if quality in VOWELS else None


def nasalize_from_spelling(word, tokens):
    """Merge only an aligned final oral-vowel + bare n prediction.

    Require all written and predicted vowels to agree in number, quality and
    tone. Ambiguous or malformed neural alignments are returned unchanged;
    this correction does not repair arbitrary neural decoding errors.
    Returns a new list and is idempotent.
    """
    out = list(tokens)
    clusters = _graphemes(word)
    if len(clusters) < 2 or clusters[-1] != 'n':
        return out
    expected = _vowel(clusters[-2])
    if expected is None or expected[0] not in NASALS:
        return out
    # A word only; never infer across spaces, punctuation, or unsupported marks.
    consonants = set('bd fghjklmnprstwyṣ'.replace(' ', ''))
    if any(_vowel(c) is None and unicodedata.normalize('NFC', c) not in consonants
           for c in clusters):
        return out
    written = [v for c in clusters if (v := _vowel(c)) is not None]
    predicted = []
    for token in out:
        quality, sep, tone = token.rpartition('_')
        quality = unicodedata.normalize('NFC', quality)
        if sep and tone in {'L', 'M', 'H'} and quality in set(VOWELS.values()) | set(NASALS.values()):
            predicted.append((quality, tone))
    oral, tone = expected
    if predicted != written or len(out) < 2 or out[-2:] != [oral + '_' + tone, 'n']:
        return out
    return out[:-2] + [NASALS[oral] + '_' + tone]
