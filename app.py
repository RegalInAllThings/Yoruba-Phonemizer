"""Single-process CPU neural inference. No rule-based fallback."""
import hashlib
import logging
import os
import sys
import unicodedata
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock

import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from yorubag2p_prototype.neural import NeuralConverter
from yorubag2p_prototype.orthography import nasalize_from_spelling, POSTPROCESSING

CHECKPOINT = ROOT / 'models/g2p_silver_model.pt'
EXPECTED_SHA256 = 'd4d5d8cc49500946abc1b8f84df7a36bc4df8f5b09849d40db487211b32df217'
lock = Lock()

@asynccontextmanager
async def lifespan(app):
    app.state.converter = None
    try:
        torch.set_num_threads(1)
        path = Path(os.environ.get('MODEL_PATH', CHECKPOINT))
        if hashlib.sha256(path.read_bytes()).hexdigest() != EXPECTED_SHA256:
            raise ValueError('Checkpoint integrity check failed')
        app.state.converter = NeuralConverter(path)
        app.state.converter.word('Yorùbá')
    except Exception:
        logging.exception('Neural model unavailable; conversion disabled')
    yield

app = FastAPI(title='Yorùbá Phonemizer', lifespan=lifespan)
app.mount('/assets', StaticFiles(directory=ROOT / 'web'), name='assets')

class Request(BaseModel):
    text: str = Field(min_length=1, max_length=500)

@app.get('/')
def index():
    return FileResponse(ROOT / 'web/index.html')

@app.get('/healthz')
def health():
    if getattr(app.state, 'converter', None) is None:
        raise HTTPException(503, 'Trained model unavailable')
    return {'status': 'ok', 'engine': 'neural', 'checkpoint_sha256': EXPECTED_SHA256, 'postprocessing': POSTPROCESSING}


def tokenize(text):
    parts, current = [], ''
    for ch in text:
        if ch.isalpha() or unicodedata.category(ch).startswith('M'):
            current += ch
        else:
            if current:
                parts.append((True, current))
                current = ''
            parts.append((False, ch))
    if current:
        parts.append((True, current))
    return parts

@app.post('/api/phonemize')
def phonemize(payload: Request):
    converter = getattr(app.state, 'converter', None)
    if converter is None:
        raise HTTPException(503, 'The trained model is unavailable. Please try again later.')
    text = unicodedata.normalize('NFC', payload.text.lower())
    parts = tokenize(text)
    words = [token for word, token in parts if word]
    if not words:
        raise HTTPException(422, 'Enter Yorùbá words to convert.')
    unsupported = sorted({ch for word in words for ch in word if ch not in converter.ci})
    if unsupported:
        raise HTTPException(422, 'Unsupported characters: ' + ' '.join(unsupported))
    if any(len(word) > 40 for word in words) or len(words) > 60:
        raise HTTPException(422, 'Use up to 60 words, with at most 40 characters per word.')
    try:
        with lock:
            results = []
            for word, token in parts:
                if word:
                    phones = nasalize_from_spelling(token, converter.word(token))
                    if not phones:
                        raise ValueError('Empty model prediction')
                    results.append('[' + ' '.join(phones) + ']')
                else:
                    results.append(token)
    except Exception:
        logging.exception('Neural conversion failed')
        raise HTTPException(503, 'The trained model could not complete this conversion.')
    return {'phonemes': ''.join(results), 'engine': 'neural', 'experimental': True, 'postprocessing': POSTPROCESSING}
