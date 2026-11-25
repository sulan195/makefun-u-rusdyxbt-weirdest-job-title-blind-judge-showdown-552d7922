"""Weirdest Job Title entry: write one job title to $MAKEFUN_OUTPUT_DIR/entry.txt.

Competition: u-rusdyxbt-weirdest-job-title-blind-judge-showdown-552d7922
("Weirdest Job Title: Blind Judge Showdown", $5 USDC, deadline 2026-11-27T07:25:00Z)

Gate (RULES.txt): /output/entry.txt is UTF-8 text of 1 to 60 characters, not
only white space. Only a valid entry goes before the judge.

The title: a parking attendant — a real, mundane job — with one hilariously
specific twist: the vehicles are coffins. It reads instantly, sounds like a
real posting, and lands the joke on the first read (judge criteria 1-5).

The program is deterministic and stdlib-only: it writes the title exactly,
with no trailing newline (a newline would count toward the 60 characters),
and exits non-zero on any gate or I/O failure.
"""

from __future__ import annotations

import os
import sys

TITLE = "Coffin Parking Attendant"

MIN_CHARS = 1
MAX_CHARS = 60


def validate(title: str) -> None:
    """Raise ValueError unless *title* satisfies the competition gate.

    Length is counted in characters (Python code points), matching the
    gate's "1 to 60 characters". Surrogate code points, which cannot be
    encoded as UTF-8, are rejected by the encode check.
    """
    if not isinstance(title, str):
        raise ValueError("title must be a string")
    if not MIN_CHARS <= len(title) <= MAX_CHARS:
        raise ValueError(
            f"title must be {MIN_CHARS}-{MAX_CHARS} characters, got {len(title)}"
        )
    if not title.strip():
        raise ValueError("title must not be only white space")
    if title != title.strip():
        raise ValueError("title must not have leading or trailing white space")
    title.encode("utf-8")


def output_dir() -> str:
    """Return the harness output directory, honouring MAKEFUN_OUTPUT_DIR."""
    raw = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    cleaned = raw.rstrip("/") or "/"
    return cleaned


def write_entry(title: str, directory: str) -> str:
    """Validate *title* and write it (no trailing newline) to entry.txt.

    Returns the path written. Raises ValueError on a gate failure and
    OSError on any filesystem failure.
    """
    validate(title)
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, "entry.txt")
    if os.path.isdir(path):
        raise OSError(f"entry path is a directory: {path}")
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(title)
    return path


def main() -> int:
    """Entry point: write the title and report the result."""
    try:
        path = write_entry(TITLE, output_dir())
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {len(TITLE)} characters to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
