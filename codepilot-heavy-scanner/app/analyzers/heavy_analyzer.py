from __future__ import annotations

import ast
import io
import re
import tokenize
from collections import Counter
from dataclasses import dataclass


@dataclass
class Finding:
    line: int
    column: int
    severity: str
    category: str
    code: str
    message: str
    suggestion: str


@dataclass
class FunctionStats:
    name: str
    line: int
    complexity: int = 1
    max_nesting: int = 0
    branches: int = 0
    returns: int = 0
    statements: int = 0


class HeavyPythonAnalyzer(ast.NodeVisitor):
    """Deterministic, execution-free analyzer for very large Python files."""

    SECRET_RE = re.compile(r"(?:password|passwd|secret|api[_-]?key|token|private[_-]?key)", re.I)
    BUILTINS = {
        "abs", "all", "any", "ascii", "bin", "bool", "breakpoint", "bytearray", "bytes",
        "callable", "chr", "classmethod", "compile", "complex", "delattr", "dict", "dir",
        "divmod", "enumerate", "eval", "exec", "filter", "float", "format", "frozenset",
        "getattr", "globals", "hasattr", "hash", "help", "hex", "id", "input", "int", "isinstance",
        "issubclass", "iter", "len", "list", "locals", "map", "max", "memoryview", "min", "next",
        "object", "oct", "open", "ord", "pow", "print", "property", "range", "repr", "reversed",
        "round", "set", "setattr", "slice", "sorted", "staticmethod", "str", "sum", "super", "tuple",
        "type", "vars", "zip",
    }

    def __init__(self, *, long_function=60, long_class=250, complexity=10, nesting=5, parameters=8):
        self.long_function = long_function
        self.long_class = long_class
        self.complexity_limit = complexity
        self.nesting_limit = nesting
        self.parameter_limit = parameters
        self.reset()

    def reset(self):
        self.findings = []
        self.functions = []
        self.classes = 0
        self.imports = 0
        self.used_names = set()
        self.imported_names = {}
        self.function_stack = []
        self.nesting = 0
        self.max_nesting = 0
        self._source_lines = []
        self._ast_nodes = 0

    def add(self, node, severity, category, code, message, suggestion):
        self.findings.append(Finding(
            getattr(node, "lineno", 1), getattr(node, "col_offset", 0),
            severity, category, code, message, suggestion,
        ))

    def analyze(self, source: str, filename: str = "<string>") -> dict:
        self.reset()
        self._source_lines = source.splitlines()
        metrics = self._metrics(source)
        try:
            tree = ast.parse(source, filename=filename, type_comments=True)
        except SyntaxError as exc:
            self.findings = [Finding(
                exc.lineno or 1, exc.offset or 0, "critical", "syntax", "PY-SYNTAX",
                f"Syntax error: {exc.msg}", "خطای نحوی را در محل مشخص‌شده اصلاح کنید.",
            )]
            return self._report(metrics, filename, {"line": exc.lineno, "column": exc.offset, "message": exc.msg})

        self.visit(tree)
        self._post_import_checks()
        self._line_checks()
        self.findings.sort(key=lambda f: (f.line, f.column, -self._severity_weight(f.severity)))
        metrics.update({
            "functions": len(self.functions),
            "classes": self.classes,
            "imports": self.imports,
            "max_complexity": max((f.complexity for f in self.functions), default=1),
            "max_nesting": self.max_nesting,
        })
        return self._report(metrics, filename, None)

    def _metrics(self, source):
        lines = source.splitlines()
        blank = sum(not line.strip() for line in lines)
        comments = 0
        try:
            token_stream = tokenize.generate_tokens(io.StringIO(source).readline)
            token_count = 0
            for token in token_stream:
                if token.type == tokenize.COMMENT:
                    comments += 1
                if token.type not in (tokenize.ENCODING, tokenize.ENDMARKER):
                    token_count += 1
        except (tokenize.TokenError, IndentationError):
            token_count = 0
        return {
            "bytes": len(source.encode("utf-8")),
            "lines": len(lines),
            "code_lines": max(0, len(lines) - blank - comments),
            "blank_lines": blank,
            "comment_lines": comments,
            "tokens": token_count,
            "ast_nodes": 0,
        }

    def _report(self, metrics, filename, syntax_error):
        metrics["ast_nodes"] = self._ast_nodes
        counts = Counter(f.severity for f in self.findings)
        weighted = sum(self._severity_weight(f.severity) for f in self.findings)
        density = weighted / max(metrics["code_lines"], 1) * 100
        score = max(0, min(100, round(100 - min(90, density * 2.2))))
        return {
            "filename": filename,
            "score": score,
            "syntax_error": syntax_error,
            "metrics": metrics,
            "severity_counts": dict(counts),
            "findings": [f.__dict__ for f in self.findings],
            "functions": [f.__dict__ for f in self.functions],
        }

    @staticmethod
    def _severity_weight(severity):
        return {"critical": 12, "high": 8, "medium": 4, "low": 2, "info": 1}.get(severity, 1)

    def generic_visit(self, node):
        self._ast_nodes += 1
        super().generic_visit(node)

    def visit_Name(self, node):
        self.used_names.add(node.id)
        if isinstance(node.ctx, ast.Store) and node.id in self.BUILTINS:
            self.add(node, "medium", "maintainability", "PY-BUILTIN-SHADOW",
                     f"نام داخلی پایتون با '{node.id}' سایه زده شده است.",
                     "برای متغیر یا تابع از نام دیگری استفاده کنید.")
        self.generic_visit(node)

    def visit_Import(self, node):
        self.imports += len(node.names)
        for alias in node.names:
            local = alias.asname or alias.name.split('.')[0]
            self.imported_names[local] = (node.lineno, node.col_offset)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self.imports += len(node.names)
        for alias in node.names:
            local = alias.asname or alias.name
            if local == "*":
                self.add(node, "medium", "imports", "PY-WILDCARD-IMPORT", "Wildcard import تشخیص داده شد.", "نام‌های موردنیاز را صریح import کنید.")
            else:
                self.imported_names[local] = (node.lineno, node.col_offset)
        self.generic_visit(node)

    def visit_FunctionDef(self, node): self._visit_function(node)
    def visit_AsyncFunctionDef(self, node): self._visit_function(node)

    def _visit_function(self, node):
        args = node.args
        parameter_count = len(args.posonlyargs) + len(args.args) + len(args.kwonlyargs)
        parameter_count += bool(args.vararg) + bool(args.kwarg)
        stats = FunctionStats(node.name, node.lineno, statements=len(node.body))
        self.functions.append(stats)
        if parameter_count > self.parameter_limit:
            self.add(node, "medium", "maintainability", "PY-MANY-PARAMS",
                     f"تابع '{node.name}' پارامترهای زیادی ({parameter_count}) دارد.",
                     "پارامترها را با config/object یا چند تابع کوچک‌تر سازمان‌دهی کنید.")
        for default in list(args.defaults) + [d for d in args.kw_defaults if d is not None]:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self.add(default, "high", "correctness", "PY-MUTABLE-DEFAULT",
                         "mutable default argument تشخیص داده شد.",
                         "از None به‌عنوان default استفاده و مقدار mutable را داخل تابع بسازید.")
        self.function_stack.append(stats)
        old_nesting = self.nesting
        self.nesting = 0
        for statement in node.body:
            self.visit(statement)
        stats.max_nesting = self.nesting
        self.max_nesting = max(self.max_nesting, stats.max_nesting)
        if stats.statements > self.long_function:
            self.add(node, "medium", "maintainability", "PY-LONG-FUNCTION",
                     f"تابع '{node.name}' بدنه بزرگی با {stats.statements} statement دارد.",
                     "تابع را به واحدهای کوچک‌تر با مسئولیت مشخص تقسیم کنید.")
        if stats.complexity > self.complexity_limit:
            self.add(node, "high", "complexity", "PY-HIGH-COMPLEXITY",
                     f"پیچیدگی تابع '{node.name}' برابر {stats.complexity} است.",
                     "شرط‌ها و حلقه‌های تو‌در‌تو را کاهش دهید و منطق را استخراج کنید.")
        if stats.max_nesting > self.nesting_limit:
            self.add(node, "high", "complexity", "PY-DEEP-NESTING",
                     f"عمق تو‌در‌تو شدن در '{node.name}' به {stats.max_nesting} رسیده است.",
                     "از guard clause و استخراج تابع استفاده کنید.")
        self.function_stack.pop()
        self.nesting = old_nesting

    def _branch(self, amount=1):
        if self.function_stack:
            self.function_stack[-1].complexity += amount
            self.function_stack[-1].branches += amount

    def _nested(self, body, extra=None):
        self._branch()
        self.nesting += 1
        self.max_nesting = max(self.max_nesting, self.nesting)
        for item in body: self.visit(item)
        for item in extra or []: self.visit(item)
        self.nesting -= 1

    def visit_If(self, node):
        self._nested(node.body, node.orelse)
        self.visit(node.test)

    def visit_For(self, node):
        self._nested(node.body, node.orelse)
        self.visit(node.target); self.visit(node.iter)
    visit_AsyncFor = visit_For

    def visit_While(self, node):
        self._nested(node.body, node.orelse)
        self.visit(node.test)

    def visit_Try(self, node):
        self._branch(len(node.handlers) + bool(node.orelse))
        self.nesting += 1
        self.max_nesting = max(self.max_nesting, self.nesting)
        for item in node.body + node.orelse + node.finalbody: self.visit(item)
        for handler in node.handlers: self.visit(handler)
        self.nesting -= 1

    def visit_ExceptHandler(self, node):
        if node.type is None:
            self.add(node, "medium", "correctness", "PY-BARE-EXCEPT", "bare except تشخیص داده شد.", "یک exception مشخص را catch کنید.")
        self.generic_visit(node)

    def visit_With(self, node):
        self._nested(node.body)
        for item in node.items: self.visit(item)
    visit_AsyncWith = visit_With

    def visit_BoolOp(self, node):
        self._branch(max(0, len(node.values) - 1))
        self.generic_visit(node)

    def visit_Return(self, node):
        if self.function_stack: self.function_stack[-1].returns += 1
        self.generic_visit(node)

    def visit_Call(self, node):
        name = self._call_name(node)
        if name in {"eval", "exec"}:
            self.add(node, "critical", "security", "PY-EVAL", f"استفاده از {name}() اجرای کد پویا ایجاد می‌کند.", "آن را حذف و از parser یا ساختار داده امن استفاده کنید.")
        if name == "os.system" or (name.startswith("subprocess.") and self._kw_bool(node, "shell", True)):
            self.add(node, "high", "security", "PY-SHELL", "اجرای command با shell فعال تشخیص داده شد.", "shell=True را حذف و آرگومان‌ها را به‌صورت argv ارسال کنید.")
        if name in {"pickle.load", "pickle.loads", "marshal.loads"}:
            self.add(node, "high", "security", "PY-UNSAFE-DESERIALIZE", f"deserialize ناامن با {name} تشخیص داده شد.", "فقط داده قابل اعتماد را deserialize کنید یا قالب امن‌تری انتخاب کنید.")
        if name in {"hashlib.md5", "hashlib.sha1"}:
            self.add(node, "medium", "security", "PY-MD5", f"استفاده از {name} تشخیص داده شد.", "برای کاربردهای امنیتی SHA-256 یا الگوریتم مدرن‌تر استفاده کنید.")
        if name == "yaml.load" and not self._has_kw(node, "Loader"):
            self.add(node, "high", "security", "PY-YAML-LOAD", "yaml.load بدون Loader امن تشخیص داده شد.", "از yaml.safe_load یا SafeLoader استفاده کنید.")
        if name.startswith("requests.") and self._kw_bool(node, "verify", False):
            self.add(node, "medium", "security", "PY-VERIFY-FALSE", "TLS certificate verification غیرفعال شده است.", "verify را فعال نگه دارید.")
        self.generic_visit(node)

    @staticmethod
    def _call_name(node):
        parts = []
        cur = node.func
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr); cur = cur.value
        if isinstance(cur, ast.Name): parts.append(cur.id)
        return ".".join(reversed(parts))

    @staticmethod
    def _kw_bool(node, key, value):
        return any(k.arg == key and isinstance(k.value, ast.Constant) and k.value.value is value for k in node.keywords)

    @staticmethod
    def _has_kw(node, key): return any(k.arg == key for k in node.keywords)

    def visit_Assign(self, node):
        for target in node.targets:
            names = self._target_names(target)
            if any(self.SECRET_RE.search(name) for name in names) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str) and len(node.value.value) >= 8:
                self.add(node, "high", "security", "PY-HARDCODED-SECRET", "مقدار متنی شبیه secret/token به‌صورت hard-coded قرار گرفته است.", "secret را در environment یا secret manager نگه دارید.")
        self.generic_visit(node)

    def _target_names(self, target):
        if isinstance(target, ast.Name): return [target.id]
        if isinstance(target, (ast.Tuple, ast.List)):
            return [n for elt in target.elts for n in self._target_names(elt)]
        return []

    def visit_Assert(self, node):
        self.add(node, "low", "correctness", "PY-ASSERT", "assert در کد اجرایی تشخیص داده شد.", "برای validation مهم از exception صریح استفاده کنید.")
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.classes += 1
        if len(node.body) > self.long_class:
            self.add(node, "medium", "maintainability", "PY-LONG-CLASS", f"کلاس '{node.name}' بسیار بزرگ است ({len(node.body)} statement).", "مسئولیت کلاس را به چند component تقسیم کنید.")
        self.generic_visit(node)

    def _post_import_checks(self):
        for name, (line, col) in self.imported_names.items():
            if name not in self.used_names:
                node = ast.Constant(value=name, lineno=line, col_offset=col)
                self.add(node, "low", "imports", "PY-POSSIBLE-UNUSED-IMPORT", f"import '{name}' ظاهراً استفاده نشده است.", "در صورت غیرضروری بودن حذفش کنید؛ dynamic access و __all__ را در نظر بگیرید.")

    def _line_checks(self):
        for index, line in enumerate(self._source_lines, 1):
            if len(line) > 120:
                node = ast.Constant(value=None, lineno=index, col_offset=120)
                self.add(node, "medium" if len(line) > 200 else "low", "style", "PY-LONG-LINE", f"خط {index} دارای {len(line)} کاراکتر است.", "خط را کوتاه یا expression را تقسیم کنید.")
            if line.rstrip() != line:
                self.add(ast.Constant(value=None, lineno=index, col_offset=max(0, len(line)-1)), "info", "style", "PY-TRAILING-WHITESPACE", "فضای خالی انتهای خط وجود دارد.", "فضای خالی انتهای خط را حذف کنید.")
            if "TODO" in line or "FIXME" in line:
                self.add(ast.Constant(value=None, lineno=index, col_offset=0), "info", "maintenance", "PY-TODO", "TODO/FIXME در فایل وجود دارد.", "در صورت اهمیت آن را به task قابل پیگیری تبدیل کنید.")


def analyze_python_heavy(source: str, filename: str = "<string>") -> dict:
    return HeavyPythonAnalyzer().analyze(source, filename)
