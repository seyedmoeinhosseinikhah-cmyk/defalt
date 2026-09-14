# CodePilot AI 🚀

A production-oriented Python developer workspace with a deterministic, AI-optional static analyzer.

## Heavy Python Analyzer — no AI required

CodePilot now includes a dedicated heavy-file analyzer designed for large Python source files. It **never imports or executes the uploaded code**. Analysis is based on Python's AST and tokenizer, so results are deterministic and work without an API key or AI provider.

### What it detects

- Syntax errors
- File size, line counts, code/comment/blank lines and token count
- AST node count, function/class/import counts
- Per-function complexity, branches, returns and nesting depth
- Very long functions and classes
- Too many parameters
- Mutable default arguments
- `eval()` / `exec()`
- shell execution through `os.system()` and `subprocess(..., shell=True)`
- unsafe `pickle` / `marshal` deserialization
- unsafe `yaml.load()` usage
- disabled TLS verification in `requests`
- weak MD5/SHA-1 hashing indicators
- hard-coded secret-like values
- wildcard imports and possible unused imports
- bare `except`
- `assert` used in runtime code
- built-in name shadowing
- long lines and trailing whitespace
- TODO/FIXME maintenance markers

### API

`POST /api/analyze/heavy`

```json
{
  "filename": "big_project.py",
  "code": "print('hello')"
}
```

`POST /api/analyze/file` accepts a UTF-8 `.py` upload. The current source limit is **25 MB**.

`GET /api/health` reports whether the heavy analyzer is enabled and confirms that AI is not required for static analysis.

## Important limitation

This is comprehensive **static** analysis, not a proof that a program is bug-free. Dynamic behavior, runtime-only errors, external services and semantic intent cannot be completely proven from a single source file without executing or instrumenting the program.

## Current MVP

- FastAPI backend
- Basic and heavy Python AST analysis
- Deterministic security-oriented detection
- Syntax error detection
- 0–100 quality score
- AI provider abstraction with a safe local mock
- ZIP upload validation and 10 MB project limit
- Pytest coverage for analyzer behavior
- Large-source regression test with 1,200 generated functions

## Run locally

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pytest
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Architecture

`app/main.py` exposes the API, `app/analyzers` contains deterministic code analysis, and `app/ai` isolates optional model providers so external AI vendors can be swapped without changing the API layer.
