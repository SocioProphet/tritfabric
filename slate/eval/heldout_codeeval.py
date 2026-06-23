"""heldout_codeeval — pass@1 on a held-out, hidden-test-graded code set.

The promotion gate's eval-delta is only meaningful if it compares a real held-out score for the
fine-tuned model against the base. This computes that score: given a generate(prompt)->text callable
(supplied by the caller, who owns the model), it solves each problem and grades against INDEPENDENT
hidden tests — never the model's own. Used after LoRA training to score base+adapter AND base, so
promote-never-demote can refuse an adapter that doesn't actually beat the base.

Pure except for `python3` (grading) — the model lives entirely behind the generate callable, so the
problem set + grader import and unit-test without torch.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from typing import Callable, List, NamedTuple


class Problem(NamedTuple):
    name: str
    prompt: str
    test: str


# Small held-out set — disjoint from any training data, hidden-test-graded.
HELDOUT: List[Problem] = [
    Problem(
        "gcd",
        "Write a Python function gcd(a: int, b: int) -> int returning the greatest common divisor.",
        "assert gcd(12, 8) == 4\nassert gcd(17, 5) == 1\nassert gcd(0, 9) == 9",
    ),
    Problem(
        "is_anagram",
        "Write a Python function is_anagram(a: str, b: str) -> bool, case-insensitive, ignoring spaces.",
        'assert is_anagram("listen", "silent") is True\nassert is_anagram("a", "b") is False',
    ),
    Problem(
        "running_max",
        "Write a Python function running_max(xs: list[int]) -> list[int] of the cumulative maximum.",
        "assert running_max([1,3,2,5,4]) == [1,3,3,5,5]\nassert running_max([]) == []",
    ),
    Problem(
        "count_vowels",
        "Write a Python function count_vowels(s: str) -> int counting a,e,i,o,u case-insensitively.",
        'assert count_vowels("Hello") == 2\nassert count_vowels("xyz") == 0',
    ),
]

_FENCE = re.compile(r"```(?:python)?\s*(.*?)```", re.DOTALL)


def extract_code(text: str) -> str | None:
    m = _FENCE.search(text or "")
    if m:
        return m.group(1).strip()
    return text.strip() if text and "def " in text else None


def grade(solution: str | None, test: str) -> bool:
    """True only if the solution passes the hidden oracle cleanly."""
    if not solution:
        return False
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "c.py")
        with open(path, "w") as fh:
            fh.write(f"{solution}\n\n{test}\nprint('HIDDEN_OK')\n")
        try:
            out = subprocess.run(["python3", path], capture_output=True, text=True, timeout=12)
        except subprocess.TimeoutExpired:
            return False
    stdout = out.stdout or ""
    return "HIDDEN_OK" in stdout and not re.search(r"\b(Error|Traceback|assert)\b", stdout.replace("HIDDEN_OK", ""))


def pass_at_1(generate: Callable[[str], str], problems: List[Problem] | None = None) -> float:
    """Fraction of held-out problems the model solves on the first try (hidden-test-graded)."""
    problems = problems or HELDOUT
    if not problems:
        return 0.0
    solved = 0
    for p in problems:
        try:
            sol = extract_code(generate(f"{p.prompt}\n\nReturn ONLY the function in a ```python code block."))
        except Exception:
            sol = None
        if grade(sol, p.test):
            solved += 1
    return solved / len(problems)
