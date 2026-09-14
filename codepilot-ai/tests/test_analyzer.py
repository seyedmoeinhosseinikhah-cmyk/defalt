from app.analyzers.python_analyzer import analyze_python, score

def test_detects_dynamic_execution():
    findings = analyze_python('eval(user_input)')
    assert any(f.code == 'PY-DYNAMIC' for f in findings)

def test_syntax_error_is_reported():
    findings = analyze_python('def broken(:')
    assert findings[0].code == 'PY-SYNTAX'

def test_clean_code_scores_high():
    findings = analyze_python('def add(a: int, b: int) -> int:\n    return a + b\n')
    assert score(findings) >= 99
