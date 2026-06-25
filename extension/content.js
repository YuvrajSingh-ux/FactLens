console.log("Content script loaded");


function waitForVideo() {
  return new Promise((resolve) => {
    const check = () => {
      const video = document.querySelector("video");
      if (video) resolve(video);
      else setTimeout(check, 500);
    };
    check();
  });
}

function createOverlay() {
  let container = document.getElementById("claim-overlay");

  if (container) return container;

  container = document.createElement("div");
  container.id = "claim-overlay";

  container.style.position = "fixed";
  container.style.top = "80px";
  container.style.right = "20px";
  container.style.width = "350px";
  container.style.maxHeight = "70vh";
  container.style.overflowY = "auto";
  container.style.background = "rgba(0,0,0,0.85)";
  container.style.color = "white";
  container.style.padding = "10px";
  container.style.borderRadius = "10px";
  container.style.zIndex = "999999";
  container.style.fontSize = "14px";

  container.innerHTML = `
    <div id="close-overlay" style="
        text-align:right;
        cursor:pointer;
        font-size:16px;
        margin-bottom:5px;
    ">❌</div>
    `;
  document.body.appendChild(container);

  container.querySelector("#close-overlay").onclick = () => {
    container.remove();
    };


  return container;
}

function displayResults(data) {
  const container = createOverlay();

  if (!data.claims || data.claims.length === 0) return;

  data.claims.forEach(claimObj => {

    const item = document.createElement("div");
    item.style.borderBottom = "1px solid #444";
    item.style.marginBottom = "10px";
    item.style.paddingBottom = "10px";

    const verdictColor = {
      SUPPORT: "#4CAF50",
      CONTRADICT: "#f44336",
      NEUTRAL: "#FFC107"
    };

    item.innerHTML = `
      <div style="font-weight:bold;">🧾 ${claimObj.claim}</div>

      <div style="margin-top:5px;">
        ⏱ ${claimObj.start_time.toFixed(1)}s
      </div>

      <div style="margin-top:5px; color:${verdictColor[claimObj.verification.verdict]}">
        ${claimObj.verification.verdict}
      </div>

      <div style="font-size:12px; margin-top:5px;">
        ${claimObj.verification.summary}
      </div>
    `;

    container.prepend(item); 
  });
}


function float32ToBase64(float32Arr) {
  const int16 = new Int16Array(float32Arr.length);

  for (let i = 0; i < float32Arr.length; i++) {
    let s = Math.max(-1, Math.min(1, float32Arr[i]));
    int16[i] = s * 32767;
  }

  let binary = "";
  const bytes = new Uint8Array(int16.buffer);

  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }

  return btoa(binary);
}

let processor = null;

chrome.runtime.onMessage.addListener((msg) => {

  if (msg.action === "START_CAPTURE") {
    console.log("START_CAPTURE received");

    (async () => {
      const video = await waitForVideo();

      console.log("✅ Video found");

      const audioContext = new AudioContext({ sampleRate: 16000 });
      await audioContext.resume();

      const source = audioContext.createMediaElementSource(video);

      processor = audioContext.createScriptProcessor(4096, 1, 1);

      source.connect(processor);

      source.connect(audioContext.destination);

      processor.connect(audioContext.destination);

      let buffer = [];

      processor.onaudioprocess = (e) => {
        const input = e.inputBuffer.getChannelData(0);

        const maxVal = Math.max(...input);
        console.log("Max audio level:", maxVal);

        buffer.push(...input);

        if (buffer.length > 16000 * 10) {
          const chunk = new Float32Array(buffer);
          buffer = [];

          const base64Audio = float32ToBase64(chunk);

          chrome.runtime.sendMessage({
            action: "UPLOAD_PCM",
            chunk: base64Audio,
            video_time: video.currentTime - 10  
            });

          console.log("🎤 Sent audio chunk");
        }
      };
    })();
  }

  if (msg.action === "STOP_CAPTURE") {
    console.log("STOP_CAPTURE");

    if (processor) {
      processor.disconnect();
      processor = null;
    }
  }
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {

  if (msg.action === "SHOW_RESULTS") {
    displayResults(msg.data);
  }

});