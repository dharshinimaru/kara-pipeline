# Kara Labs outreach pipeline

Context for every session in this repo.

## What Kara Labs sells

YC-backed manufacturer of CVD diamond thermal materials for high-power
electronics and semiconductor packaging. Six product lines:

1. Single-crystal CVD diamond plates
2. Ultra-high-purity and engineered SCD
3. Polycrystalline CVD diamond wafers
4. Copper-diamond composite
5. Aluminum-diamond composite
6. GaN-on-diamond

Founding team member running this: Dharshini. All outbound signs as her, with no
title.

## The thesis

Apollo title-filter prospecting into cold email is not producing replies. Titles
are a bad proxy for who evaluates substrate materials.

The people who publish on near-junction thermal management, GaN-on-diamond, and
thermal boundary resistance are the people who actually evaluate substrate
materials. Sourcing them from publication metadata beats sourcing them from job
titles, and their own paper is a personalization hook that cannot be templated.

So: OpenAlex works metadata in, tiered and hooked prospects out, drafts for a
human to review.

## Hard rules

1. **The claims ledger governs all numbers.** `claims/verified_claims.md` is the
   only source of thermal, dimensional, pricing, lead-time, and qualification
   figures in copy. VERIFIED only. Anything else gets written around and logged to
   `data/claims_gaps.csv`. The audience is thermal engineers. One fabricated
   number permanently closes an account, and they will catch it, because we are
   deliberately emailing the people who measure these things for a living.
2. **Never send.** This pipeline produces drafts. Gmail drafts, CSV rows, nothing
   else. No sequence starts, no scheduled sends, no campaign activation. A human
   presses send, every time.
3. **One asset per application, not per prospect.** Six assets, A1 to A6, listed
   in the ledger. We do not build a custom deck for a prospect. An unchecked asset
   does not exist and may not be offered.
4. **Cite the paper, not the person.** The hook references what the work found or
   what device it studied. Not the author's career, seniority, reputation, or
   inferred job. Never invent a job title.
5. **Respect source terms.** OpenAlex metadata is CC0. Use it. Use open
   abstracts. Do not scrape or store paywalled full text, and do not route around
   a paywall to enrich a row.
6. **OpenAlex has a daily budget.** The free tier is 1,000 credits per day,
   resetting at midnight UTC. A full sweep can spend it. Develop against
   `--max-pages 1` and treat a full run as a once-a-day action to plan, not a
   command to re-run casually.

## Stages and gates

| # | Stage | Runs how | Human gate |
| --- | --- | --- | --- |
| 1 | Mine OpenAlex | `scripts/mine_openalex.py` | No |
| 2 | Qualify and tier | `skills/qualify-authors` | No |
| 3 | Contact enrichment | Manual | **Yes**, and it is the bottleneck |
| 4 | Verify current employer | Manual | **Yes**, affiliations run up to two years stale |
| 5 | Draft copy | `skills/draft-outreach` | No |
| 6 | Numbers in copy | Ledger check | **Yes**, blocked by default |
| 7 | Export-flagged rows | Manual review | **Yes** |
| 8 | Send | Human only | **Yes**, always, no exceptions |
| 9 | New claim or asset | Human sign-off | **Yes** |

Autonomous on research, qualification, and drafting. Hard-gated on numbers and
sending.

## Copy rules

- 80 to 100 words, five beats: credibility opener naming Kara as YC-backed, paper
  hook, what Kara makes in their thermal path, one direct question about diamond
  as a substrate or spreader, closer.
- If the closer is "worth a quick conversation?", the next line is "Happy to send
  a short technical brief!"
- Sign-off exactly: `Dharshini / Kara Labs / https://karalabs.ai`
- No em dashes anywhere.
- No title after the name.
- Never the phrase "as X pushes power density higher each generation".
- One question per email. Count the question marks.
- No flattery about the paper being fascinating, impressive, or excellent.
- Subject lines reference the device or paper topic, not Kara, and read like a
  colleague wrote them.

## ICP exclusions

- **Competitors:** Element Six, De Beers, Diamond Foundry, Arm. Dropped at mining.
- **Jewelry and gemology** of any kind.
- **Diamond as abrasive or gemstone** with no device or thermal angle.
- **Review-only authors** with no primary work in the space.
- **Export-restricted countries:** flagged for human review, never silently
  dropped. No draft until a human clears the flag.
- **T3 academics:** in scope, but they receive a non-commercial research note,
  never a sales email. T4 receives nothing.
