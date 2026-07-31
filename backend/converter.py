"""
Conversion engine.

Strategy: Markdown is the hub format.
  - Any supported format -> Markdown  (extraction step)
  - Markdown -> any supported format  (generation step)
So converting X -> Y is done as X -> Markdown -> Y (unless X == md or Y == md,
in which case one leg is skipped).

Backends used:
  - pandoc (docx, html, epub, md — it understands all of these natively)
  - pymupdf4llm (pdf -> markdown; pandoc's own PDF reading is unreliable)
  - pandoc + weasyprint pdf-engine (markdown -> pdf, no LaTeX required)
"""

import subprocess
import tempfile
import os
from pathlib import Path

SUPPORTED_FORMATS = ["md", "pdf", "docx", "html", "epub"]

EXT_TO_FORMAT = {
    "md": "md",
    "markdown": "md",
    "pdf": "pdf",
    "docx": "docx",
    "doc": "docx",
    "html": "html",
    "htm": "html",
    "epub": "epub",
}

FORMAT_LABELS = {
    "md": "Markdown",
    "pdf": "PDF",
    "docx": "Word (.docx)",
    "html": "HTML",
    "epub": "EPUB",
}


class ConversionError(Exception):
    pass


def _run(cmd, cwd=None):
    result = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise ConversionError(
            f"Command failed: {' '.join(cmd)}\n{result.stderr.strip()[-2000:]}"
        )
    return result


def _pdf_to_markdown(pdf_path: str, out_md_path: str):
    import pymupdf4llm

    md_text = pymupdf4llm.to_markdown(pdf_path)
    Path(out_md_path).write_text(md_text, encoding="utf-8")


def _to_markdown(src_path: str, src_fmt: str, out_md_path: str):
    """Convert src_path (of src_fmt) into a markdown file at out_md_path."""
    if src_fmt == "md":
        Path(out_md_path).write_bytes(Path(src_path).read_bytes())
        return
    if src_fmt == "pdf":
        _pdf_to_markdown(src_path, out_md_path)
        return
    if src_fmt in ("docx", "html", "epub"):
        _run(["pandoc", src_path, "-f", src_fmt, "-t", "gfm", "-o", out_md_path])
        return
    raise ConversionError(f"Unsupported source format: {src_fmt}")


def _from_markdown(md_path: str, dst_fmt: str, out_path: str, title: str = "Document"):
    """Convert a markdown file into dst_fmt at out_path."""
    if dst_fmt == "md":
        Path(out_path).write_bytes(Path(md_path).read_bytes())
        return
    if dst_fmt == "pdf":
        _run([
            "pandoc", md_path, "-f", "gfm", "-o", out_path,
            "--pdf-engine=weasyprint", "--metadata", f"title={title}",
        ])
        return
    if dst_fmt in ("docx", "html", "epub"):
        extra = []
        if dst_fmt == "html":
            extra = ["--standalone", "--metadata", f"title={title}"]
        elif dst_fmt == "epub":
            extra = ["--metadata", f"title={title}"]
        _run(["pandoc", md_path, "-f", "gfm", "-t", dst_fmt, "-o", out_path, *extra])
        return
    raise ConversionError(f"Unsupported target format: {dst_fmt}")


def convert(input_path: str, src_fmt: str, dst_fmt: str, out_dir: str, title: str = "Document") -> str:
    """
    Convert a file at input_path (format src_fmt) to dst_fmt.
    Returns the path to the converted output file (inside out_dir).
    """
    if src_fmt not in SUPPORTED_FORMATS:
        raise ConversionError(f"Unsupported source format: {src_fmt}")
    if dst_fmt not in SUPPORTED_FORMATS:
        raise ConversionError(f"Unsupported target format: {dst_fmt}")

    os.makedirs(out_dir, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        if src_fmt == dst_fmt:
            out_path = os.path.join(out_dir, f"converted.{dst_fmt}")
            Path(out_path).write_bytes(Path(input_path).read_bytes())
            return out_path

        if src_fmt == "md":
            md_path = input_path
        else:
            md_path = os.path.join(tmp, "intermediate.md")
            _to_markdown(input_path, src_fmt, md_path)

        if dst_fmt == "md":
            out_path = os.path.join(out_dir, "converted.md")
            Path(out_path).write_bytes(Path(md_path).read_bytes())
            return out_path

        out_path = os.path.join(out_dir, f"converted.{dst_fmt}")
        _from_markdown(md_path, dst_fmt, out_path, title=title)
        return out_path
