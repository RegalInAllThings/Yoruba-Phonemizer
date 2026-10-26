import unicodedata

import pytest
from fastapi.testclient import TestClient
import app
from yorubag2p_prototype.orthography import nasalize_from_spelling as correct
from yorubag2p_prototype.reviewed import nasalize_from_spelling as reviewed_correct

@pytest.mark.parametrize('word,raw,want', [
    ('ẹran', ['ɛ_M', 'r', 'a_M', 'n'], ['ɛ_M', 'r', 'ã_M']),
    ('ọrùn', ['ɔ_M', 'r', 'u_L', 'n'], ['ɔ_M', 'r', 'ũ_L']),
    ('ọ̀run', ['ɔ_L', 'r', 'u_M', 'n'], ['ɔ_L', 'r', 'ũ_M']),
    ('kán', ['k', 'a_H', 'n'], ['k', 'ã_H']),
    ('kàn', ['k', 'a_L', 'n'], ['k', 'ã_L']),
    ('kan', ['k', 'a_M', 'n'], ['k', 'ã_M']),
    ('in', ['i_M', 'n'], ['ĩ_M']),
    ('ẹn', ['ɛ_M', 'n'], ['ɛ̃_M']),
    ('ọn', ['ɔ_M', 'n'], ['ɔ̃_M']),
])
def test_aligned_final_nasal(word, raw, want):
    original = raw.copy()
    assert correct(word, raw) == want
    assert correct(unicodedata.normalize('NFD', word.upper()), raw) == want
    assert raw == original
    assert correct(word, want) == want
    assert reviewed_correct(word, raw) == want

@pytest.mark.parametrize('word,phones', [
    ('inú', ['i_M','n','u_H']), # intervocalic consonantal onset
    ('aná', ['a_M','n','a_H']),
    ('ìná', ['i_L','n','a_H']),
    ('ń', ['n_H']), ('ǹ', ['n_L']),
    ('ań', ['a_M','n_H']), ('aǹ', ['a_M','n_L']),
    ('en', ['e_M','n']), ('on', ['o_M','n']), # no automatic nasal e/o
    ('anka', ['a_M','n','k','a_M']), # medial contexts deferred
    ('a n', ['a_M','n']), ('a-n', ['a_M','n']),
    ('kan', ['k','a_H','n']), # tone mismatch
    ('kan', ['k','i_M','n']), # quality mismatch
    ('kan', ['k','a_M','n','a_M']), # neural insertion
    ('ẹran', ['r','a_M','n']), # neural deletion
    ('ẹran', ['e_M','r','a_M','n']), # earlier vowel mismatch
    ('kan', ['k','a_M','n_L']), # tone-bearing n is not bare marker
    ('kan', ['k','ã_M']),
])
def test_no_unjustified_merge(word, phones):
    assert correct(word, phones) == phones


def test_real_api_and_raw_model_boundaries():
    with TestClient(app.app) as client:
        raw = app.app.state.converter.word('ẹran')
        assert raw == ['ɛ_M', 'r', 'a_M', 'n']
        response = client.post('/api/phonemize', json={'text': 'ẸRAN, ọrùn; ọ̀run! inú aná ń ǹ'})
        assert response.status_code == 200
        assert response.json()['phonemes'] == '[ɛ_M r ã_M], [ɔ_M r ũ_L]; [ɔ_L r ũ_M]! [i_M n u_H] [a_M n a_H] [n_H] [n_L]'
        assert response.json()['postprocessing'] == 'word-final-nasal-v1'
        assert client.get('/healthz').json()['checkpoint_sha256'] == app.EXPECTED_SHA256
        # No merging between the last vowel of one word and the next word's n.
        a = client.post('/api/phonemize', json={'text': 'a náà'}).json()['phonemes']
        assert a.startswith('[a_M] [n ')

@pytest.mark.parametrize('word,want', [
    ('ẹran', ['ɛ_M','r','ã_M']),
    ('ọrùn', ['ɔ_M','r','ũ_L']),
    ('ọ̀run', ['ɔ_L','r','ũ_M']),
    ('iyán', ['i_M','j','ã_H']),
    ('ǹkan', ['n_L','k','ã_M']),
])
def test_reviewed_lexical_entries_preserved(word, want):
    from yorubag2p_prototype.reviewed import ReviewedConverter
    # Lexical entries return before touching the optional rule engine.
    reviewed = ReviewedConverter.__new__(ReviewedConverter)
    assert reviewed.word(word.upper()) == want
