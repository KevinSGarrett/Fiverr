from __future__ import annotations

from pathlib import Path


def main() -> None:
    base = Path("C:/Fiverr/Fiverr/PM_Pack/03_cursor_agent_system")
    labels = ["A", "B", "E", "C", "F", "D"]
    for label in labels:
        prompt = base / f"CYCLE_065_AGENT_{label}_PROMPT.md"
        if not prompt.exists():
            print(f"CYCLE_065_AGENT_{label}: 0")
            continue
        with prompt.open("r", encoding="utf-8") as handle:
            line_count = sum(1 for _ in handle)
        print(f"CYCLE_065_AGENT_{label}: {line_count}")


if __name__ == "__main__":
    main()
