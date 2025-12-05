// static/js/voice.js

// --- 1. Audio Feedback (Beeps) ---
// We use the Web Audio API to generate simple, clean beeps without external MP3 files.
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

function playTone(freq, duration, type = "sine") {
  if (audioCtx.state === "suspended") audioCtx.resume();
  
  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();
  
  osc.type = type;
  osc.frequency.value = freq;
  
  // Fade out to avoid clicking sound
  gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
  
  osc.connect(gain);
  gain.connect(audioCtx.destination);
  
  osc.start();
  osc.stop(audioCtx.currentTime + duration);
}

export function playMicStart() {
  playTone(880, 0.1); // High pitch "Ding"
}

export function playMicStop() {
  playTone(440, 0.1); // Lower pitch "Dong"
}

// --- 2. Text-to-Speech (TTS) ---
export function speakText(text) {
  if (!window.speechSynthesis) return;

  const synth = window.speechSynthesis;
  synth.cancel(); // Stop any previous speech immediately

  const utter = new SpeechSynthesisUtterance(text);
  
  // Try to pick a pleasant voice (Prioritize Google US English or standard Male)
  const voices = synth.getVoices();
  const preferredVoice = voices.find(v => 
    v.name.includes("Google US English") || 
    v.name.includes("Male") || 
    v.lang === "en-US"
  );

  if (preferredVoice) utter.voice = preferredVoice;

  utter.rate = 1;   // Normal speed
  utter.pitch = 1;  // Normal pitch
  
  synth.speak(utter);
}

// --- 3. Speech-to-Text (STT) ---
export function startVoiceInput() {
  return new Promise((resolve, reject) => {
    // Browser compatibility check
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Your browser does not support voice input. Please use Chrome.");
      return reject("No Browser Support");
    }

    const recog = new SpeechRecognition();
    recog.lang = "en-US";
    recog.interimResults = false; // We only want the final result
    recog.maxAlternatives = 1;

    // Play sound when logic starts
    playMicStart();

    recog.onresult = (event) => {
      const text = event.results[0][0].transcript;
      resolve(text);
    };

    recog.onerror = (err) => {
      playMicStop(); // Error sound
      reject(err);
    };

    recog.onend = () => {
      playMicStop(); // End sound
    };

    recog.start();
  });
}