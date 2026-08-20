#!/usr/bin/env python3
"""Build the morning email: only what is new and actually contactable.

Writes data/digest.txt. If there is nothing new, writes a one-line file saying
so, and the caller decides whether to send at all.
"""

import argparse
import csv
import datetime
import os

SENT_MARKER = "sent_in_digest"


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", default=os.path.join(here, "data", "review_batch.csv"))
    ap.add_argument("--out", default=os.path.join(here, "data", "digest.txt"))
    ap.add_argument("--mark", action="store_true",
                    help="mark the included rows so tomorrow does not repeat them")
    args = ap.parse_args()

    with open(args.batch, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        cols = list(reader.fieldnames or [])
        rows = [dict(r) for r in reader]

    if SENT_MARKER not in cols:
        cols.append(SENT_MARKER)
    for r in rows:
        r.setdefault(SENT_MARKER, "")

    fresh = [r for r in rows
             if (r.get("email") or "").strip()
             and not (r.get(SENT_MARKER) or "").strip()]

    today = datetime.date.today().isoformat()
    lines = []
    if not fresh:
        lines.append("No new contactable candidates today.")
        lines.append("")
        total = sum(1 for r in rows if (r.get("email") or "").strip())
        pending = sum(1 for r in rows if not (r.get("email") or "").strip())
        lines.append("%d contacts found so far, %d still without an address."
                     % (total, pending))
    else:
        lines.append("%d new contacts with drafts, %s." % (len(fresh), today))
        lines.append("")
        lines.append("Nothing has been sent. Copy a body into Gmail to send it.")
        lines.append("Full sheet: ~/kara-pipeline/data/review_batch.csv")
        lines.append("")
        for i, r in enumerate(fresh, 1):
            lines.append("=" * 60)
            lines.append("%d) %s" % (i, r["author"]))
            if r.get("title"):
                lines.append("   %s" % r["title"])
            lines.append("   %s" % r["affiliation"])
            lines.append("   %s" % r["email"])
            if r.get("linkedin_url"):
                lines.append("   %s" % r["linkedin_url"])
            lines.append("   paper: %s" % r["paper_title"][:90])
            lines.append("   doi:   %s" % r["paper_doi"])
            lines.append("")
            lines.append("   Subject: %s" % r["subject"])
            lines.append("")
            for para in r["body"].split("\n\n"):
                lines.append("   " + para.replace("\n", "\n   "))
                lines.append("")
        lines.append("=" * 60)
        lines.append("Verify current employer before sending. Paper affiliations "
                     "run up to two years stale.")

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    if args.mark and fresh:
        for r in fresh:
            r[SENT_MARKER] = today
        with open(args.batch, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)

    print("%d new contacts in digest -> %s" % (len(fresh), args.out))
    print("HAS_NEW=%d" % len(fresh))


if __name__ == "__main__":
    main()
