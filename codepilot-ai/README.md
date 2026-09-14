# CodePilot AI 🚀

A production-oriented starting point for an AI-powered Python developer workspace.

## Current MVP
- FastAPI backend
- Real Python AST analysis
- Security-oriented detection for `eval` / `exec`
- Syntax error detection
- Function-size heuristic
- 0–100 code quality score
- AI provider abstraction with a safe local mock
- ZIP upload validation and 10 MB limit
- Responsive developer dashboard
- Pytest coverage for analyzer behavior

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

## Roadmap
1. PostgreSQL + SQLAlchemy persistence
2. Authentication and project history
3. Safe ZIP extraction with path traversal protection
4. Ruff/Radon integration
5. Real AI providers via server-side API keys
6. Test generation and documentation generation
7. Project-wide scanner and analytics dashboard
8. Docker + CI

## Architecture
`app/main.py` exposes the API, `app/analyzers` contains deterministic code analysis, and `app/ai` isolates model providers so external AI vendors can be swapped without changing the API layer.
