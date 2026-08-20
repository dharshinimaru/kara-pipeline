#!/bin/zsh
# Enrichment and delivery, using Claude Code's own Apollo and Gmail connections.
# No API key: the same account connection an interactive session uses.
#
# Two narrow Claude jobs, each allowed exactly one tool family:
#   1. look up email addresses in Apollo and write a CSV
#   2. send one email to Dharshini containing the prepared digest
# Everything else is plain Python, so the parts that must be exact are not
# left to a model.

cd "$(dirname "$0")/.." || exit 1
PY=/Library/Frameworks/Python.framework/Versions/3.14/bin/python3
[ -x "$PY" ] || PY=$(command -v python3)
CLAUDE=$(command -v claude || echo "$HOME/.local/bin/claude")
TO="${DIGEST_TO:-dharshini.mar@gmail.com}"
LIMIT="${ENRICH_LIMIT:-20}"
PER_COMPANY="${ENRICH_PER_COMPANY:-1}"

mkdir -p data/log
LOG="data/log/enrich-$(date +%Y-%m-%d).log"
log() { echo "[$(date '+%H:%M')] $*" | tee -a "$LOG"; }

# ---------------------------------------------------------------- enrichment
"$PY" scripts/prepare_enrichment.py --limit "$LIMIT" --per-company "$PER_COMPANY" >>"$LOG" 2>&1
PENDING=$("$PY" -c "import csv;print(len(list(csv.DictReader(open('data/pending_enrichment.csv')))))")
log "queued $PENDING for Apollo lookup"

if [ "$PENDING" -gt 0 ]; then
  rm -f data/apollo_auto.csv
  "$CLAUDE" -p "Read data/pending_enrichment.csv. For every row, look up the person in Apollo using apollo_people_bulk_match, passing name and organization_name, at most 10 people per call. Then write data/apollo_auto.csv with the header line exactly: Name,Title,Company,Email,Person Linkedin Url. Include one row per person Apollo returned that has a real email address. Skip anyone whose email_status is not 'verified' - do not include extrapolated or unavailable addresses. Quote any field containing a comma. If Apollo returned nobody with a verified email, still create the file with only the header line. Do not send anything. Reply with just the number of rows you wrote." \
    --allowedTools "Read,Write,mcp__claude_ai_Apollo_io__apollo_people_bulk_match" \
    >>"$LOG" 2>&1
  if [ -f data/apollo_auto.csv ]; then
    "$PY" scripts/ingest_apollo.py --apollo data/apollo_auto.csv >>"$LOG" 2>&1
    log "ingested Apollo results"
  else
    log "WARNING: enrichment step produced no file"
  fi
fi

# Remember who we tried, so tomorrow does not pay to look them up again.
"$PY" - <<'PYEOF' >>"$LOG" 2>&1
import csv, os
pend = "data/pending_enrichment.csv"
batch = "data/review_batch.csv"
if os.path.exists(pend):
    tried = {r["author"] for r in csv.DictReader(open(pend, encoding="utf-8"))}
    rows = list(csv.DictReader(open(batch, newline="", encoding="utf-8")))
    cols = list(rows[0].keys()) if rows else []
    if "match_confidence" not in cols:
        cols.append("match_confidence")
    for r in rows:
        r.setdefault("match_confidence", "")
        if r["author"] in tried and not (r.get("email") or "").strip():
            r["match_confidence"] = "tried, no Apollo match"
    with open(batch, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)
PYEOF

# ------------------------------------------------------------------ delivery
OUT=$("$PY" scripts/build_digest.py --mark)
echo "$OUT" >>"$LOG"
HAS_NEW=$(echo "$OUT" | sed -n 's/HAS_NEW=//p')
log "digest built, $HAS_NEW new"

HOUR=$(date +%H)
if [ "${HAS_NEW:-0}" -gt 0 ] || [ "$HOUR" = "15" ] || [ -n "$DIGEST_ALWAYS" ]; then
  "$CLAUDE" -p "Read the file data/digest.txt. Send its contents as a plain text email to $TO with the subject 'Kara pipeline: $HAS_NEW new contacts'. Send the file contents verbatim as the body. Do not summarise, reword, or add anything. Send to $TO only, nobody else. Reply with just 'sent'." \
    --allowedTools "Read,mcp__claude_ai_Gmail__send_message" \
    >>"$LOG" 2>&1
  log "digest emailed to $TO"
else
  log "nothing new, no email sent"
fi
