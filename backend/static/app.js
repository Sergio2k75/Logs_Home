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
const refreshBtn = $("#refresh-btn");
const highlightEnabled = $("#highlight-enabled");
const highlightPattern = $("#highlight-pattern");
const highlightCaseSensitive = $("#highlight-case-sensitive");
const logOutput = $("#log-output");
const appVersion = $("#app-version");

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

function renderLogLines(lines) {
  if (!lines.length) {
    logOutput.innerHTML = "";
    return;
  }

  logOutput.innerHTML = lines
    .map((line) => {
      const cls = getHighlightClass(line);
      return `<span class="log-line${cls ? ` ${cls}` : ""}">${escapeHtml(line)}</span>`;
    })
    .join("\n");

  logOutput.scrollTop = logOutput.scrollHeight;
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
  selectedSourceId = id;
  viewerEmpty.hidden = true;
  viewer.hidden = false;
  await loadSources();
  await fetchTail();
  setupPolling();
}

function clearViewer() {
  selectedSourceId = null;
  viewerEmpty.hidden = false;
  viewer.hidden = true;
  stopPolling();
}

async function fetchTail() {
  if (!selectedSourceId) return;

  const lines = lineCountSelect.value;
  try {
    const data = await api(`/api/sources/${selectedSourceId}/tail?lines=${lines}`);
    viewerTitle.textContent = data.name;
    viewerPath.textContent = data.path;
    renderLogLines(data.lines);
  } catch (err) {
    logOutput.innerHTML = `<span class="log-line highlight-error">${escapeHtml(err.message)}</span>`;
  }
}

function setupPolling() {
  stopPolling();
  if (autoRefreshCheckbox.checked && selectedSourceId) {
    pollTimer = setInterval(fetchTail, POLL_INTERVAL_MS);
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

refreshBtn.addEventListener("click", fetchTail);
lineCountSelect.addEventListener("change", fetchTail);
autoRefreshCheckbox.addEventListener("change", setupPolling);

highlightEnabled.addEventListener("change", () => {
  if (logOutput.children.length) fetchTail();
  else renderLogLines([]);
});
highlightPattern.addEventListener("input", () => {
  const lines = [...logOutput.querySelectorAll(".log-line")].map((el) => el.textContent);
  if (lines.length) renderLogLines(lines);
});
highlightCaseSensitive.addEventListener("change", () => {
  const lines = [...logOutput.querySelectorAll(".log-line")].map((el) => el.textContent);
  if (lines.length) renderLogLines(lines);
});

document.querySelectorAll(".preset").forEach((btn) => {
  btn.addEventListener("click", () => {
    highlightPattern.value = btn.dataset.pattern;
    highlightEnabled.checked = true;
    const lines = [...logOutput.querySelectorAll(".log-line")].map((el) => el.textContent);
    if (lines.length) renderLogLines(lines);
  });
});

loadSources().catch((err) => showFormError(err.message));
loadVersion();
