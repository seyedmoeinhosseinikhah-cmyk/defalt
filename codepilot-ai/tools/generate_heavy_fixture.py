from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "examples" / "heavy_sample.py"
FUNCTIONS = 5000


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as file:
        file.write("# Auto-generated deterministic stress fixture. Never execute untrusted generated code.\n\n")
        for index in range(FUNCTIONS):
            file.write(
                f"def generated_function_{index}(value, items=None):\n"
                "    if items is None:\n"
                "        items = []\n"
                "    total = value\n"
                "    for item in items:\n"
                "        if item % 2 == 0:\n"
                "            total += item\n"
                "        else:\n"
                "            total -= item\n"
                "    return total\n\n"
            )
    print(f"generated {FUNCTIONS} functions -> {OUT}")


if __name__ == "__main__":
    main()
