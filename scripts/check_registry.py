#!/usr/bin/env python3
"""Check a list of CUIs (one per line, from a file or stdin) and report the pass rate.

    python3 scripts/check_registry.py cuis.txt
    python3 scripts/check_registry.py --sample 100000 --seed 1 cuis.txt

Used to test cui_ro against the trade register: export the CUI column of the
ONRC open-data firm list (data.gov.ro), one CUI per line. Blank lines, "0"
(firms without a CUI) and 13-digit values (the CNP of a sole trader, which the
register keeps in the same column; a CNP is not a CUI) are counted apart and
left out of the rate.
"""
from __future__ import annotations

import argparse
import os
import random
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "python"))
from cui_ro import is_valid, normalize  # noqa: E402


def is_cnp_shaped(s: str) -> bool:
    return s.isdigit() and len(s) == 13


def reason(cui: str) -> str:
    try:
        digits = normalize(cui)
    except ValueError:
        return "not 1-10 digits"
    if len(digits) < 2:
        return "one digit"
    for i in range(len(digits) - 1):
        swapped = digits[:i] + digits[i + 1] + digits[i] + digits[i + 2:]
        if swapped != digits and is_valid(swapped):
            return "wrong control digit (valid if two adjacent digits are swapped)"
    return "wrong control digit"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file", nargs="?", help="one CUI per line (default: stdin)")
    ap.add_argument("--sample", type=int, help="check a random sample of this many distinct CUIs")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    with (open(args.file, encoding="utf-8") if args.file else sys.stdin) as f:
        lines = [line.strip() for line in f]
    empty = sum(1 for s in lines if s in ("", "0"))
    cnp = sum(1 for s in lines if is_cnp_shaped(s))
    cuis = [s for s in lines if s not in ("", "0") and not is_cnp_shaped(s)]
    if args.sample:
        distinct = sorted(set(cuis))
        cuis = random.Random(args.seed).sample(distinct, min(args.sample, len(distinct)))
    bad = Counter(reason(c) for c in cuis if not is_valid(c))
    ok = len(cuis) - sum(bad.values())
    print(f"checked {len(cuis):,} CUIs ({empty:,} blank or 0 and {cnp:,} 13-digit CNPs left out)")
    print(f"valid   {ok:,} ({100 * ok / max(len(cuis), 1):.4f}%)")
    for why, n in bad.most_common():
        print(f"invalid {n:,}: {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
