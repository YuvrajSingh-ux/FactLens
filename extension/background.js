console.log("BACKGROUND SERVICE WORKER LOADED");
const SESSION_ID = "session_" + Date.now();
const BACKEND_URL = "https://sunbonneted-doretha-introvertedly.ngrok-free.dev/process_audio/";

function base64ToFloat32(base64) {
  const binary = atob(base64);
  const len = binary.length;
  const bytes = new Uint8Array(len);

  for (let i = 0; i < len; i++) {
    bytes[i] = binary.charCodeAt(i);
  }

  const int16 = new Int16Array(bytes.buffer);
  const float32 = new Float32Array(int16.length);

  for (let i = 0; i < int16.length; i++) {
    float32[i] = int16[i] / 32767;
  }

  return float32;
}



function float32ToWav(float32Array, sampleRate = 16000) {
  const buffer = new ArrayBuffer(44 + float32Array.length * 2);
  const view = new DataView(buffer);

  function writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }

  let offset = 0;

  writeString(view, offset, "RIFF"); offset += 4;
  view.setUint32(offset, 36 + float32Array.length * 2, true); offset += 4;
  writeString(view, offset, "WAVE"); offset += 4;

  writeString(view, offset, "fmt "); offset += 4;
  view.setUint32(offset, 16, true); offset += 4;
  view.setUint16(offset, 1, true); offset += 2;
  view.setUint16(offset, 1, true); offset += 2;
  view.setUint32(offset, sampleRate, true); offset += 4;
  view.setUint32(offset, sampleRate * 2, true); offset += 4;
  view.setUint16(offset, 2, true); offset += 2;
  view.setUint16(offset, 16, true); offset += 2;

  writeString(view, offset, "data"); offset += 4;
  view.setUint32(offset, float32Array.length * 2, true); offset += 4;

  let pos = offset;
  for (let i = 0; i < float32Array.length; i++, pos += 2) {
    let s = Math.max(-1, Math.min(1, float32Array[i]));
    view.setInt16(pos, s * 32767, true);
  }

  return buffer;
}


chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {

  (async () => {
    try {

      if (msg.action === "START_CAPTURE") {
        const [tab] = await chrome.tabs.query({
          active: true,
          currentWindow: true
        });

        chrome.tabs.sendMessage(tab.id, {
          action: "START_CAPTURE"
        });

        sendResponse({ status: "started" });
      }

      if (msg.action === "UPLOAD_PCM") {
        console.log("Receiving PCM");

        const float32 = base64ToFloat32(msg.chunk);
        const wavBuffer = float32ToWav(float32);

        const blob = new Blob([wavBuffer], { type: "audio/wav" });

        const formData = new FormData();
        formData.append("audio_file", blob, "audio.wav");
        formData.append("chunk_start_time", msg.video_time);
        formData.append("session_id", SESSION_ID);

        const res = await fetch(BACKEND_URL, {
          method: "POST",
          body: formData
        });

        const data = await res.json();

       
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
          if (tabs[0]?.id) {
            chrome.tabs.sendMessage(tabs[0].id, {
              action: "SHOW_RESULTS",
              data: data
            });
          }
        });

        console.log("Upload status:", res.status);
      }

      if (msg.action === "STOP_CAPTURE") {
        const [tab] = await chrome.tabs.query({
          active: true,
          currentWindow: true
        });

        chrome.tabs.sendMessage(tab.id, {
          action: "STOP_CAPTURE"
        });

        sendResponse({ status: "stopped" });
      }

    } catch (err) {
      console.error(err);
    }
  })();

  return true;
});