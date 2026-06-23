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
    Problem(
        "sum_digits",
        "Write a Python function sum_digits(n: int) -> int summing the decimal digits of abs(n).",
        "assert sum_digits(123) == 6\nassert sum_digits(-405) == 9\nassert sum_digits(0) == 0",
    ),
    Problem(
        "dedup_order",
        "Write a Python function dedup_order(xs: list) -> list removing duplicates but preserving first-seen order.",
        "assert dedup_order([1,3,1,2,3]) == [1,3,2]\nassert dedup_order([]) == []",
    ),
    Problem(
        "to_snake",
        "Write a Python function to_snake(s: str) -> str converting a camelCase string to snake_case.",
        'assert to_snake("camelCase") == "camel_case"\nassert to_snake("HTTPServer") == "h_t_t_p_server"',
    ),
    Problem(
        "clamp",
        "Write a Python function clamp(x: float, lo: float, hi: float) -> float clamping x into [lo, hi].",
        "assert clamp(5, 0, 3) == 3\nassert clamp(-1, 0, 3) == 0\nassert clamp(2, 0, 3) == 2",
    ),
    Problem(
        "is_sorted",
        "Write a Python function is_sorted(xs: list[int]) -> bool returning True if xs is non-decreasing.",
        "assert is_sorted([1,2,2,3]) is True\nassert is_sorted([1,3,2]) is False\nassert is_sorted([]) is True",
    ),
    Problem(
        "char_freq",
        "Write a Python function char_freq(s: str) -> dict mapping each character to its count.",
        'assert char_freq("aab") == {"a": 2, "b": 1}\nassert char_freq("") == {}',
    ),
    Problem(
        "rotate",
        "Write a Python function rotate(xs: list, k: int) -> list rotating xs right by k (k may exceed len).",
        "assert rotate([1,2,3,4], 1) == [4,1,2,3]\nassert rotate([1,2,3], 4) == [3,1,2]\nassert rotate([], 2) == []",
    ),
    Problem(
        "most_common",
        "Write a Python function most_common(xs: list) -> object returning the most frequent element (ties: earliest).",
        "assert most_common([1,2,2,3,3]) == 2\nassert most_common([5]) == 5",
    ),
]

_FENCE = re.compile(r"```(?:python)?\s*(.*?)```", re.DOTALL)


def extract_code(text: str) -> str | None:
    m = _FENCE.search(text or "")
    if m:
        return m.group(1).strip()
    return text.strip() if text and "def " in text else None


def grade(solution: str | None, test: str) -> bool:
    """True only if the hidden asserts ran to completion and passed.

    Judged by a SENTINEL FILE written *after* the appended asserts, plus a clean exit code — never by
    the model's stdout (which it can fake by printing a success marker). A wrong solution fails an
    assert (AssertionError → non-zero exit, sentinel never written); a solution that exits early or
    swallows the asserts also never reaches the sentinel. The sentinel path is a random temp file the
    candidate code never sees, so a pass cannot be forged.
    """
    if not solution:
        return False
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "candidate.py")
        sentinel = os.path.join(d, "passed.flag")
        with open(path, "w") as fh:
            fh.write(f"{solution}\n\n{test}\n\nopen({sentinel!r}, 'w').close()\n")
        try:
            out = subprocess.run(["python3", path], capture_output=True, text=True, timeout=12)
        except subprocess.TimeoutExpired:
            return False
        return out.returncode == 0 and os.path.exists(sentinel)


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
