import os
import shutil
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from converter import convert, ConversionError, EXT_TO_FORMAT, SUPPORTED_FORMATS, FORMAT_LABELS

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"
WORK_DIR = Path(tempfile.gettempdir()) / "doc-converter-jobs"
WORK_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Doc Converter")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/formats")
def get_formats():
    return {"formats": [{"id": f, "label": FORMAT_LABELS[f]} for f in SUPPORTED_FORMATS]}


@app.post("/api/convert")
async def api_convert(file: UploadFile = File(...), target: str = Form(...)):
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    src_fmt = EXT_TO_FORMAT.get(ext)
    if src_fmt is None:
        raise HTTPException(400, f"Unsupported input file type: .{ext}")
    if target not in SUPPORTED_FORMATS:
        raise HTTPException(400, f"Unsupported target format: {target}")

    job_id = uuid.uuid4().hex
    job_dir = WORK_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    input_path = job_dir / file.filename
    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    title = Path(file.filename).stem
    out_dir = job_dir / "out"

    try:
        out_path = convert(str(input_path), src_fmt, target, str(out_dir), title=title)
    except ConversionError as e:
        raise HTTPException(500, str(e))

    download_name = f"{title}.{target}"
    return FileResponse(
        out_path,
        filename=download_name,
        media_type="application/octet-stream",
    )


# Serve the frontend last so /api routes above take priority
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
