const frame = document.getElementById('call-frame');
const callButton = document.getElementById('call-button');
const statusText = document.getElementById('status-text');

let timerInterval;
let seconds = 0;

function startCallTimer() {
  timerInterval = setInterval(() => {
    seconds++;
    const min = String(Math.floor(seconds / 60)).padStart(2, '0');
    const sec = String(seconds % 60).padStart(2, '0');
    statusText.textContent = `${min}:${sec}`;
  }, 1000);
}

// NOTE: The Twilio voice integration was removed. The call button below is a
// placeholder UI only — wire a new call provider into makeCall()/endCall() to
// restore actual calling. The red/green button states are kept because the
// server-side Selenium flow (website_handler.py) watches them to detect call
// start/end.
async function makeCall() {
  console.warn("Call provider not configured — placeholder only. selectedPhoneNumber:", window.selectedPhoneNumber);
  updateUIForCallInProgress();
}

function endCall() {
  updateUIForEndedCall();
}

// UI update functions
function updateUICallReady() {
  clearInterval(timerInterval);
  seconds = 0;
  statusText.textContent = '';
  callButton.classList.remove('bg-red-500', 'hover:bg-red-600');
  callButton.classList.add('bg-green-500', 'hover:bg-green-600');
  callButton.innerHTML = `
    <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
      <path d="M6.62 10.79a15.053 15.053 0 006.59 6.59l2.2-2.2a1 1 0 011.11-.27c1.2.48 2.53.73 3.88.73a1 1 0 011 1V20a1 1 0 01-1 1C10.4 21 3 13.6 3 5a1 1 0 011-1h3.5a1 1 0 011 1c0 1.35.25 2.68.73 3.88.13.28.07.6-.27 1.11l-2.34 2.34z"/>
    </svg>
  `;
}

function updateUIForCallInProgress() {
  callButton.classList.remove('bg-green-500', 'hover:bg-green-600');
  callButton.classList.add('bg-red-500', 'hover:bg-red-600');
  callButton.innerHTML = `
    <svg class="w-6 h-6 [transform:rotate(140deg)]" fill="currentColor" viewBox="0 0 24 24">
        <path d="M6.62 10.79a15.053 15.053 0 006.59 6.59l2.2-2.2a1 1 0 011.11-.27c1.2.48 2.53.73 3.88.73a1 1 0 011 1V20a1 1 0 01-1 1C10.4 21 3 13.6 3 5a1 1 0 011-1h3.5a1 1 0 011 1c0 1.35.25 2.68.73 3.88.13.28.07.6-.27 1.11l-2.34 2.34z"/>
    </svg>
  `;
  statusText.textContent = '接続中...';
  startCallTimer();
}

function updateUIForEndedCall() {
  clearInterval(timerInterval);
  seconds = 0;
  statusText.textContent = '';
  callButton.classList.remove('bg-red-500', 'hover:bg-red-600');
  callButton.classList.add('bg-green-500', 'hover:bg-green-600');
  callButton.innerHTML = `
    <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
      <path d="M6.62 10.79a15.053 15.053 0 006.59 6.59l2.2-2.2a1 1 0 011.11-.27c1.2.48 2.53.73 3.88.73a1 1 0 011 1V20a1 1 0 01-1 1C10.4 21 3 13.6 3 5a1 1 0 011-1h3.5a1 1 0 011 1c0 1.35.25 2.68.73 3.88.13.28.07.6-.27 1.11l-2.34 2.34z"/>
    </svg>
  `;
}

// Event listeners
callButton.addEventListener('click', () => {
  if (callButton.classList.contains('bg-green-500')) {
    makeCall();
  } else {
    endCall();
  }
});
