#!/usr/bin/env python3
"""Generate review-ready drafts per skills/draft-outreach/SKILL.md.

Drafts only. This script never sends and never touches Gmail.

Copy content is hand authored per paper, keyed by DOI, and hooks are written
only from the paper title. Nothing here generates a hook automatically, because
a hallucinated hook goes to the person who wrote the paper.

Every number is blocked. The claims ledger is unsigned, so no thermal,
dimensional, pricing, lead-time or qualification figure appears in any body.
The validator at the bottom enforces that mechanically, along with the em dash
ban, the one-question rule, the word count, and the sign-off.

Usage:
    python3 scripts/draft_outreach.py --sel /tmp/sel50.json \
        --out data/review_batch.csv --gaps data/needs_verification.md
"""

import argparse
import csv
import json
import os
import re
import sys

SIGNOFF = "Dharshini / Kara Labs / https://karalabs.ai"
OPENER = ("I am on the founding team at Kara Labs, a YC backed manufacturer of "
          "CVD diamond thermal materials.")

# Beat 5 variants. Pattern A ends on the approved question plus the approved
# brief line. Pattern B keeps the question in beat 4 and closes declaratively.
CLOSER_A = "Worth a quick conversation?\nHappy to send a short technical brief!"
CLOSER_B = "Happy to send a short technical brief either way."

# ---------------------------------------------------------------------------
# Hand-authored content, keyed by DOI.
#   hook   : single clause, defensible from the title alone
#   subject: device or topic, never Kara
#   beat2  : the paper hook sentence
#   beat3  : what Kara makes, sitting in their thermal path
#   beat4  : the diamond question, phrased as a statement under pattern A
#   pattern: A or B
# ---------------------------------------------------------------------------

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from copy_content import (CLEARED_CLAIMS, PRODUCT_SENTENCES,
                          BY_DOI as PAPERS, BY_TITLE as PAPERS_BY_TITLE)

EM_DASH = "—"
EN_DASH = "–"


def company_name(affiliation):
    """Turn an OpenAlex affiliation into something you would say out loud."""
    a = (affiliation or "").strip()
    a = re.sub(r"\s*\((?:United States|United Kingdom|Germany|Japan|Taiwan|"
               r"South Korea|China|France|Italy|Austria|Norway|Poland|Sweden|"
               r"Switzerland|Netherlands|Belgium|Spain|Canada|India|Singapore|"
               r"Israel|Ireland|Denmark|Finland)\)\s*$", "", a)
    a = a.split(",")[0].strip()
    a = re.sub(r"\s+(Inc\.?|Ltd\.?|LLC|GmbH|Corporation|Corp\.?|Company)$", "", a)
    return a


def possessive(name):
    return name + "'" if name.endswith("s") else name + "'s"


def build_body(first_name, company, paper, product_line):
    sentence, claims = PRODUCT_SENTENCES.get(
        product_line, PRODUCT_SENTENCES["polycrystalline-CVD-diamond-wafer"])
    if paper.get("ask"):
        ask = paper["ask"] % (possessive(company), paper["work"])
    else:
        ask = "For %s %s, has diamond come up as a way to %s?" % (
            possessive(company), paper["work"], paper["benefit"])
    return "\n\n".join([
        "Hi %s," % first_name,
        ask + " " + sentence,
        "Happy to share more if it's relevant.",
        SIGNOFF,
    ]), claims


def body_word_count(body):
    """Words in the body, excluding the greeting line and the sign-off."""
    lines = body.split("\n\n")
    core = lines[1:-1]
    return len(" ".join(core).split())


def validate(body, row):
    """Return a list of rule violations. Empty means the draft is clean."""
    problems = []
    core = "\n".join(body.split("\n\n")[1:-1])

    wc = body_word_count(body)
    if not (36 <= wc <= 80):
        problems.append("word count %d outside 36-80" % wc)
    if EM_DASH in body or EN_DASH in body:
        problems.append("dash character present")
    qs = core.count("?")
    if qs != 1:
        problems.append("%d question marks, expected 1" % qs)
    if not body.endswith(SIGNOFF):
        problems.append("sign-off not exact")
    stripped = core
    for text in CLEARED_CLAIMS.values():
        stripped = stripped.replace(text, "")
    if re.search(r"\d", stripped):
        problems.append("uncleared number in body")
    for banned in ("5x", "5 x", "0.1 K/W", "400 W"):
        if banned in core:
            problems.append("blocked claim: %s" % banned)
    for word in ("fascinating", "impressive", "excellent", "great paper",
                 "really enjoyed", "interesting paper"):
        if word in core.lower():
            problems.append("flattery: %s" % word)
    if re.search(r"pushes power density higher each generation", core, re.I):
        problems.append("banned phrase")
    if "one-pager" in core.lower() or "comparison sheet" in core.lower():
        problems.append("offers an unchecked asset")
    return problems


def paper_pattern_a(body):
    return "Worth a quick conversation?" in body


def today():
    import datetime
    return datetime.date.today().isoformat()


def read_existing(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return [dict(r) for r in csv.DictReader(fh)]


def append_rows(path, cols, rows):
    """Append rows, writing a header only when creating the file."""
    if not rows:
        return
    new = not os.path.exists(path)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        if new:
            w.writeheader()
        w.writerows(rows)


def dedupe_keys(path):
    """Keys already drafted: ORCID where present, else name plus affiliation."""
    keys = set()
    for r in read_existing(path):
        orcid = (r.get("orcid") or "").strip()
        if orcid:
            keys.add(("orcid", orcid))
        keys.add(("name", (r.get("author") or "").strip().lower(),
                  (r.get("affiliation") or "").strip().lower()))
    return keys


def row_keys(r):
    out = []
    orcid = (r.get("orcid") or "").strip()
    if orcid:
        out.append(("orcid", orcid))
    out.append(("name", (r.get("author") or "").strip().lower(),
                (r.get("affiliation") or "").strip().lower()))
    return out


def norm_title(t):
    """Normalize a title for matching: unicode dashes, spacing, case."""
    t = (t or "")
    for ch in ("‐", "‑", "‒", "–", "—", "−"):
        t = t.replace(ch, "-")
    t = re.sub(r"\s+", " ", t).strip().lower()
    return t


PAPERS_BY_NORM_TITLE = None


def lookup_paper(row):
    """DOI first, then normalized-title prefix. Never guesses across papers."""
    global PAPERS_BY_NORM_TITLE
    if PAPERS_BY_NORM_TITLE is None:
        PAPERS_BY_NORM_TITLE = {norm_title(k): v for k, v in PAPERS_BY_TITLE.items()}
    p = PAPERS.get(row["paper_doi"])
    if p:
        return p
    nt = norm_title(row["paper_title"])
    p = PAPERS_BY_NORM_TITLE.get(nt)
    if p:
        return p
    # Titles in the data are sometimes truncated relative to the authored key.
    for key, val in PAPERS_BY_NORM_TITLE.items():
        if nt and (key.startswith(nt[:60]) or nt.startswith(key[:60])):
            return val
    return None


def first_name(full):
    full = full.strip()
    if "," in full:                       # "Surname, Given"
        part = full.split(",", 1)[1].strip()
    else:
        part = full.split()[0]
    part = part.split()[0] if part else full
    # Initials are not a usable greeting. Short given names like "Yu" are.
    if part.endswith(".") or len(part.strip(".")) <= 1:
        return ""
    return part


COLUMNS = ["rank", "tier", "class", "author", "affiliation", "affil_suspect",
           "product_line", "paper_title", "paper_doi", "paper_year", "hook",
           "subject", "body", "current_employer_verified", "email",
           "linkedin_url", "approved"]


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--sel", default="/tmp/sel50.json")
    ap.add_argument("--out", default=os.path.join(here, "data", "review_batch.csv"))
    ap.add_argument("--log", default=os.path.join(here, "data", "draft_log.csv"))
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--drafted", default=os.path.join(here, "data", "already_drafted.csv"))
    args = ap.parse_args()

    with open(args.sel, encoding="utf-8") as fh:
        sel = json.load(fh)

    seen = dedupe_keys(args.drafted)
    out_rows, log_rows, skipped, drafted_src = [], [], [], []
    already = 0
    rank = 0
    for r in sel:
        if rank >= args.limit:
            break
        if any(k in seen for k in row_keys(r)):
            already += 1
            continue
        paper = lookup_paper(r)
        fn = first_name(r["author"])
        if paper is None or not fn:
            skipped.append((r["author"], r["paper_title"],
                            "no adjudicated hook" if paper is None else "no usable first name"))
            continue
        company = company_name(r["affiliation"])
        body, claims = build_body(fn, company, paper, r["product_line"])
        problems = validate(body, r)
        if problems:
            skipped.append((r["author"], r["paper_title"], "; ".join(problems)))
            continue
        rank += 1
        for k in row_keys(r):
            seen.add(k)
        out_rows.append({
            "rank": rank,
            "tier": r["tier"],
            "class": r["query_class"],
            "author": r["author"],
            "affiliation": r["affiliation"],
            "affil_suspect": r["affil_suspect"],
            "product_line": r["product_line"],
            "paper_title": r["paper_title"],
            "paper_doi": r["paper_doi"],
            "paper_year": r["paper_year"],
            "hook": paper["hook"],
            "subject": paper["subject"],
            "body": body,
            "current_employer_verified": "",
            "email": "",
            "linkedin_url": "",
            "approved": "",
        })
        drafted_src.append(r)
        log_rows.append({
            "date": "", "author": r["author"], "orcid": r["orcid"],
            "affiliation": r["affiliation"], "tier": r["tier"],
            "product_line": r["product_line"], "asset": "NONE",
            "channel": "email-draft", "subject": paper["subject"],
            "paper_doi": r["paper_doi"], "hook": paper["hook"],
            "word_count": body_word_count(body),
            "claims_used": ",".join(claims) if claims else "none",
            "drafted_by": "draft_outreach.py",
        })

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)

    # Append, never overwrite. Existing rows keep the columns a human filled in
    # (email, approved, and so on), and new people continue the rank sequence.
    log_cols = ["date", "author", "orcid", "affiliation", "tier", "product_line",
                "asset", "channel", "subject", "paper_doi", "hook", "word_count",
                "claims_used", "drafted_by"]
    append_rows(args.log, log_cols, log_rows)

    # The dedupe ledger for every future run.
    append_rows(args.drafted, ["author", "orcid", "affiliation", "paper_doi", "date"],
                [{"author": r["author"], "orcid": r.get("orcid", ""),
                  "affiliation": r["affiliation"], "paper_doi": r["paper_doi"],
                  "date": today()} for r in drafted_src])

    existing = read_existing(args.out)
    for i, row in enumerate(out_rows):
        row["rank"] = len(existing) + i + 1
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(existing + out_rows)

    print("drafted %d new, skipped %d, already drafted %d"
          % (len(out_rows), len(skipped), already), file=sys.stderr)
    for a, t, why in skipped:
        print("  SKIP %-28s %-60s %s" % (a[:28], t[:60], why), file=sys.stderr)


if __name__ == "__main__":
    main()
