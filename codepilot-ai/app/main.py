from pathlib import Path
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.analyzers.python_analyzer import analyze_python, score
from app.analyzers.heavy_analyzer import analyze_python_heavy
from app.ai.provider import MockProvider

BASE = Path(__file__).resolve().parent.parent
app = FastAPI(title='CodePilot AI', version='0.2.0')
ai = MockProvider()
MAX_PYTHON_BYTES = 25 * 1024 * 1024

class CodeRequest(BaseModel):
    code: str
    filename: str = '<string>'

class AIRequest(BaseModel):
    prompt: str
    context: str = ''

@app.get('/')
def index():
    return FileResponse(BASE / 'static' / 'index.html')

@app.get('/api/health')
def health():
    return {'status': 'ok', 'service': 'codepilot-ai', 'heavy_analyzer': 'enabled', 'ai_required': False}

@app.post('/api/analyze')
def analyze(req: CodeRequest):
    findings = analyze_python(req.code)
    return {'score': score(findings), 'findings': [f.__dict__ for f in findings]}

@app.post('/api/analyze/heavy')
def analyze_heavy(req: CodeRequest):
    if len(req.code.encode('utf-8')) > MAX_PYTHON_BYTES:
        raise HTTPException(413, 'Python source is limited to 25 MB.')
    return analyze_python_heavy(req.code, req.filename)

@app.post('/api/analyze/file')
async def analyze_file(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith('.py'):
        raise HTTPException(400, 'Only Python .py files are supported.')
    data = await file.read(MAX_PYTHON_BYTES + 1)
    if len(data) > MAX_PYTHON_BYTES:
        raise HTTPException(413, 'Python source is limited to 25 MB.')
    try:
        source = data.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise HTTPException(400, 'Python file must be UTF-8 encoded.')
    return analyze_python_heavy(source, file.filename)

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
