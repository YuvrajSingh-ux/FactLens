document.getElementById("startBtn").addEventListener("click", () => {
  chrome.runtime.sendMessage({ action: "START_CAPTURE" }, (res) => {
    console.log("Offscreen replied:", res);
  });
});

document.getElementById("stopBtn").addEventListener("click", () => {
  chrome.runtime.sendMessage({ action: "STOP_CAPTURE" }, (res) => {
    console.log("Offscreen replied:", res);
  });
});
