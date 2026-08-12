// ─────────────────────── Navigation ───────────────────────
const views = ["home", "mandi", "yojana", "chat", "profile"];

function goTo(view) {
  views.forEach(v => {
    document.getElementById(`view-${v}`).classList.toggle("active", v === view);
  });
  document.querySelectorAll(".nav-link").forEach(el => {
    el.classList.toggle("active", el.dataset.nav === view);
  });
  document.querySelectorAll(".bottomnav-item").forEach(el => {
    el.classList.toggle("active", el.dataset.nav === view);
  });
  window.scrollTo({ top: 0, behavior: "instant" });
}

document.querySelectorAll("[data-nav]").forEach(el => {
  el.addEventListener("click", (e) => {
    e.preventDefault();
    goTo(el.dataset.nav);
  });
});

// ─────────────────────── Quick-suggestion buttons ───────────────────────
document.querySelectorAll(".quick-card").forEach(btn => {
  btn.addEventListener("click", () => {
    goTo("chat");
    sendQuestion(btn.textContent.trim());
  });
});

// ─────────────────────── Yojana finder form ───────────────────────
document.getElementById("finder-submit").addEventListener("click", () => {
  const state = document.getElementById("finder-state").value;
  const crop = document.getElementById("finder-crop").value;
  let question = "Which government schemes am I eligible for as a farmer";
  if (crop) question += ` growing ${crop}`;
  if (state) question += ` in ${state}`;
  question += "?";
  goTo("chat");
  sendQuestion(question);
});

// ─────────────────────── Chat state ───────────────────────
const chatLog = document.getElementById("chat-log");
const chatEmpty = document.getElementById("chat-empty");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");

document.getElementById("clear-chat").addEventListener("click", () => {
  chatLog.querySelectorAll(".msg").forEach(el => el.remove());
  chatEmpty.style.display = "block";
});

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = chatInput.value.trim();
  if (!text) return;
  chatInput.value = "";
  sendQuestion(text);
});

function escapeHtml(str) {
  const d = document.createElement("div");
  d.textContent = str;
  return d.innerHTML;
}

// Very small markdown-ish formatter: **bold** and line breaks
function formatAnswer(text) {
  if (!text) return "";
  let safe = escapeHtml(text);
  safe = safe.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  safe = safe.replace(/\n/g, "<br>");
  return safe;
}

function addUserMessage(text) {
  chatEmpty.style.display = "none";
  const el = document.createElement("div");
  el.className = "msg msg-user";
  el.innerHTML = `<div class="msg-bubble">${escapeHtml(text)}</div>`;
  chatLog.appendChild(el);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function addTypingIndicator() {
  const el = document.createElement("div");
  el.className = "msg msg-assistant";
  el.id = "typing-indicator";
  el.innerHTML = `<div class="msg-bubble"><div class="typing-dots"><span></span><span></span><span></span></div></div>`;
  chatLog.appendChild(el);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function removeTypingIndicator() {
  const el = document.getElementById("typing-indicator");
  if (el) el.remove();
}

let chartCounter = 0;

function renderAssistantMessage(data) {
  const { routed_to, badge, answer_text, response } = data;
  const wrap = document.createElement("div");
  wrap.className = "msg msg-assistant";

  const chipClass = routed_to === "price_agent" ? "price" : "scheme";
  const chipIcon = routed_to === "price_agent" ? "📈" : "📋";

  let bubbleInner = `<span class="chip ${chipClass}">${chipIcon} ${badge}</span>`;

  if (routed_to === "price_agent") {
    bubbleInner += renderPriceContent(response, answer_text);
  } else {
    bubbleInner += `<div class="scheme-card">${formatAnswer(answer_text)}</div>`;
    bubbleInner += `<div class="disclaimer-box">⚠️ This answer is a guide based on the retrieved scheme rules, not a final verification. Please confirm your eligibility with your local Common Service Centre (CSC) or bank branch before applying.</div>`;
    if (response.retrieved_chunks && response.retrieved_chunks.length) {
      const sourcesId = `sources-${++chartCounter}`;
      bubbleInner += `<button class="details-toggle" data-target="${sourcesId}">📄 Source documents used</button>`;
      bubbleInner += `<div class="details-panel" id="${sourcesId}">`;
      response.retrieved_chunks.forEach((chunk, i) => {
        bubbleInner += `<div class="source-chunk"><div class="source-chunk-title">Source ${i + 1}</div>${escapeHtml(chunk.trim())}</div>`;
      });
      bubbleInner += `</div>`;
    }
  }

  wrap.innerHTML = `<div class="msg-bubble">${bubbleInner}</div>`;
  chatLog.appendChild(wrap);
  chatLog.scrollTop = chatLog.scrollHeight;

  // Plot any charts now that the elements exist in the DOM
  if (routed_to === "price_agent") {
    plotFiguresFor(wrap, response);
  }
}

function renderPriceContent(response, answerText) {
  let html = "";

  if (response.error) {
    html += `<p>⚠️ Query error: ${escapeHtml(response.error)}</p>`;
    return html;
  }

  const singleValue = response.result && response.result.length === 1 && response.columns.length === 1;

  if (singleValue) {
    const col = response.columns[0];
    const val = response.result[0][col];
    const isMissing = val === null || val === undefined || (typeof val === "number" && Number.isNaN(val));
    const displayVal = isMissing
      ? "No data found"
      : (typeof val === "number" ? `₹${val.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : `₹${val}`);
    let deltaHtml = "";
    if (isMissing) {
      html += `<div class="price-tile">
        <div class="price-tile-icon">🔍</div>
        <div>
          <div class="price-tile-label">Price / quintal</div>
          <div class="price-tile-value" style="font-size:1.15rem;">No matching records for this query</div>
        </div>
      </div>`;
      return html;
    }
    if (response.percent_change !== null && response.percent_change !== undefined) {
      const pct = response.percent_change;
      if (pct > 0) deltaHtml = `<div class="delta-pill up">▲ ${pct.toFixed(1)}% over recent records</div>`;
      else if (pct < 0) deltaHtml = `<div class="delta-pill down">▼ ${Math.abs(pct).toFixed(1)}% over recent records</div>`;
    }
    html += `<div class="price-tile">
      <div class="price-tile-icon">💰</div>
      <div>
        <div class="price-tile-label">Price / quintal</div>
        <div class="price-tile-value">${displayVal}</div>
        ${deltaHtml}
      </div>
    </div>`;
  } else if (answerText) {
    html += `<p>${formatAnswer(answerText)}</p>`;
  }

  const figureKeys = [];
  if (response.figure) figureKeys.push("figure");
  if (response.context_chart) figureKeys.push("context_chart");
  figureKeys.forEach(key => {
    const id = `chart-${++chartCounter}`;
    html += `<div class="chart-box"><div id="${id}" class="plotly-target" data-figkey="${key}"></div></div>`;
  });

  if (response.query) {
    const detailsId = `details-${++chartCounter}`;
    html += `<button class="details-toggle" data-target="${detailsId}">📊 Query details</button>`;
    html += `<div class="details-panel" id="${detailsId}">`;
    html += `<div class="sql-box">${escapeHtml(response.query)}</div>`;
    if (response.explanation) html += `<p style="margin-bottom:0.5rem;">💡 ${escapeHtml(response.explanation)}</p>`;
    if (response.result && response.result.length) {
      html += `<table class="data-table"><thead><tr>${response.columns.map(c => `<th>${escapeHtml(c)}</th>`).join("")}</tr></thead><tbody>`;
      response.result.slice(0, 15).forEach(row => {
        html += `<tr>${response.columns.map(c => `<td>${escapeHtml(String(row[c]))}</td>`).join("")}</tr>`;
      });
      html += `</tbody></table>`;
    }
    html += `</div>`;
  }

  return html;
}

function plotFiguresFor(container, response) {
  container.querySelectorAll(".plotly-target").forEach(target => {
    const key = target.dataset.figkey;
    const fig = response[key];
    if (!fig) return;
    const layout = Object.assign({}, fig.layout, {
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      font: { color: "#5C6B57", family: "Inter, sans-serif", size: 12 },
      margin: { l: 50, r: 20, t: 36, b: 44 },
      xaxis: Object.assign({}, fig.layout.xaxis, { gridcolor: "rgba(34,48,31,0.08)" }),
      yaxis: Object.assign({}, fig.layout.yaxis, { gridcolor: "rgba(34,48,31,0.08)" }),
    });
    const data = fig.data.map(trace => {
      const t = Object.assign({}, trace);
      if (t.type === "scatter") { t.line = Object.assign({}, t.line, { color: "#3F6B3F" }); t.marker = Object.assign({}, t.marker, { color: "#3F6B3F" }); }
      if (t.type === "bar") { t.marker = Object.assign({}, t.marker, { color: "#F0932B" }); }
      return t;
    });
    Plotly.newPlot(target.id, data, layout, { displayModeBar: false, responsive: true });
  });
}

// Expand/collapse details panels (event delegation)
chatLog.addEventListener("click", (e) => {
  if (e.target.classList.contains("details-toggle")) {
    const panel = document.getElementById(e.target.dataset.target);
    if (panel) panel.classList.toggle("open");
  }
});

// ─────────────────────── Sending a question ───────────────────────
async function sendQuestion(text) {
  addUserMessage(text);
  addTypingIndicator();
  document.getElementById("send-btn").disabled = true;

  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: text }),
    });
    if (!res.ok) throw new Error(`Server error ${res.status}`);
    const data = await res.json();
    removeTypingIndicator();
    renderAssistantMessage(data);
  } catch (err) {
    removeTypingIndicator();
    const el = document.createElement("div");
    el.className = "msg msg-assistant";
    el.innerHTML = `<div class="msg-bubble">⚠️ Something went wrong reaching the server: ${escapeHtml(err.message)}. Make sure the backend (uvicorn) is running.</div>`;
    chatLog.appendChild(el);
  } finally {
    document.getElementById("send-btn").disabled = false;
  }
}

// ─────────────────────── Voice input (Web Speech API) ───────────────────────
// Uses the browser's built-in speech recognition instead of recording audio
// and sending it to a backend transcription endpoint — no server round-trip,
// no API quota, no WAV encoding. Only needs `mic-btn`, `.recording`, and
// `chatInput` to already exist, same as before.
const micBtn = document.getElementById("mic-btn");
let recognition = null;
let isRecording = false;
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

micBtn.addEventListener("click", () => {
  if (!SpeechRecognition) {
    showSystemNotice("Voice input isn't supported in this browser. Please type your question, or try Chrome/Edge.");
    return;
  }
  if (isRecording) {
    recognition.stop();
    return;
  }

  recognition = new SpeechRecognition();
  recognition.lang = "hi-IN"; // swap to "en-IN" or wire to your language selector
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    isRecording = true;
    micBtn.classList.add("recording");
    chatInput.placeholder = "सुन रहा हूँ... / Listening...";
  };

  recognition.onresult = (event) => {
    sendQuestion(event.results[0][0].transcript);
  };

  recognition.onerror = (event) => {
    if (event.error !== "aborted") {
      showSystemNotice("Couldn't hear that clearly. Please try again, or type your question.");
    }
  };

  recognition.onend = () => {
    isRecording = false;
    micBtn.classList.remove("recording");
    chatInput.placeholder = "पूछें / Ask your question...";
  };

  recognition.start();
});

function showSystemNotice(text) {
  chatEmpty.style.display = "none";
  const el = document.createElement("div");
  el.className = "msg msg-assistant";
  el.innerHTML = `<div class="msg-bubble">🎤 ${escapeHtml(text)}</div>`;
  chatLog.appendChild(el);
  chatLog.scrollTop = chatLog.scrollHeight;
}