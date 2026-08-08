# Logs Home

<!-- APP_SCREENSHOT -->
![Logs Home screenshot](docs/screenshot.png)
<!-- /APP_SCREENSHOT -->

Local log viewer: register named log sources by file path, tail the latest lines, and highlight matching entries.

## Requirements

- Python 3.10+
- Node.js 18+ (for Husky screenshot hook)

## Setup

```bash
pip install -r requirements.txt
npm install
```

## Run

From the project root:

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Usage

1. **Add a source** — enter a display name (e.g. `ollama logs`) and the full path to a `.log` or `.txt` file on your machine. Use the folder button next to the path field to browse with the Windows file picker.
2. **Open a source** — click it in the list to view the latest lines.
3. **Highlight** — enable highlighting and set a pattern (e.g. `ERR`). Use presets for common patterns.
4. **Refresh** — auto-refresh polls every 2 seconds; use the line count selector to change how many lines are shown.

Sources are saved in `data/sources.json` (created on first run).

The browse button opens a native file dialog on the machine where the server is running. It requires a desktop session (not headless/remote without display).

## Development

Each commit runs a Husky pre-commit hook that captures a fresh app screenshot and updates the README image above. Run manually with:

```bash
npm run screenshot
```

App version is defined in `package.json` and shown in the top-right corner of the UI.
