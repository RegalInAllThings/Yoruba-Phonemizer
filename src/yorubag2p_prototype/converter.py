import unicodedata
from yoruba_g2p import YorubaG2P

NASAL_OVERRIDES = {'ń': ['n_H'], 'ǹ': ['n_L']}

class YorubaConverter:
    """Rule-based, tone-preserving Yoruba G2P prototype; NOT gold-validated."""
    def __init__(self):
        self.baseline = YorubaG2P()

    def word(self, word):
        word = unicodedata.normalize('NFC', word).lower()
        if word in NASAL_OVERRIDES:
            return NASAL_OVERRIDES[word][:]
        phones, aligned = self.baseline.yoruba_word_to_ipa_phones(word)
        return list(phones)

    @staticmethod
    def tokenize(text):
        text = unicodedata.normalize('NFC', text)
        parts, current = [], ''
        for ch in text:
            is_word = ch.isalpha() or unicodedata.category(ch).startswith('M')
            if is_word:
                current += ch
            else:
                if current:
                    parts.append(('word', current))
                    current = ''
                parts.append(('other', ch))
        if current:
            parts.append(('word', current))
        return parts

    def text(self, text):
        result = []
        for kind, token in self.tokenize(text):
            result.append('[' + ' '.join(self.word(token)) + ']' if kind == 'word' else token)
        return ''.join(result)

    def batch(self, texts):
        return [self.text(t) for t in texts]
