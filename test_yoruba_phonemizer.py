import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from yoruba_phonemizer import convert_word, convert_text, ConversionError

def test_gb_is_single_phone():
    assert convert_word("gbà")['phonemes'] == ['ɡ͡b', 'a_L']

def test_yoruba_special_letters():
    assert convert_word("ṣé")['phonemes'] == ['ʃ', 'e_H']
    assert convert_word("ọ̀")['phonemes'] == ['ɔ_L']
    assert convert_word("ẹ́")['phonemes'] == ['ɛ_H']

def test_tone_defaults_to_mid_only_when_unmarked():
    assert convert_word("aba")['phonemes'] == ['a_M', 'b', 'a_M']
    assert convert_word("àbá")['phonemes'] == ['a_L', 'b', 'a_H']

def test_combining_and_precomposed_normalize_same():
    assert convert_word("ẹ́")['phonemes'] == convert_word("e\u0323\u0301")['phonemes']

def test_syllabic_nasal_tone():
    assert convert_word("ń")['phonemes'] == ['n̩_H']
    assert convert_word("ǹ")['phonemes'] == ['n̩_L']

def test_unknown_symbols_fail_loudly():
    with pytest.raises(ConversionError):
        convert_word("abc🙂")

def test_phrase_conversion():
    result = convert_text("àbí ṣé")
    assert len(result['words']) == 2
    assert result['words'][0]['phonemes'] == ['a_L', 'b', 'i_H']

def test_ipa_is_returned():
    result = convert_word("gbà")
    assert result['ipa'] == 'ɡ͡b a˩'
