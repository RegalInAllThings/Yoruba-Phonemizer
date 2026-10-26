import unicodedata

import pytest
from fastapi.testclient import TestClient
import app

@pytest.fixture
def client():
    with TestClient(app.app) as client:
        yield client


def test_real_checkpoint_and_conversion(client):
    assert client.get('/healthz').status_code == 200
    response = client.post('/api/phonemize', json={'text': 'Yorùbá!'})
    assert response.status_code == 200
    assert response.json()['phonemes'] == '[j o_M r u_L b a_H]!'
    assert response.json()['engine'] == 'neural'
    assert len(app.app.state.converter.model.state_dict()) > 10


def test_normalization_and_punctuation(client):
    word = 'Ọ̀RUN, ẹran!'
    a = client.post('/api/phonemize', json={'text': word}).json()
    b = client.post('/api/phonemize', json={'text': unicodedata.normalize('NFD', word)}).json()
    assert a == b
    assert a['phonemes'] == '[ɔ_L r u_M n], [ɛ_M r a_M n]!'


@pytest.mark.parametrize('text', ['', '   ', '123!', 'hello🙂世界', 'a'*501, 'a'*41, 'a '*61])
def test_invalid_input(client, text):
    assert client.post('/api/phonemize', json={'text': text}).status_code == 422


def test_static_page(client):
    page = client.get('/')
    assert page.status_code == 200
    assert 'Developed by Stephen Mayowa Afolabi.' in page.text
    assert client.get('/assets/app.js').status_code == 200


def test_missing_checkpoint_has_no_fallback(monkeypatch, tmp_path):
    monkeypatch.setenv('MODEL_PATH', str(tmp_path / 'missing.pt'))
    with TestClient(app.app) as client:
        assert client.get('/healthz').status_code == 503
        assert client.post('/api/phonemize', json={'text': 'Yorùbá'}).status_code == 503


def test_changed_checkpoint_rejected(monkeypatch, tmp_path):
    fake = tmp_path / 'bad.pt'
    fake.write_bytes(b'invalid')
    monkeypatch.setenv('MODEL_PATH', str(fake))
    with TestClient(app.app) as client:
        assert client.get('/healthz').status_code == 503


def test_inference_failure_has_no_fallback(client, monkeypatch):
    def fail(*args):
        raise ValueError('failed')
    monkeypatch.setattr(app.app.state.converter, 'word', fail)
    assert client.post('/api/phonemize', json={'text': 'ẹran'}).status_code == 503


def test_decoder_limit(client):
    with pytest.raises(ValueError, match='did not terminate'):
        app.app.state.converter.word('Yorùbá', max_steps=0)
