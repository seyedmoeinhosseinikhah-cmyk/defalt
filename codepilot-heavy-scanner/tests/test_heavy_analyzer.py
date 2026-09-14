from app.analyzers.heavy_analyzer import HeavyPythonAnalyzer


def test_security_and_metrics():
    source = '''import subprocess\nimport hashlib\n\nAPI_TOKEN = "secret-value-123"\n\ndef risky(value, items=[]):\n    for item in items:\n        if item:\n            subprocess.run(value, shell=True)\n    eval(value)\n    return hashlib.md5(value.encode()).hexdigest()\n\ntry:\n    risky("x")\nexcept:\n    pass\n'''
    report = HeavyPythonAnalyzer().analyze(source, "heavy.py")
    codes = {item["code"] for item in report["findings"]}
    assert report["metrics"]["functions"] == 1
    assert "PY-EVAL" in codes
    assert "PY-SHELL" in codes
    assert "PY-MUTABLE-DEFAULT" in codes
    assert "PY-MD5" in codes
    assert "PY-BARE-EXCEPT" in codes
    assert "PY-HARDCODED-SECRET" in codes
    assert 0 <= report["score"] <= 100


def test_15000_line_scale():
    lines = []
    for index in range(2500):
        lines.extend([
            f"def stress_{index}(value, cache=None):",
            "    if cache is None:",
            "        cache = {}",
            "    total = 0",
            "    for step in range(5):",
            "        if step % 2 == 0:",
            "            total += step + value",
            "        else:",
            "            total -= step",
            "    cache['result'] = total",
            "    return cache['result']",
            "",
        ])
    source = "\n".join(lines)
    assert len(source.splitlines()) >= 15000
    report = HeavyPythonAnalyzer().analyze(source, "heavy_15000_lines.py")
    assert report["metrics"]["lines"] >= 15000
    assert report["metrics"]["functions"] == 2500
    assert report["metrics"]["ast_nodes"] > 50000


def test_syntax_error():
    report = HeavyPythonAnalyzer().analyze("def broken(:\n    pass\n", "broken.py")
    assert report["syntax_error"] is not None
    assert report["findings"][0]["code"] == "PY-SYNTAX"
    assert report["score"] == 0
