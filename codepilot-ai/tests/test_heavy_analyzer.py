from app.analyzers.heavy_analyzer import HeavyPythonAnalyzer


def test_heavy_file_metrics_and_security_findings():
    source = '''import os\nimport subprocess\nimport hashlib\n\nAPI_TOKEN = "super-secret-token-value"\n\ndef risky(value, items=[]):\n    if value:\n        for item in items:\n            if item:\n                try:\n                    subprocess.run(value, shell=True)\n                except Exception:\n                    pass\n    eval(value)\n    return hashlib.md5(value.encode()).hexdigest()\n\ntry:\n    risky("x")\nexcept:\n    pass\n'''
    report = HeavyPythonAnalyzer().analyze(source, "heavy.py")
    assert report["metrics"]["lines"] >= 20
    assert report["metrics"]["functions"] == 1
    codes = {item["code"] for item in report["findings"]}
    assert "PY-EVAL" in codes
    assert "PY-SHELL" in codes
    assert "PY-MUTABLE-DEFAULT" in codes
    assert "PY-MD5" in codes
    assert "PY-BARE-EXCEPT" in codes
    assert 0 <= report["score"] <= 100


def test_very_large_source_is_analyzed_without_execution():
    functions = []
    for index in range(1200):
        functions.append(
            f"def function_{index}(value):\n"
            "    total = 0\n"
            "    for item in range(10):\n"
            "        if item % 2 == 0:\n"
            "            total += item\n"
            "    return total + value\n"
        )
    source = "\n".join(functions)
    report = HeavyPythonAnalyzer().analyze(source, "10k-lines.py")
    assert report["metrics"]["functions"] == 1200
    assert report["metrics"]["lines"] > 7000
    assert report["metrics"]["ast_nodes"] > 10000
    assert report["metrics"]["max_complexity"] >= 2


def test_syntax_error_is_reported_cleanly():
    report = HeavyPythonAnalyzer().analyze("def broken(:\n    pass\n", "broken.py")
    assert report["syntax_error"] is not None
    assert report["score"] == 0
    assert report["findings"][0]["code"] == "PY-SYNTAX"
