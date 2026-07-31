# EasyConvert
A small local web app for converting documents between **Markdown, PDF, Word (.docx), HTML, and EPUB**.
Runs entirely on your machine — nothing is uploaded anywhere.

Drop in a file, pick an output format, and it converts and downloads the result. Any format can go
to any other format (e.g. EPUB → Word, PDF → Markdown, HTML → PDF) — internally every conversion
passes through Markdown as a hub format.

## How it works

- **pandoc** handles Word, HTML, EPUB, and Markdown conversions (it understands all of these natively).
- **pymupdf4llm** extracts PDF content into clean Markdown (pandoc's own PDF reading is unreliable, so this
  is used specifically for PDF → Markdown).
- **pandoc + weasyprint** generates PDFs from Markdown (via HTML/CSS, no LaTeX install required).

## Setup

You need **Python 3.10+** and **pandoc** installed.

1. Install pandoc (if you don't already have it):
   - macOS: `brew install pandoc`
   - Ubuntu/Debian: `sudo apt install pandoc`
   - Windows: download the installer from https://pandoc.org/installing.html

2. Install the Python dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

   Note: `weasyprint` needs a couple of system libraries (Pango, Cairo, GDK-Pixbuf) for PDF generation.
   These are usually already present on Linux/macOS. If you hit errors generating PDFs, see
   https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation for your OS.

3. Start the app:
   ```bash
   ./start.sh
   ```
   or directly:
   ```bash
   cd backend
   uvicorn main:app --host 127.0.0.1 --port 8000
   ```

4. Open **http://127.0.0.1:8000** in your browser.

## Project layout

```
converter-app/
├── backend/
│   ├── main.py          FastAPI app — serves the frontend + /api/convert endpoint
│   ├── converter.py      conversion engine (pandoc + pymupdf4llm + weasyprint)
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
└── start.sh
```

## Extending it

To add another format, add it to `SUPPORTED_FORMATS` / `EXT_TO_FORMAT` / `FORMAT_LABELS` in
`backend/converter.py`, then extend `_to_markdown` and `_from_markdown` with a case for it (pandoc
supports many more formats out of the box — RTF, ODT, LaTeX, reStructuredText, etc. — so most new
formats are a one-line addition). Mirror the new format in `frontend/app.js`'s `FORMATS` array.

## Limits

- Single file conversions only (no batch/zip upload).
- PDF → other formats always goes through Markdown extraction, so complex PDF layouts (multi-column,
  heavy graphics) will lose some fidelity — this is inherent to any PDF text-extraction approach.
- Max request size follows FastAPI/Starlette defaults; for very large files you may want to raise
  upload limits in `main.py`.

