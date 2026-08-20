#!/bin/zsh
# One command for the whole pipeline. Safe to run again and again.
#
#   ./run.sh
#
# Mines OpenAlex, qualifies, and drafts. Only people who have never been
# drafted before are added to data/review_batch.csv, so anything you have
# already filled in or sent is left alone. Nothing is ever sent.
#
# Also runs unattended from launchd; see scripts/schedule.sh.

cd "$(dirname "$0")" || exit 1

# launchd gives a minimal PATH, so python3 is addressed absolutely with a
# fallback to whatever is on PATH for interactive use.
PY=/Library/Frameworks/Python.framework/Versions/3.14/bin/python3
[ -x "$PY" ] || PY=$(command -v python3)

export OPENALEX_MAILTO="${OPENALEX_MAILTO:-dharshini@karadiam.com}"
mkdir -p data/log
LOG="data/log/run-$(date +%Y-%m-%d).log"

log() { echo "[$(date '+%Y-%m-%d %H:%M')] $*" | tee -a "$LOG"; }

log "mining OpenAlex"
if ! "$PY" scripts/mine_openalex.py --max-pages 1 --company-only \
      --out data/authors_raw.csv \
      --yield-table data/query_yield_company.md >>"$LOG" 2>&1; then
  if grep -q "daily budget exhausted" "$LOG"; then
    log "STOPPED: OpenAlex daily budget is used up. Nothing changed."
    log "The budget resets at midnight UTC. Try again after that."
    exit 0
  fi
  log "FAILED during mining. See $LOG"
  exit 1
fi

log "qualifying"
"$PY" scripts/qualify_authors.py >>"$LOG" 2>&1 || { log "FAILED during qualify"; exit 1; }

log "selecting candidates"
"$PY" scripts/select_candidates.py --out data/candidates.json >>"$LOG" 2>&1 \
  || { log "FAILED during select"; exit 1; }

log "drafting"
BEFORE=$("$PY" -c "import csv,os;p='data/review_batch.csv';print(len(list(csv.DictReader(open(p)))) if os.path.exists(p) else 0)")
"$PY" scripts/draft_outreach.py --sel data/candidates.json --limit "${LIMIT:-50}" >>"$LOG" 2>&1 \
  || { log "FAILED during drafting"; exit 1; }
AFTER=$("$PY" -c "import csv;print(len(list(csv.DictReader(open('data/review_batch.csv')))))")

log "done. $((AFTER - BEFORE)) new people added, $AFTER total in data/review_batch.csv"
