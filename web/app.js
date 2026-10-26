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
document.querySelectorAll('[data-example]').forEach(button => button.addEventListener('click', () => {
  text.value = button.dataset.example; changed(); text.focus();
}));
async function health() {
  const badge = document.querySelector('#model-status');
  try {
    const response = await fetch('/healthz', {signal: AbortSignal.timeout(90000)});
    if (!response.ok) throw Error();
    badge.textContent = 'Neural model ready';
  } catch { badge.textContent = 'Model unavailable · retry shortly'; }
}
health();
form.addEventListener('submit', async event => {
  event.preventDefault();
  result = ''; copy.disabled = true; submit.disabled = true; text.disabled = true;
  document.querySelectorAll('[data-example]').forEach(b => b.disabled = true);
  output.textContent = 'Converting…'; message.textContent = '';
  try {
    const response = await fetch('/api/phonemize', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text: text.value}), signal: AbortSignal.timeout(90000)
    });
    const data = await response.json();
    if (!response.ok) throw Error(typeof data.detail === 'string' ? data.detail : 'Enter 1–500 characters of Yorùbá text.');
    result = data.phonemes; output.textContent = result; copy.disabled = false;
    document.querySelector('#model-status').textContent = 'Neural model ready';
  } catch (error) {
    output.textContent = 'Conversion unavailable.';
    message.textContent = error.name === 'TimeoutError' ? 'The service is taking time to wake up. Please try again shortly.' : error.message;
  } finally {
    submit.disabled = false; text.disabled = false;
    document.querySelectorAll('[data-example]').forEach(b => b.disabled = false);
  }
});
copy.addEventListener('click', async () => {
  try { await navigator.clipboard.writeText(result); message.textContent = 'Phonemes copied.'; }
  catch { message.textContent = 'Select and copy the phoneme sequence above.'; }
});
