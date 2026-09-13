#!/usr/bin/env python3
"""Integrity checks for the synthetic review benchmark corpus."""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
CASES = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
LABELS = json.loads((HERE / "labels.json").read_text(encoding="utf-8"))


def main() -> int:
    assert CASES["corpus_version"] == LABELS["corpus_version"] == "0.1"
    cases = CASES["cases"]
    labels = LABELS["labels"]
    ids = [case["id"] for case in cases]
    assert len(ids) == len(set(ids)), "case IDs must be unique"
    assert set(ids) == set(labels), "visible cases and hidden labels must have identical IDs"
    assert len(cases) == 9, "v0.1 is frozen at nine cases"
    assert sum(bool(labels[i]["defective"]) for i in ids) == 6
    assert sum(not bool(labels[i]["defective"]) for i in ids) == 3

    required_visible = {"id", "title", "predeclaration", "results", "report"}
    forbidden = {"defective", "class", "required_finding", "label", "ground_truth"}
    for case in cases:
        missing = required_visible - set(case)
        assert not missing, f"{case.get('id')}: missing {sorted(missing)}"
        leaked = forbidden & set(case)
        assert not leaked, f"{case['id']}: hidden label fields leaked: {sorted(leaked)}"
        for field in ("predeclaration", "results", "report"):
            text = case[field]
            assert isinstance(text, str) and len(text.strip()) >= 40, f"{case['id']}: {field} too short"

    for case_id, label in labels.items():
        assert isinstance(label["defective"], bool)
        if label["defective"]:
            assert label["required_finding"], f"{case_id}: defective case needs scoring target"
        else:
            assert label["required_finding"] is None, f"{case_id}: clean control must not have required finding"

    print(f"review corpus v0.1: OK — {len(cases)} cases (6 defect, 3 clean)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
