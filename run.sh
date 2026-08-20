#!/bin/zsh
# One command for the whole pipeline. Safe to run again and again.
#
#   ./run.sh
#
# Mines OpenAlex, qualifies, and drafts. Only people who have never been
# drafted before are added to data/review_batch.csv, so anything you have
# already filled in or sent is left alone. Nothing is ever sent.

set -e
cd "$(dirname "$0")"

export OPENALEX_MAILTO="${OPENALEX_MAILTO:-dharshini@karadiam.com}"
STAMP=$(date +%Y-%m-%d)
mkdir -p data/log

echo "[$(date +%H:%M)] mining OpenAlex"
python3 scripts/mine_openalex.py --max-pages 1 --company-only \
  --out data/authors_raw.csv \
  --yield-table data/query_yield_company.md

echo "[$(date +%H:%M)] qualifying"
python3 scripts/qualify_authors.py

echo "[$(date +%H:%M)] selecting candidates"
python3 scripts/select_candidates.py --out data/candidates.json

echo "[$(date +%H:%M)] drafting"
python3 scripts/draft_outreach.py --sel data/candidates.json --limit "${LIMIT:-50}"

echo "[$(date +%H:%M)] done. Open data/review_batch.csv"
