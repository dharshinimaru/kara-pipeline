#!/usr/bin/env python3
"""Pick who still needs an email address, and cap how many we look up.

Writes data/pending_enrichment.csv, which the enrichment step reads. Capped so
an unattended run can never chew through the Apollo balance, and deduplicated by
company so we do not spend credits on six co-authors of one paper.
"""

import argparse
import collections
import csv
import os

COLS = ["author", "organization_name", "affiliation", "tier", "score"]


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", default=os.path.join(here, "data", "review_batch.csv"))
    ap.add_argument("--out", default=os.path.join(here, "data", "pending_enrichment.csv"))
    ap.add_argument("--limit", type=int, default=20, help="max lookups per run")
    ap.add_argument("--per-company", type=int, default=1,
                    help="max people per company per run")
    args = ap.parse_args()

    with open(args.batch, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    seen = collections.Counter()
    out = []
    for r in rows:
        if (r.get("email") or "").strip():
            continue
        if (r.get("match_confidence") or "").startswith("tried"):
            continue          # already looked up and not found, do not pay twice
        company = r["affiliation"].split("(")[0].split(",")[0].strip()
        if not company:
            continue
        if seen[company] >= args.per_company:
            continue
        seen[company] += 1
        out.append({
            "author": r["author"],
            "organization_name": company,
            "affiliation": r["affiliation"],
            "tier": r.get("tier", ""),
            "score": r.get("score", ""),
        })
        if len(out) >= args.limit:
            break

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(out)
    print("%d people queued for enrichment -> %s" % (len(out), args.out))


if __name__ == "__main__":
    main()
