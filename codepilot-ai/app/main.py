from pathlib import Path
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.analyzers.python_analyzer import analyze_python, score
from app.ai.provider import MockProvider

BASE = Path(__file__).resolve().parent.parent
app = FastAPI(title='CodePilot AI', version='0.1.0')
ai = MockProvider()

class CodeRequest(BaseModel):
    code: str

class AIRequest(BaseModel):
    prompt: str
    context: str = ''

@app.get('/')
def index():
    return FileResponse(BASE / 'static' / 'index.html')

@app.get('/api/health')
def health():
    return {'status': 'ok', 'service': 'codepilot-ai'}

@app.post('/api/analyze')
def analyze(req: CodeRequest):
    findings = analyze_python(req.code)
    return {'score': score(findings), 'findings': [f.__dict__ for f in findings]}

@app.post('/api/ai/ask')
def ask(req: AIRequest):
    return ai.ask(req.prompt, req.context).__dict__

@app.post('/api/project/scan')
async def scan(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith('.zip'):
        raise HTTPException(400, 'Only ZIP project uploads are supported.')
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(413, 'Project archive is limited to 10 MB.')
    return {'filename': file.filename, 'size_bytes': len(data), 'status': 'queued'}
