const POLL_INTERVAL_MS = 2000;

let selectedSourceId = null;
let pollTimer = null;

const $ = (sel) => document.querySelector(sel);

const sourceForm = $("#source-form");
const sourceNameInput = $("#source-name");
const sourcePathInput = $("#source-path");
const browseBtn = $("#browse-btn");
const formError = $("#form-error");
const sourceList = $("#source-list");
const viewerEmpty = $("#viewer-empty");
const viewer = $("#viewer");
const viewerTitle = $("#viewer-title");
const viewerPath = $("#viewer-path");
const lineCountSelect = $("#line-count");
const autoRefreshCheckbox = $("#auto-refresh");
const followToggle = $("#follow-toggle");
const refreshBtn = $("#refresh-btn");
const highlightEnabled = $("#highlight-enabled");
const highlightPattern = $("#highlight-pattern");
const highlightCaseSensitive = $("#highlight-case-sensitive");
const matchNav = $("#match-nav");
const matchPrev = $("#match-prev");
const matchNext = $("#match-next");
const matchStatus = $("#match-status");
const logOutput = $("#log-output");
const appVersion = $("#app-version");

let currentMatch = null;
let followTail = true;
let fetchGeneration = 0;
let suppressScrollFollow = false;
let suppressScrollToken = 0;
let wasScrolledUp = false;

async function loadVersion() {
  try {
    const data = await api("/api/version");
    appVersion.textContent = `v${data.version}`;
    appVersion.hidden = false;
  } catch {
    appVersion.hidden = true;
  }
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `Request failed (${res.status})`);
  }
  return data;
}

function showFormError(message) {
  formError.textContent = message;
  formError.hidden = !message;
}

function nameFromPath(filePath) {
  const fileName = filePath.split(/[\\/]/).pop() || "";
  const stem = fileName.replace(/\.[^.]+$/, "");
  if (!stem) return "";
  return stem.replace(/[-_]+/g, " ").trim();
}

async function browseForFile() {
  showFormError("");
  browseBtn.disabled = true;
  browseBtn.title = "Opening file picker...";

  try {
    const result = await api("/api/pick-file", { method: "POST" });
    if (!result?.path) return;

    sourcePathInput.value = result.path;
    if (!sourceNameInput.value.trim()) {
      sourceNameInput.value = nameFromPath(result.path);
    }
  } catch (err) {
    showFormError(err.message);
  } finally {
    browseBtn.disabled = false;
    browseBtn.title = "Browse for file";
  }
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function getHighlightClass(line) {
  if (!highlightEnabled.checked) return "";
  const pattern = highlightPattern.value.trim();
  if (!pattern) return "";

  const haystack = highlightCaseSensitive.checked ? line : line.toLowerCase();
  const needle = highlightCaseSensitive.checked ? pattern : pattern.toLowerCase();
  if (!haystack.includes(needle)) return "";

  const upper = pattern.toUpperCase();
  if (upper === "WARN" || upper === "WARNING") return "highlight-warn";
  return "highlight-error";
}

function getMatchLines() {
  return [...logOutput.querySelectorAll(".log-line.highlight-error, .log-line.highlight-warn")];
}

function matchKey(matches, index) {
  const text = matches[index].textContent;
  let occurrence = 0;
  for (let i = 0; i < index; i += 1) {
    if (matches[i].textContent === text) occurrence += 1;
  }
  return { text, occurrence };
}

function findMatchIndex(matches, saved) {
  if (!saved) return null;
  let seen = 0;
  for (let i = 0; i < matches.length; i += 1) {
    if (matches[i].textContent !== saved.text) continue;
    if (seen === saved.occurrence) return i;
    seen += 1;
  }
  return null;
}

function formatMatchStatus(total, currentIndex) {
  if (currentIndex == null) {
    return total === 1 ? "1 match" : `${total} matches`;
  }
  return `${currentIndex + 1} / ${total}`;
}

function syncPresetButtons() {
  const pattern = highlightPattern.value.trim();
  const highlighting = highlightEnabled.checked && pattern.length > 0;
  document.querySelectorAll(".preset").forEach((btn) => {
    const preset = btn.dataset.pattern || "";
    const matches = highlightCaseSensitive.checked
      ? pattern === preset
      : pattern.toLowerCase() === preset.toLowerCase();
    const active = highlighting && matches;
    btn.classList.toggle("is-active", active);
    btn.setAttribute("aria-pressed", active ? "true" : "false");
  });
}

function updateMatchNavigator() {
  syncPresetButtons();
  const active = highlightEnabled.checked && highlightPattern.value.trim();
  matchNav.hidden = !active;
  if (!active) {
    currentMatch = null;
    return;
  }

  const matches = getMatchLines();
  const total = matches.length;
  let currentIndex = findMatchIndex(matches, currentMatch);
  if (currentMatch && currentIndex == null) {
    currentMatch = null;
    currentIndex = null;
  }

  matches.forEach((el, index) => {
    el.classList.toggle("highlight-current", index === currentIndex);
  });

  matchStatus.textContent = formatMatchStatus(total, currentIndex);
  const canStep = total >= 1;
  matchPrev.disabled = !canStep;
  matchNext.disabled = !canStep;
}

function beginSuppressScroll() {
  suppressScrollToken += 1;
  suppressScrollFollow = true;
  return suppressScrollToken;
}

function endSuppressScroll(token) {
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      if (suppressScrollToken === token) suppressScrollFollow = false;
    });
  });
}

function setLogScroll(next) {
  const token = beginSuppressScroll();
  logOutput.scrollTop = next;
  endSuppressScroll(token);
}

function scrollLineIntoLog(el) {
  const pane = logOutput.getBoundingClientRect();
  const line = el.getBoundingClientRect();
  const delta = line.top - pane.top - (pane.height - line.height) / 2;
  const maxScroll = Math.max(0, logOutput.scrollHeight - logOutput.clientHeight);
  const next = logOutput.scrollTop + delta;
  setLogScroll(Math.max(0, Math.min(next, maxScroll)));
}

function renderLogLines(lines, { scroll = "bottom" } = {}) {
  const previousScroll = logOutput.scrollTop;
  const token = beginSuppressScroll();

  if (!lines.length) {
    logOutput.innerHTML = "";
    updateMatchNavigator();
    endSuppressScroll(token);
    return;
  }

  logOutput.innerHTML = lines
    .map((line) => {
      const cls = getHighlightClass(line);
      return `<span class="log-line${cls ? ` ${cls}` : ""}">${escapeHtml(line)}</span>`;
    })
    .join("\n");

  updateMatchNavigator();

  if (scroll === "preserve") {
    logOutput.scrollTop = previousScroll;
  } else {
    logOutput.scrollTop = logOutput.scrollHeight;
  }

  endSuppressScroll(token);
}

function rerenderVisibleLines() {
  const lines = [...logOutput.querySelectorAll(".log-line")].map((el) => el.textContent);
  if (lines.length) renderLogLines(lines, { scroll: "preserve" });
  else updateMatchNavigator();
}

function updateFollowToggle() {
  const show = autoRefreshCheckbox.checked && selectedSourceId && !viewer.hidden;
  followToggle.hidden = !show;
  if (!show) return;
  followToggle.textContent = followTail ? "Pause" : "Follow";
}

function pauseFollow() {
  if (!followTail) {
    updateFollowToggle();
    return;
  }
  followTail = false;
  fetchGeneration += 1;
  stopPolling();
  updateFollowToggle();
}

function resumeFollow() {
  if (followTail) return;
  followTail = true;
  wasScrolledUp = false;
  currentMatch = null;
  updateFollowToggle();
  if (!selectedSourceId) return;
  fetchTail({ scroll: "bottom" });
  setupPolling();
}

function stepMatch(delta) {
  const matches = getMatchLines();
  const total = matches.length;
  if (total < 1) return;

  pauseFollow();

  let index = findMatchIndex(matches, currentMatch);
  if (index == null) {
    index = delta > 0 ? 0 : total - 1;
  } else if (total === 1) {
    index = 0;
  } else {
    index = (index + delta + total) % total;
  }

  currentMatch = matchKey(matches, index);
  updateMatchNavigator();
  const current = getMatchLines()[index];
  if (current) scrollLineIntoLog(current);
}

async function loadSources() {
  const sources = await api("/api/sources");
  renderSourceList(sources);
  return sources;
}

function renderSourceList(sources) {
  sourceList.innerHTML = "";

  if (!sources.length) {
    sourceList.innerHTML = '<li class="source-empty">No sources yet. Add one above.</li>';
    return;
  }

  for (const source of sources) {
    const li = document.createElement("li");
    li.className = "source-item" + (source.id === selectedSourceId ? " active" : "");
    li.dataset.id = source.id;

    li.innerHTML = `
      <div class="source-item-info">
        <span class="source-item-name">${escapeHtml(source.name)}</span>
        <span class="source-item-path">${escapeHtml(source.path)}</span>
      </div>
      <div class="source-item-actions">
        <button type="button" class="delete-btn" data-id="${escapeHtml(source.id)}" title="Delete">×</button>
      </div>
    `;

    li.querySelector(".source-item-info").addEventListener("click", () => selectSource(source.id));
    li.querySelector(".delete-btn").addEventListener("click", (e) => {
      e.stopPropagation();
      deleteSource(source.id);
    });

    sourceList.appendChild(li);
  }
}

async function selectSource(id) {
  currentMatch = null;
  followTail = true;
  wasScrolledUp = false;
  fetchGeneration += 1;
  selectedSourceId = id;
  viewerEmpty.hidden = true;
  viewer.hidden = false;
  updateFollowToggle();
  await loadSources();
  await fetchTail({ scroll: "bottom" });
  setupPolling();
}

function clearViewer() {
  currentMatch = null;
  followTail = true;
  wasScrolledUp = false;
  fetchGeneration += 1;
  selectedSourceId = null;
  viewerEmpty.hidden = false;
  viewer.hidden = true;
  stopPolling();
  updateFollowToggle();
}

async function fetchTail({ scroll } = {}) {
  if (!selectedSourceId) return;

  const gen = fetchGeneration;
  const sourceId = selectedSourceId;
  const scrollMode = scroll ?? (followTail ? "bottom" : "preserve");
  const lines = lineCountSelect.value;
  try {
    const data = await api(`/api/sources/${sourceId}/tail?lines=${lines}`);
    if (gen !== fetchGeneration || sourceId !== selectedSourceId) return;
    viewerTitle.textContent = data.name;
    viewerPath.textContent = data.path;
    renderLogLines(data.lines, { scroll: scrollMode });
  } catch (err) {
    if (gen !== fetchGeneration || sourceId !== selectedSourceId) return;
    currentMatch = null;
    const token = beginSuppressScroll();
    logOutput.innerHTML = `<span class="log-line fetch-error">${escapeHtml(err.message)}</span>`;
    updateMatchNavigator();
    endSuppressScroll(token);
  }
}

function requestTail() {
  fetchTail({ scroll: followTail ? "bottom" : "preserve" });
}

function setupPolling() {
  stopPolling();
  if (autoRefreshCheckbox.checked && followTail && selectedSourceId) {
    pollTimer = setInterval(() => fetchTail({ scroll: "bottom" }), POLL_INTERVAL_MS);
  }
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

browseBtn.addEventListener("click", browseForFile);

sourceForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  showFormError("");

  try {
    await api("/api/sources", {
      method: "POST",
      body: JSON.stringify({
        name: sourceNameInput.value.trim(),
        path: sourcePathInput.value.trim(),
      }),
    });
    sourceNameInput.value = "";
    sourcePathInput.value = "";
    await loadSources();
  } catch (err) {
    showFormError(err.message);
  }
});

async function deleteSource(id) {
  if (!confirm("Delete this source?")) return;

  try {
    await api(`/api/sources/${id}`, { method: "DELETE" });
    if (selectedSourceId === id) clearViewer();
    await loadSources();
  } catch (err) {
    showFormError(err.message);
  }
}

refreshBtn.addEventListener("click", requestTail);
lineCountSelect.addEventListener("change", requestTail);
autoRefreshCheckbox.addEventListener("change", () => {
  if (!autoRefreshCheckbox.checked) {
    fetchGeneration += 1;
    stopPolling();
  } else if (followTail && selectedSourceId) {
    fetchTail({ scroll: "bottom" });
    setupPolling();
  }
  updateFollowToggle();
});
followToggle.addEventListener("click", () => {
  if (followTail) pauseFollow();
  else resumeFollow();
});

logOutput.addEventListener("scroll", () => {
  if (suppressScrollFollow) return;
  if (!autoRefreshCheckbox.checked || !selectedSourceId) return;
  const distance = logOutput.scrollHeight - logOutput.scrollTop - logOutput.clientHeight;
  const atBottom = distance < 8;
  if (!atBottom) {
    wasScrolledUp = true;
    pauseFollow();
    return;
  }
  if (wasScrolledUp) resumeFollow();
});

highlightEnabled.addEventListener("change", () => {
  currentMatch = null;
  rerenderVisibleLines();
});
highlightPattern.addEventListener("input", () => {
  currentMatch = null;
  rerenderVisibleLines();
});
highlightPattern.addEventListener("keydown", (event) => {
  if (event.key !== "Enter") return;
  event.preventDefault();
  stepMatch(event.shiftKey ? -1 : 1);
});
highlightCaseSensitive.addEventListener("change", () => {
  currentMatch = null;
  rerenderVisibleLines();
});
matchPrev.addEventListener("click", () => stepMatch(-1));
matchNext.addEventListener("click", () => stepMatch(1));

document.querySelectorAll(".preset").forEach((btn) => {
  btn.addEventListener("click", () => {
    highlightPattern.value = btn.dataset.pattern;
    highlightEnabled.checked = true;
    currentMatch = null;
    rerenderVisibleLines();
  });
});

loadSources().catch((err) => showFormError(err.message));
loadVersion();
