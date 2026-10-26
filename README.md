# Yorùbá Phonemizer

Experimental Yorùbá text-to-phoneme website, continuing YorùbáG2P.
Developed by Stephen Mayowa Afolabi.

## What runs

FastAPI serves a mobile-friendly HTML/CSS/JavaScript frontend and the actual recovered PyTorch GRU checkpoint in one CPU process. No external AI API, database, paid font, or audio service is needed. The model is not retrained. `POST /api/phonemize` uses `NeuralConverter`, followed by the explicitly identified `word-final-nasal-v1` orthographic postprocessor; it never substitutes the rule or reviewed converter. The checkpoint is verified by SHA-256 before loading; missing, changed or failed models return HTTP 503 with no substitute prediction. `/healthz` succeeds only after model loading and an inference warmup.

The original neural converter's two explicit standalone `ń` / `ǹ` overrides are retained. Other words use greedy neural decoding. Input is lowercase NFC-normalized; punctuation and spacing are preserved. Unknown word characters are rejected instead of silently mapped to unknown tokens. Requests allow 500 characters, 60 words, and 40 characters per word; decoding stops at EOS or reports failure at 60 steps. One worker and one CPU thread keep memory use modest.

## Research status

The model learned silver labels from `yoruba-g2p==0.2.4`. A Yorùbá language expert positively reviewed 100 project conversion outputs, according to the project owner. The reviewed sample is not included here and is not established as an independent evaluation of the neural endpoint. Independently verified held-out performance is not yet established.

Raw neural launch checks reveal errors: `ẹran` yields `[ɛ_M r a_M n]` (now corrected by the API to `[ɛ_M r ã_M]`), and `ǹkan` yields `[d k p n n]`. The 43-token phone vocabulary contains no nasal-vowel tokens and does not represent `gb` as a single phone. Outputs are research predictions, not pronunciation authorities. See [the inference audit](reports/launch_inference_audit.json) for actual outputs, checkpoint hash and measured memory.

`src/yorubag2p_prototype/reviewed.py` retains its reviewed lexical entries and now shares the conservative nasalization helper in `orthography.py`. Its former provisional preconsonantal rewrite has been narrowed to aligned word-final contexts. It calls the hybrid converter's default rule mode, so using it would not demonstrate trained-model predictions. Its optional `yoruba-g2p==0.2.4` dependency is not required or installed by the web application. Historical Stage 20 reports and metadata describe their original snapshots; the launch audit describes this application.

## Run and test

Python 3.12, Linux CPU:

```sh
python -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
.venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000 --workers 1
```

Open http://localhost:8000. GitHub Actions runs the 48 automated tests on pushes and pull requests. Tests verify actual model inference, Unicode normalization, punctuation, validation, static files, unavailable/corrupt checkpoint behavior and inference failure. They are engineering regression tests, not linguistic accuracy measurements. Checkpoint loading uses `weights_only=True`, CPU mapping, checkpoint vocabularies and hidden size, strict state-dict loading and evaluation/inference mode.

## Deploy from an iPhone for ₦0

1. Sign in to [Render](https://dashboard.render.com/) using GitHub. Choose the free Hobby workspace option where offered.
2. Open [the Blueprint deployment link](https://render.com/deploy?repo=https://github.com/RegalInAllThings/Yoruba-Phonemizer). Authorize this repository and select its `main` branch. The tracked `render.yaml` declares **plan: free**. Review the displayed cost before creating the service; do not select a paid instance or add paid resources.
3. If Blueprint creation is unavailable in your account, choose **New → Web Service**, connect this repository, set runtime **Python 3**, build command `pip install -r requirements.txt`, start command `uvicorn app:app --host 0.0.0.0 --port $PORT --workers 1`, Python version environment variable `PYTHON_VERSION=3.12.8`, health check `/healthz`, and instance type **Free**.
4. Wait for a successful build and startup. Open the assigned `https://…onrender.com` URL in Safari. A successful build alone does not prove conversion works.
5. Visit `/healthz`; it must return `status: ok` and `engine: neural`. At the home page, choose **Yorùbá**, tap **Show phonemes**, and confirm `[j o_M r u_L b a_H]`. Check Copy result and the layout on your phone. Share the URL for an independent live check.

No ZIP extraction, laptop, custom domain, API key or database is needed. Render account creation and GitHub authorization must happen in your own browser; this repository does not contain Render credentials.

Render's [free-service documentation](https://render.com/docs/free) was checked during implementation: free web services sleep after 15 idle minutes, can take about a minute to wake, and share 750 free instance hours per workspace per month. Build and outbound traffic quotas also apply. Without a payment method, exceeding these quotas suspends services/builds rather than buying additional usage. Keep the default onrender.com address, avoid paid upgrades, and review your dashboard's current terms. Free hosting is feasible based on local CPU tests, but actual Render memory and build behavior still require a live deployment test. Local peak RSS was about 262 MiB for a loaded converter; it is not a guarantee of hosted peak memory.

## Verification boundaries

Local automated tests and real HTTP startup/conversion checks are recorded in `reports/launch_inference_audit.json` and `reports/launch_http_smoke.json`. No browser automation is available in the implementation environment, so visual rendering and clipboard interaction remain to be checked on a device. No live Render deployment has been claimed. Audio/text-to-speech is future work.

## Word-final nasal correction

`orthography.nasalize_from_spelling` converts an aligned terminal vowel + bare `n` to a nasal vowel only for standard nasal qualities /ã, ɛ̃, ĩ, ɔ̃, ũ/. In standard Yorùbá spelling, final unmarked n after these vowels marks nasalization. It does not globally merge V+n or invent nasal /e, o/. It requires the complete predicted vowel sequence to match the spelling in count, vowel quality and tone, and requires the final two output tokens to be the matching oral vowel and unmarked `n`. Existing nasal output is unchanged. Processing is per word, NFC/NFD and case independent; combining underdots are retained when reading vowel qualities. The neural phone vocabulary remains unchanged.

Examples: `ẹran` → `[ɛ_M r ã_M]`, `ọrùn` → `[ɔ_M r ũ_L]`, `ọ̀run` → `[ɔ_L r ũ_M]`. Consonantal n in `inú` and `aná`, tone-bearing syllabic nasals, and n across word boundaries are preserved. Medial/preconsonantal contexts are deliberately deferred because the old heuristic does not establish their lexical analysis. Loanword final consonants require lexical review; this is a bounded standard-orthography correction, not a complete phonological or morphological analyzer. It does not repair extra/missing neural vowels such as the current `iyán` output.

Both `/healthz` and conversion responses declare `postprocessing: word-final-nasal-v1`. The frontend discloses neural inference plus nasal correction. See `reports/nasalization_fix.json` for the reproduced public baseline and local corrected HTTP results. Public deployment is fixed only after Render redeploys and its endpoint returns the corrected sequence.
