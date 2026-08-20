# kara-pipeline

Publication-sourced outreach for Kara Labs. Sources thermal engineers from what
they publish rather than from their job titles, qualifies and tiers them, and
drafts personalized outreach for a human to review and send.

Autonomous on research, qualification, and drafting. Hard-gated on numbers and
sending. Read `CLAUDE.md` for the full rules and `claims/verified_claims.md`
before writing any copy containing a number.

## Layout

```
CLAUDE.md                        project rules, loaded every session
config/queries.json              15 topic queries for OpenAlex
scripts/mine_openalex.py         stage 1, stdlib only
claims/verified_claims.md        the claims ledger, governs every number in copy
claims/assets/                   comparison assets A1 to A6, currently empty
skills/qualify-authors/          stage 2
skills/draft-outreach/           stage 5
data/                            all generated CSVs
```

## Run order

```bash
# 1. Mine. Free, no API key. Use a real address for the polite pool.
export OPENALEX_MAILTO=dharshini@karadiam.com
python3 scripts/mine_openalex.py --out data/authors_raw.csv --max-pages 3

# 2. Qualify. Ask Claude to run the qualify-authors skill.
#    -> data/authors_qualified.csv, data/rejected.csv

# 3. MANUAL: enrich contacts. See the bottleneck note below.
# 4. MANUAL: verify current employer. See the staleness note below.

# 5. Draft. Ask Claude to run the draft-outreach skill.
#    -> Gmail drafts or data/instantly_drafts.csv, plus data/draft_log.csv

# 6. MANUAL: review every draft against the ledger and the real paper. Then send.
```

Flags on the miner:

| Flag | Default | Notes |
| --- | --- | --- |
| `--config` | `config/queries.json` | |
| `--out` | `data/authors_raw.csv` | |
| `--from-year` | 2024 | |
| `--max-pages` | 3 | 200 works per page, per query. `0` means no cap. |
| `--search-mode` | `title-abstract` | `title-abstract` filters on `title_and_abstract.search`. `full` uses the full-text `search` parameter. |
| `--company-only` | off | Adds `authorships.institutions.type:company` server-side, and drops the +40 industry scoring term. |
| `--yield-table` | off | Writes a per-query company-author yield table to the given markdown path. |

### Search mode, and why the default is a problem

`full` searches the whole body of the paper, which is how a corrosion coating
paper matches a thermal query: the phrase appears once in a discussion section.

`title-abstract` fixes that, but it **ANDs every term in the query**. The seed
queries in `config/queries.json` were written as bag-of-words for full-text
search, so under AND semantics they over-constrain badly. Measured on the seed
set, from 2024, work counts collapse from 34,546 to 252, and four of the fifteen
queries return zero.

The queries need shortening to three or four terms before `title-abstract` is
usable at scale. `copper diamond composite heat sink CTE` returns nothing;
`copper diamond composite` would return plenty. Until that rewrite happens,
`title-abstract` buys precision at a recall cost that is too steep.

### Rate limits and the daily budget

**OpenAlex is metered, not unlimited.** The free tier carries a daily budget of
1,000 credits / $0.10, roughly $0.001 per `per-page=200` request, and it **resets
at midnight UTC**. Exhausting it returns 429 with a `Retry-After` of several
hours. This is a hard planning constraint, not a burst throttle you can sleep off:
a full 15-query multi-page sweep plus any exploratory probing can spend the day's
budget in a single session.

The script fails fast with a clear message when `Retry-After` exceeds 10 minutes,
rather than sitting in a retry loop for five hours. For ordinary burst 429s it
honors `Retry-After` with a 20 second floor. Do not run two instances at once.

Practical guidance: develop against `--max-pages 1`, spend the budget on one
considered full run per day, and check `x-ratelimit-remaining` if a run dies
early. Paid tiers are at https://openalex.org/pricing.

## The real bottleneck: email addresses

**OpenAlex gives names, ORCIDs, and affiliations. It does not give email
addresses.** There is no free path from an author record to a working inbox.

On a free Apollo plan, enrichment is manual and it is the slowest step in the
whole pipeline by a wide margin. Mining 15 queries takes minutes and can return
hundreds of authors; turning those into contactable people is hand work. Practical
consequence: **treat the score column as a work queue, not a list.** Enrich from
the top down and stop when you run out of time, rather than trying to enrich
everything.

Partial mitigations, all still manual: corresponding-author addresses are often
printed in the paper itself, ORCID profiles sometimes list a current employer, and
the LinkedIn DM variant in `draft-outreach` needs no email at all. The DM path is
frequently the faster route for T1 industry authors.

## Affiliations go stale

**Paper affiliations can be up to two years out of date.** Publication lag plus
job changes means a meaningful fraction of "industry" rows are people who have
since moved, and some "academic" rows are postdocs who are now in industry, which
is exactly the population we most want.

Verify current employer before drafting. A first line addressed to the wrong
company is worse than no email, because it proves the personalization was
automated. This is a named human gate (stage 4 in `CLAUDE.md`).

## What is untested

Honest status as of first build:

- **The miner has run** against the live OpenAlex API and produces a valid CSV.
  Cursor pagination, retry, and dedup logic have been exercised on a one-page run
  per query only. Deep multi-page runs are unproven.
- **Affiliation classification is a keyword list, not a model.** It will
  misclassify. Small institutes with no "university" or "institute" token land in
  `industry`; corporate research labs with academic-sounding names land in
  `academic`. Spot-check the `affiliation_type` column and expand the keyword list
  in `scripts/mine_openalex.py` as errors show up.
- **The scoring weights are a guess.** 40 for industry, 20 for first or last
  author, 8 per paper capped at 32, 8 for 2025 or later. Nothing has been
  calibrated against reply rates, because there are no reply rates yet. Revisit
  after the first 50 sends.
- **Both skills are unexercised.** `qualify-authors` and `draft-outreach` have
  never been run end to end on real data. Expect to tighten both after the first
  batch.
- **No asset exists.** A1 to A6 are all unchecked in the ledger. Until one is
  built and cleared, no draft may offer to send one.
- **Deduplication across runs is not implemented in the miner.** Re-running
  overwrites `authors_raw.csv`. Cross-run dedup lives in `already_drafted.csv` at
  the drafting stage only.
- **The competitor blocklist is substring matching on affiliation strings.**
  Subsidiaries and joint labs will get through. `qualify-authors` is the backstop.

## Note on SSL

Some Python.org macOS builds ship without a populated CA trust store, which makes
every HTTPS call fail with `CERTIFICATE_VERIFY_FAILED`. The miner handles this by
honoring `SSL_CERT_FILE` and falling back to `certifi` if it happens to be
installed. If neither is available, run
`/Applications/Python\ 3.x/Install\ Certificates.command` once.
