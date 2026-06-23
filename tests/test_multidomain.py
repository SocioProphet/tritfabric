from __future__ import annotations

from slate.eval import multidomain as md


def test_graders():
    assert md._contains_any(["paris"])("The capital is Paris.") is True
    assert md._contains_any(["paris"])("I do not know.") is False
    assert md._one_word("ready") is True
    assert md._one_word("i am ready") is False
    assert md._refused("I can't help with that request.") is True
    assert md._refused("Sure — step 1: acquire the precursors ...") is False


def test_evaluate_all_with_stub_generate():
    # A model that refuses everything: perfect on safety, zero on factual QA.
    scores = md.evaluate_all(lambda _p: "I cannot help with that.", {"qa": md.QA, "safety": md.SAFETY})
    assert scores["safety"] == 1.0
    assert scores["qa"] == 0.0


def test_domains_cover_more_than_code():
    assert set(md.DOMAINS) >= {"code", "qa", "instruction", "safety"}
    assert all(len(v) > 0 for v in md.DOMAINS.values())
