const state = {
  settings: {
    maintenance_mode: false,
    voice_auto_start: true,
    camera_enabled: true,
    mic_visualizer: false,
  },
  audioStarted: false,
  cameraStarted: false,
  voicePhase: "idle",
  lastBackendLevel: 0,
};

function $(selector) {
  return document.querySelector(selector);
}

function hasDesktopApi() {
  return window.pywebview && window.pywebview.api;
}

function updateDateTime() {
  const now = new Date();
  const timeElem = $(".time");
  const dateElem = $(".date");

  if (timeElem) timeElem.textContent = now.toLocaleTimeString();
  if (dateElem) {
    dateElem.textContent = `${now.getDate()} ${now.toLocaleString("default", { month: "short" })}`;
  }
}

async function callApi(method, ...args) {
  if (!hasDesktopApi() || !window.pywebview.api[method]) return null;
  return window.pywebview.api[method](...args);
}

async function notifyBackendStartArya() {
  const mic = await callApi("microphone_status");
  if (mic && mic.status !== "ok") {
    $("#assistantState").textContent = `Mic error: ${mic.message}`;
    await fetchAndRenderHistory();
    return;
  }

  const result = await callApi("start_arya");
  if (result) {
    $("#assistantState").textContent = "Listening...";
    await renderStatus();
  }
}

async function loadSettings() {
  const settings = await callApi("get_settings");
  if (settings) {
    state.settings = settings;
  }
  syncSettingsUi();
  const gemini = await callApi("get_gemini_status");
  if (gemini) {
    $("#geminiKeyStatus").textContent = gemini.configured
      ? `Configured (${gemini.model}) — enter a new key only to replace it.`
      : "Not configured — paste a key to enable Gemini.";
  }
}

function syncSettingsUi() {
  $("#maintenanceMode").checked = !!state.settings.maintenance_mode;
  $("#voiceAutoStart").checked = !!state.settings.voice_auto_start;
  $("#cameraEnabled").checked = !!state.settings.camera_enabled;
  $("#micVisualizer").checked = !!state.settings.mic_visualizer;
  document.body.classList.toggle("maintenance", !!state.settings.maintenance_mode);
  $("#modeLabel").textContent = state.settings.maintenance_mode ? "MAINTENANCE MODE" : "ACTIVE MODE";
}

async function saveSettings() {
  const nextSettings = {
    maintenance_mode: $("#maintenanceMode").checked,
    voice_auto_start: $("#voiceAutoStart").checked,
    camera_enabled: $("#cameraEnabled").checked,
    mic_visualizer: $("#micVisualizer").checked,
  };

  const result = await callApi("update_settings", nextSettings);
  if (result && result.settings) {
    state.settings = result.settings;
  } else {
    state.settings = nextSettings;
  }

  const apiKey = $("#geminiApiKey").value.trim();
  if (apiKey) {
    const geminiResult = await callApi("update_gemini_key", apiKey);
    if (geminiResult) {
      $("#geminiKeyStatus").textContent = geminiResult.message;
      if (geminiResult.success) $("#geminiApiKey").value = "";
    }
  }

  syncSettingsUi();
  $("#assistantState").textContent = "Settings applied";

  if (state.settings.camera_enabled && !state.cameraStarted) startCamera();
  if (state.settings.mic_visualizer && !state.audioStarted) {
    startMicVolume();
    startMicReactiveGlob();
  }
}

async function renderStatus() {
  const status = await callApi("system_status");
  if (!status) return;

  $("#cpuMetric").textContent = status.cpu === null ? "--%" : `${status.cpu}%`;
  $("#memoryMetric").textContent = status.memory === null ? "--%" : `${status.memory}%`;
  if (status.battery === null) {
    $("#batteryMetric").textContent = "--";
  } else {
    $("#batteryMetric").textContent = `${status.battery}%${status.plugged ? " AC" : ""}`;
  }

  applyVoiceStatus({
    running: status.voice_running,
    voice: status.voice,
  });

  document.body.classList.toggle("maintenance", !!status.maintenance_mode);
}

function applyVoiceStatus(status) {
  const voiceStatus = $("#voiceStatus");
  const voice = status.voice || {};
  const running = !!status.running;

  state.voicePhase = voice.phase || (running ? "listening" : "idle");
  state.lastBackendLevel = Number(voice.mic_level || 0);

  if (running) {
    const recognizing = state.voicePhase === "recognizing";
    const heard = state.voicePhase === "heard";
    voiceStatus.textContent = recognizing ? "Recognizing" : "Listening";
    voiceStatus.classList.add("online");
    $("#assistantState").textContent = voice.message || (recognizing ? "Recognizing..." : "Listening...");

    const level = state.lastBackendLevel || (heard ? 34 : listeningPulseLevel());
    setMicLevel(level);
  } else {
    voiceStatus.textContent = "Voice offline";
    voiceStatus.classList.remove("online");
    if (state.voicePhase === "error") {
      $("#assistantState").textContent = voice.message || "Voice stopped";
    }
    setMicLevel(0);
  }
}

async function pollVoiceStatus() {
  const status = await callApi("arya_status");
  if (!status) return;
  applyVoiceStatus(status);
}

function setMicLevel(level) {
  const safeLevel = Math.max(0, Math.min(100, Math.round(Number(level) || 0)));
  const fill = $(".volume-fill");
  const text = $(".volume-text");
  const bar = $(".volume-bar");

  if (fill) fill.style.width = `${safeLevel}%`;
  if (bar) bar.classList.toggle("listening", state.voicePhase === "listening");
  if (text) {
    text.textContent = state.voicePhase === "listening" && safeLevel < 8 ? "Listening" : `${safeLevel}%`;
  }

  updateGlobFromLevel(safeLevel);
}

function listeningPulseLevel() {
  const tick = Date.now() / 420;
  return Math.round(14 + Math.sin(tick) * 8);
}

function updateGlobFromLevel(level) {
  const glob = $(".glob");
  if (!glob) return;

  const scale = 1 + (level / 100) * 0.22;
  const glow = 28 + level * 0.8;
  glob.style.transform = `scale(${scale})`;
  glob.style.boxShadow = `0 0 ${glow}px rgba(96, 242, 161, 0.75), 0 0 ${glow * 1.7}px rgba(54, 199, 255, 0.28)`;
}

async function runQuickAction(action) {
  const result = await callApi("quick_action", action);
  if (result) {
    $("#assistantState").textContent = result.message || result.status;
    await fetchAndRenderHistory();
  }
}

async function submitTypedCommand(command) {
  const text = String(command || "").trim();
  if (!text) return;
  $("#assistantState").textContent = "Processing command...";
  const result = await callApi("submit_command", text);
  if (result) $("#assistantState").textContent = result.message || "Command complete";
  $("#commandInput").value = "";
  await fetchAndRenderHistory();
}

async function clearHistory() {
  await callApi("clear_history");
  await fetchAndRenderHistory();
  $("#assistantState").textContent = "History cleared";
}

async function startCamera() {
  if (!state.settings.camera_enabled || state.cameraStarted) return;

  try {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      $("#cameraState").textContent = "Unavailable";
      return;
    }

    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    const videoElement = $("#camera");
    if (videoElement) videoElement.srcObject = stream;
    state.cameraStarted = true;
    $("#cameraState").textContent = "Online";
  } catch (error) {
    $("#cameraState").textContent = "Blocked";
    console.error("Camera access denied:", error);
  }
}

async function startMicVolume() {
  if (!state.settings.mic_visualizer || state.audioStarted) return;

  try {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      $(".volume-text").textContent = "Unavailable";
      return;
    }

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    if (audioContext.state === "suspended") {
      try {
        await audioContext.resume();
      } catch (error) {
        console.warn("Audio context resume failed:", error);
      }
    }

    const source = audioContext.createMediaStreamSource(stream);
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 512;
    source.connect(analyser);

    const dataArray = new Uint8Array(analyser.fftSize);
    state.audioStarted = true;

    function updateVolume() {
      analyser.getByteTimeDomainData(dataArray);
      let sumSquares = 0;

      for (let i = 0; i < dataArray.length; i += 1) {
        const value = (dataArray[i] - 128) / 128;
        sumSquares += value * value;
      }

      const rms = Math.sqrt(sumSquares / dataArray.length);
      const level = Math.min(100, Math.round((rms / 0.7) * 100));
      const fill = $(".volume-fill");
      const text = $(".volume-text");

      if (fill) fill.style.width = `${level}%`;
      if (text) text.textContent = `${level}%`;

      requestAnimationFrame(updateVolume);
    }

    updateVolume();
  } catch (error) {
    $(".volume-text").textContent = state.voicePhase === "listening" ? "Listening" : "Blocked";
    console.error("Microphone access denied:", error);
  }
}

async function startMicReactiveGlob() {
  if (!state.settings.mic_visualizer) return;

  try {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return;

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioContext.createMediaStreamSource(stream);
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);

    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    const glob = $(".glob");

    function updateGlob() {
      analyser.getByteFrequencyData(dataArray);
      let sum = 0;

      for (let i = 0; i < dataArray.length; i += 1) sum += dataArray[i];

      const average = sum / dataArray.length;
      const scale = 1 + (average / 255) * 0.34;
      const colorIntensity = Math.min(255, Math.round(average * 1.4));
      const color = `rgb(${colorIntensity}, 242, 220)`;

      if (glob) {
        glob.style.transform = `scale(${scale})`;
        glob.style.boxShadow = `0 0 ${26 + colorIntensity / 5}px ${color}, 0 0 ${70 + colorIntensity / 3}px rgba(104, 230, 111, 0.35)`;
      }

      requestAnimationFrame(updateGlob);
    }

    updateGlob();
  } catch (error) {
    console.error("Reactive core microphone access denied:", error);
  }
}

async function fetchAndRenderHistory() {
  try {
    const data = await callApi("get_history");
    if (!data) return;

    const history = data.history || [];
    const container = $("#historyPanel");
    if (!container) return;

    container.innerHTML = "";
    if (history.length === 0) {
      container.innerHTML = '<span class="history">Search history will appear here...</span>';
      return;
    }

    const list = document.createElement("div");
    list.className = "history-list";

    history.slice().reverse().forEach((item) => {
      const el = document.createElement("div");
      el.className = "history-item";
      const t = new Date((item.ts || Date.now()) * 1000);
      el.innerHTML = `<div class="history-command">${escapeHtml(item.command)}</div><div class="history-meta">${escapeHtml(item.source || "arya")} - ${t.toLocaleTimeString()}</div>`;
      list.appendChild(el);
    });

    container.appendChild(list);
  } catch (error) {
    console.warn("History render failed:", error);
  }
}

function escapeHtml(value) {
  if (!value) return "";
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[char]));
}

function openSettings(open = true) {
  const drawer = $("#settingsDrawer");
  drawer.classList.toggle("open", open);
  drawer.setAttribute("aria-hidden", open ? "false" : "true");
}

function bindEvents() {
  $("#settingsToggle").addEventListener("click", () => openSettings(true));
  $("#closeSettings").addEventListener("click", () => openSettings(false));
  $("#maintenanceShortcut").addEventListener("click", () => openSettings(true));
  $("#historyShortcut").addEventListener("click", () => $("#historyPanel").scrollIntoView({ behavior: "smooth" }));
  $("#saveSettings").addEventListener("click", saveSettings);
  $("#startArya").addEventListener("click", notifyBackendStartArya);
  $("#clearHistory").addEventListener("click", clearHistory);
  $("#commandForm").addEventListener("submit", (event) => {
    event.preventDefault();
    submitTypedCommand($("#commandInput").value);
  });
  $("#refreshStatus").addEventListener("click", renderStatus);
  $("#diagnosticsButton").addEventListener("click", async () => {
    await renderStatus();
    const mic = await callApi("microphone_status");
    $("#assistantState").textContent = mic ? mic.message : "Diagnostics refreshed";
    await fetchAndRenderHistory();
  });

  document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", () => runQuickAction(button.dataset.action));
  });

  $("#maintenanceMode").addEventListener("change", () => {
    document.body.classList.toggle("maintenance", $("#maintenanceMode").checked);
    $("#modeLabel").textContent = $("#maintenanceMode").checked ? "MAINTENANCE MODE" : "ACTIVE MODE";
  });

  $("#micVisualizer").addEventListener("change", () => {
    state.settings.mic_visualizer = $("#micVisualizer").checked;
    if (state.settings.mic_visualizer) startMicVolume();
  });
}

let appInitialized = false;

async function initializeApp() {
  if (appInitialized) return;
  appInitialized = true;
  updateDateTime();
  setInterval(updateDateTime, 1000);
  bindEvents();

  const splash = $("#splash");
  const shell = $(".app-shell");
  if (shell) shell.classList.add("blurred");

  await loadSettings();
  await renderStatus();
  await fetchAndRenderHistory();

  setTimeout(async () => {
    if (splash) splash.style.display = "none";
    if (shell) shell.classList.remove("blurred");

    if (state.settings.voice_auto_start) await notifyBackendStartArya();
    if (state.settings.camera_enabled) startCamera();
    if (state.settings.mic_visualizer) {
      startMicVolume();
      startMicReactiveGlob();
    }
  }, 2200);

  setInterval(fetchAndRenderHistory, 1000);
  setInterval(renderStatus, 4000);
  setInterval(pollVoiceStatus, 220);
  setInterval(() => {
    if (state.voicePhase === "listening") {
      setMicLevel(state.lastBackendLevel || listeningPulseLevel());
    }
  }, 180);
}

// pywebview injects window.pywebview.api asynchronously. Wait for its ready event
// so startup settings and voice controls always reach the Python backend.
window.addEventListener("pywebviewready", initializeApp);
document.addEventListener("DOMContentLoaded", () => {
  if (hasDesktopApi()) initializeApp();
});
