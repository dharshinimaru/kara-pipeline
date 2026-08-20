#!/usr/bin/env python3
"""Fill email addresses into the pipeline from an Apollo CSV export.

Works with whatever Apollo gives you: a UI export today, an API pull later.
Matches on name plus company, falls back to name alone when the company string
differs between OpenAlex and Apollo (it usually does).

    python3 scripts/ingest_apollo.py --apollo ~/Downloads/apollo-contacts.csv

Updates data/candidates_*.csv and data/review_batch.csv in place, filling the
email, linkedin_url and title columns where a confident match is found. Never
overwrites a value you typed yourself.
"""

import argparse
import csv
import glob
import os
import re
import sys

# Apollo's column names have moved around over the years, so accept any of them.
NAME_COLS = ("Name", "Full Name", "name")
FIRST_COLS = ("First Name", "first_name")
LAST_COLS = ("Last Name", "last_name")
EMAIL_COLS = ("Email", "Work Email", "email", "Primary Email", "Email Address")
COMPANY_COLS = ("Company", "Company Name", "Account Name", "organization_name",
                "Employer", "Organization")
LINKEDIN_COLS = ("Person Linkedin Url", "LinkedIn URL", "linkedin_url", "Linkedin Url")
TITLE_COLS = ("Title", "Job Title", "title")


def pick(row, names):
    for n in names:
        if n in row and (row[n] or "").strip():
            return row[n].strip()
    return ""


def norm_name(s):
    s = (s or "").lower()
    if "," in s:                                  # "Surname, Given" -> "given surname"
        last, first = s.split(",", 1)
        s = first + " " + last
    s = re.sub(r"[^a-z\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def norm_company(s):
    s = (s or "").lower()
    s = re.sub(r"\((?:[^)]*)\)", " ", s)          # drop "(United States)"
    s = re.sub(r"\b(inc|ltd|llc|gmbh|corp|corporation|co|plc|company|technologies|"
               r"technology|group|holdings|semiconductors?|electronics)\b", " ", s)
    s = re.sub(r"[^a-z\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load_apollo(path):
    """Return {norm_name: [ {email, linkedin, title, company, company_norm} ]}."""
    by_name = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            name = pick(row, NAME_COLS)
            if not name:
                name = (pick(row, FIRST_COLS) + " " + pick(row, LAST_COLS)).strip()
            email = pick(row, EMAIL_COLS)
            if not name or not email:
                continue
            if "email_not_unlocked" in email or "@" not in email:
                continue
            company = pick(row, COMPANY_COLS)
            by_name.setdefault(norm_name(name), []).append({
                "email": email,
                "linkedin": pick(row, LINKEDIN_COLS),
                "title": pick(row, TITLE_COLS),
                "company": company,
                "company_norm": norm_company(company),
            })
    return by_name


def match(row_name, row_company, by_name):
    """Exact name, then prefer the record whose company overlaps. None if unsure."""
    cands = by_name.get(norm_name(row_name))
    if not cands:
        return None, ""
    if len(cands) == 1:
        c = cands[0]
        rc, cc = norm_company(row_company), c["company_norm"]
        conf = "name+company" if rc and cc and (rc in cc or cc in rc) else "name-only"
        return c, conf
    rc = norm_company(row_company)
    for c in cands:
        cc = c["company_norm"]
        if rc and cc and (rc in cc or cc in rc):
            return c, "name+company"
    return None, "ambiguous"


def update_file(path, by_name, dry_run):
    if not os.path.exists(path):
        return 0, 0, 0
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        cols = list(reader.fieldnames or [])
        rows = [dict(r) for r in reader]
    if not rows or "author" not in cols:
        return 0, 0, 0

    for extra in ("email", "linkedin_url", "title", "match_confidence"):
        if extra not in cols:
            cols.append(extra)

    filled = skipped = ambiguous = 0
    for r in rows:
        r.setdefault("email", "")
        r.setdefault("linkedin_url", "")
        r.setdefault("title", "")
        r.setdefault("match_confidence", "")
        if (r.get("email") or "").strip():
            skipped += 1
            continue
        hit, conf = match(r.get("author", ""), r.get("affiliation", ""), by_name)
        if conf == "ambiguous":
            ambiguous += 1
            r["match_confidence"] = "ambiguous, several people share this name"
            continue
        if not hit:
            continue
        r["email"] = hit["email"]
        r["linkedin_url"] = hit["linkedin"] or r.get("linkedin_url", "")
        r["title"] = hit["title"]
        r["match_confidence"] = conf
        filled += 1

    if not dry_run:
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
    return filled, skipped, ambiguous


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--apollo", required=True, help="Apollo CSV export")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.apollo):
        sys.exit("no such file: %s" % args.apollo)

    by_name = load_apollo(args.apollo)
    print("Apollo rows with a usable email: %d" % sum(len(v) for v in by_name.values()))

    targets = [os.path.join(here, "data", "review_batch.csv")]
    targets += sorted(glob.glob(os.path.join(here, "data", "candidates_*.csv")))

    total = 0
    for path in targets:
        filled, skipped, amb = update_file(path, by_name, args.dry_run)
        if filled or skipped or amb:
            print("%-28s filled %3d, already had one %3d, ambiguous %2d"
                  % (os.path.basename(path), filled, skipped, amb))
            total += filled
    print("%s%d email addresses added" % ("DRY RUN: " if args.dry_run else "", total))
    if total:
        print("Verify current employer before sending. Paper affiliations run stale.")


if __name__ == "__main__":
    main()
