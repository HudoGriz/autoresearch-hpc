#!/usr/bin/env python3
"""Exact paired mean-difference example with no third-party dependencies."""

from __future__ import annotations

import csv
import itertools
import json
import sys
from pathlib import Path


def load_differences(path: Path) -> list[float]:
    diffs: list[float] = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"subject", "before", "after"}
        if set(reader.fieldnames or ()) != required:
            raise SystemExit(f"expected columns {sorted(required)}, got {reader.fieldnames}")
        for row in reader:
            diffs.append(float(row["after"]) - float(row["before"]))
    if not diffs:
        raise SystemExit("no observations")
    return diffs


def exact_sign_flip_p(diffs: list[float]) -> float:
    observed = abs(sum(diffs) / len(diffs))
    extreme = 0
    total = 0
    for signs in itertools.product((-1.0, 1.0), repeat=len(diffs)):
        permuted = abs(sum(s * d for s, d in zip(signs, diffs)) / len(diffs))
        total += 1
        if permuted + 1e-12 >= observed:
            extreme += 1
    return extreme / total


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} DATA.tsv")
    diffs = load_differences(Path(sys.argv[1]))
    result = {
        "estimand": "mean(after - before)",
        "mean_difference": round(sum(diffs) / len(diffs), 12),
        "n": len(diffs),
        "sign_flip_p_value": exact_sign_flip_p(diffs),
    }
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
