from pathlib import Path

OUTPUT = Path(__file__).with_name("heavy_15000_lines.py")
TARGET_LINES = 15_250


def build_function(index: int) -> list[str]:
    return [
        f"def stress_function_{index}(value, cache=None):",
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
    ]


def generate() -> None:
    lines = [
        '"""Generated stress fixture for CodePilot Heavy Python Scanner.',
        "This file intentionally exceeds fifteen thousand physical lines.",
        'It is test data and must never be executed as an application.',
        '"""',
        "",
    ]
    index = 0
    while len(lines) + 12 <= TARGET_LINES:
        lines.extend(build_function(index))
        index += 1

    while len(lines) < TARGET_LINES:
        lines.append(f"stress_marker_{len(lines)} = {len(lines)}")

    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"created {OUTPUT} with {len(lines)} lines")


if __name__ == "__main__":
    generate()
