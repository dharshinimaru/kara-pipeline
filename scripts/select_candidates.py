#!/usr/bin/env python3
"""Pick who to draft next, balanced across core and displacement queries.

Reads data/authors_qualified.csv, keeps T1 and T2 rows that are not export
flagged and not suspect, and writes an ordered candidate list. The drafter
handles deduplication against people already drafted, so this deliberately
emits more candidates than one run needs.
"""

import argparse
import csv
import json
import os


def sort_key(r):
    return (0 if r["tier"] == "T1" else 1,
            -int(r["score"] or 0),
            -int(r["n_relevant_papers"] or 0),
            r["author"])


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp",
                    default=os.path.join(here, "data", "authors_qualified.csv"))
    ap.add_argument("--out", default=os.path.join(here, "data", "candidates.json"))
    ap.add_argument("--per-class", type=int, default=200,
                    help="candidates to take from each query class before pooling")
    args = ap.parse_args()

    with open(args.inp, newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh)
                if r["tier"] in ("T1", "T2")
                and r["export_review"] == "FALSE"
                and r["affil_suspect"] == "N"]

    sel, keys = [], set()
    # Interleave the classes so neither dominates the top of the list.
    by_class = {}
    for cls in ("core", "displacement"):
        by_class[cls] = sorted([r for r in rows if r["query_class"] == cls],
                               key=sort_key)[:args.per_class]
    i = 0
    while any(i < len(v) for v in by_class.values()):
        for cls in ("core", "displacement"):
            if i < len(by_class[cls]):
                r = by_class[cls][i]
                k = (r["author"], r["paper_doi"])
                if k not in keys:
                    keys.add(k)
                    sel.append(r)
        i += 1
    # Anything left over, in score order.
    for r in sorted(rows, key=sort_key):
        k = (r["author"], r["paper_doi"])
        if k not in keys:
            keys.add(k)
            sel.append(r)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(sel, fh)
    print("wrote %d candidates to %s" % (len(sel), args.out))


if __name__ == "__main__":
    main()
