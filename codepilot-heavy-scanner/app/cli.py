from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.analyzers.heavy_analyzer import analyze_python_heavy


def main() -> None:
    parser = argparse.ArgumentParser(description="CodePilot Heavy Python Scanner")
    parser.add_argument("file", type=Path)
    parser.add_argument("--max-findings", type=int, default=2000)
    args = parser.parse_args()

    source = args.file.read_text(encoding="utf-8-sig")
    report = analyze_python_heavy(source, args.file.name)
    if len(report["findings"]) > args.max_findings:
        report["findings"] = report["findings"][:args.max_findings]
        report["findings_truncated"] = True
    else:
        report["findings_truncated"] = False
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
