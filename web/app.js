const form = document.querySelector('#convert-form');
const text = document.querySelector('#text');
const output = document.querySelector('#output');
const message = document.querySelector('#message');
const submit = document.querySelector('#convert');
const copy = document.querySelector('#copy');
let result = '';
function changed() {
  document.querySelector('#count').textContent = `${text.value.length} / 500`;
  result = ''; copy.disabled = true;
  output.textContent = 'Your phonemes will appear here.';
  message.textContent = '';
}
text.addEventListener('input', changed);
// History stays on this browser; only the current conversion is sent to the API.
const HISTORY_KEY = 'yoruba-phonemizer.recent.v1';
const recent = document.querySelector('#recent');
const historyItems = document.querySelector('#history-items');
const clearHistory = document.querySelector('#clear-history');
const historyKey = value => value.trim().normalize('NFC').toLowerCase();
function validHistory(values) {
  if (!Array.isArray(values)) return [];
  const seen = new Set();
  return values.filter(value => {
    if (typeof value !== 'string' || !value.trim() || value.length > 500) return false;
    const key = historyKey(value);
    if (seen.has(key)) return false;
    seen.add(key); return true;
  }).slice(0, 4);
}
let history = [];
try { history = validHistory(JSON.parse(localStorage.getItem(HISTORY_KEY))); }
catch { /* Unavailable or invalid storage: retain working in-memory history. */ }
function renderHistory() {
  historyItems.replaceChildren();
  recent.hidden = history.length === 0;
  for (const value of history) {
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'history-entry';
    button.textContent = value; button.title = value; button.disabled = text.disabled;
    button.addEventListener('click', () => {
      text.value = value; changed(); text.focus();
    });
    historyItems.append(button);
  }
}
function remember(value) {
  history = validHistory([value.trim(), ...history]);
  try { localStorage.setItem(HISTORY_KEY, JSON.stringify(history)); }
  catch { /* Conversion still succeeds if storage is blocked or full. */ }
  renderHistory();
}
clearHistory.addEventListener('click', () => {
  history = [];
  try { localStorage.removeItem(HISTORY_KEY); } catch { /* Clear this session. */ }
  renderHistory(); text.focus();
});
renderHistory();
form.addEventListener('submit', async event => {
  event.preventDefault();
  result = ''; copy.disabled = true; submit.disabled = true; text.disabled = true;
  historyItems.querySelectorAll('button').forEach(b => b.disabled = true);
  const submittedText = text.value;
  output.textContent = 'Converting…'; message.textContent = '';
  try {
    const response = await fetch('/api/phonemize', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text: submittedText}), signal: AbortSignal.timeout(90000)
    });
    const data = await response.json();
    if (!response.ok) throw Error(response.status >= 500 ? 'Conversion is temporarily unavailable. Please try again shortly.' : typeof data.detail === 'string' ? data.detail : 'Enter 1–500 characters of Yorùbá text.');
    if (typeof data.phonemes !== 'string' || !data.phonemes.trim()) throw Error('No conversion was returned. Please try again.');
    remember(submittedText);
    result = data.phonemes; output.textContent = result; copy.disabled = false;
  } catch (error) {
    output.textContent = 'Conversion unavailable.';
    message.textContent = error.name === 'TimeoutError' ? 'The service is taking time to wake up. Please try again shortly.' : error.message;
  } finally {
    submit.disabled = false; text.disabled = false;
    historyItems.querySelectorAll('button').forEach(b => b.disabled = false);
  }
});
copy.addEventListener('click', async () => {
  try { await navigator.clipboard.writeText(result); message.textContent = 'Phonemes copied.'; }
  catch { message.textContent = 'Select and copy the phoneme sequence above.'; }
});
