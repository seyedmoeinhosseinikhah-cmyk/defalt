import ast
from dataclasses import dataclass

@dataclass
class Finding:
    line: int
    severity: str
    code: str
    message: str


def analyze_python(source: str) -> list[Finding]:
    findings: list[Finding] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [Finding(exc.lineno or 1, 'error', 'PY-SYNTAX', exc.msg)]
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {'eval', 'exec'}:
            findings.append(Finding(node.lineno, 'high', 'PY-DYNAMIC', f'Use of {node.func.id} can execute dynamic code.'))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'print':
            findings.append(Finding(node.lineno, 'info', 'PY-PRINT', 'Consider structured logging for production applications.'))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and len(node.body) > 25:
            findings.append(Finding(node.lineno, 'medium', 'PY-LONG-FUNC', f'Function {node.name} is large; consider extracting smaller units.'))
    return findings


def score(findings: list[Finding]) -> int:
    penalties = {'error': 30, 'high': 15, 'medium': 8, 'info': 1}
    return max(0, 100 - sum(penalties.get(f.severity, 0) for f in findings))
