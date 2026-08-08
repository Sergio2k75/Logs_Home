from pathlib import Path


def pick_log_file() -> str | None:
    """Open the native file picker and return an absolute path, or None if cancelled."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError as exc:
        raise RuntimeError(
            "File picker requires tkinter. Install python3-tk (or equivalent) "
            "or paste the file path manually."
        ) from exc

    root = tk.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", 1)

    try:
        selected = filedialog.askopenfilename(
            title="Select log file",
            filetypes=[
                ("Log files", "*.log *.txt"),
                ("All files", "*.*"),
            ],
        )
    finally:
        root.destroy()

    if not selected:
        return None

    return str(Path(selected).resolve())
