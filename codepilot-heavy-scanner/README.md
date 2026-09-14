# CodePilot Heavy Python Scanner 🚀

A standalone, deterministic and AI-free Python static analyzer designed for very large `.py` files.

## What it does

- Parses Python with the standard-library `ast` module.
- Never imports or executes the analyzed source.
- Measures file size, lines, code/comment/blank lines, tokens and AST nodes.
- Counts functions, classes and imports.
- Calculates function complexity, branch count and nesting depth.
- Detects long functions/classes and excessive parameters.
- Detects mutable default arguments.
- Detects `eval()` / `exec()`.
- Detects shell execution patterns such as `subprocess(..., shell=True)` and `os.system()`.
- Detects risky deserialization (`pickle`, `marshal`).
- Detects weak hashes (`md5`, `sha1`).
- Detects unsafe `yaml.load()` usage.
- Detects `verify=False` in requests-style calls.
- Detects likely hard-coded secrets.
- Detects wildcard and possible unused imports.
- Detects built-in name shadowing, bare `except`, runtime `assert`, long lines, trailing whitespace and TODO/FIXME markers.
- Returns deterministic findings with line/column, severity, category, explanation and suggestion.
- Produces a 0–100 score without any external AI service.

## Requirements

- Python 3.11+ recommended.
- No AI API key.
- No third-party analyzer is required.
- FastAPI/uvicorn are only needed for the optional web API.
- Pytest is needed for tests.

## Run the analyzer

```bash
python -m app.cli examples/heavy_15000_lines.py
```

## Run the API

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then use:

- `POST /api/analyze/heavy` with JSON `{ "code": "...", "filename": "file.py" }`
- `POST /api/analyze/file` with a `.py` upload
- `GET /api/health`

## Very large fixture

`examples/heavy_15000_lines.py` is intentionally generated as a large stress-test source file with more than 15,000 physical lines. It contains a mixture of clean and intentionally problematic constructs so the scanner can demonstrate multiple finding categories without executing the fixture.

The fixture is test data. Do not treat its intentionally unsafe examples as recommended application code.

## Performance design

The analyzer uses a single AST parse followed by bounded AST/token/line scans. It avoids pairwise comparison of every line with every other line, which is important for large files. Findings are collected and sorted by source location.

Static analysis cannot prove the absence of every runtime bug. It is intentionally execution-free.

## Project layout

```text
app/
  __init__.py
  cli.py
  main.py
  analyzers/
    __init__.py
    heavy_analyzer.py
examples/
  heavy_15000_lines.py
  generate_heavy_file.py
tests/
  test_heavy_analyzer.py
requirements.txt
LICENSE
```

## Release notes

### v1.0.0 — Heavy Static Analyzer

- AI-free large-file analysis
- Security and correctness heuristics
- Complexity and maintainability metrics
- Large-file stress fixture (>15,000 lines)
- CLI + FastAPI interfaces
- Automated regression tests
