from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.analyzers.heavy_analyzer import analyze_python_heavy

MAX_SOURCE_BYTES = 25 * 1024 * 1024
app = FastAPI(title="CodePilot Heavy Python Scanner", version="1.0.0")


class AnalyzeRequest(BaseModel):
    code: str
    filename: str = "<string>"


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "codepilot-heavy-scanner", "ai_required": False}


@app.post("/api/analyze/heavy")
def analyze_heavy(req: AnalyzeRequest):
    if len(req.code.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise HTTPException(413, "Source file is limited to 25 MB.")
    return analyze_python_heavy(req.code, req.filename)


@app.post("/api/analyze/file")
async def analyze_file(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".py"):
        raise HTTPException(400, "Only .py files are supported.")
    data = await file.read(MAX_SOURCE_BYTES + 1)
    if len(data) > MAX_SOURCE_BYTES:
        raise HTTPException(413, "Python source is limited to 25 MB.")
    try:
        source = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(400, "The Python file must be UTF-8 encoded.") from exc
    return analyze_python_heavy(source, file.filename)
