---
name: qualify-authors
description: Qualify raw OpenAlex author rows into a tiered, product-mapped prospect list. Reads data/authors_raw.csv and writes data/authors_qualified.csv plus data/rejected.csv with a reason on every rejected row. Use after scripts/mine_openalex.py and before draft-outreach.
---

# Qualify authors

Turn `data/authors_raw.csv` into a list a human would actually work.

**Input:** `data/authors_raw.csv` (output of `scripts/mine_openalex.py`)
**Outputs:** `data/authors_qualified.csv`, `data/rejected.csv`

Every input row ends up in exactly one output file. Nothing is silently dropped.
`rejected.csv` carries all input columns plus a `reject_reason` column, and the
reason is specific ("gemology venue, no device angle") not generic ("not a fit").

## Working method

Judge from what the mining script captured plus, where needed, the paper's public
abstract. Respect source terms: use OpenAlex metadata and open-access abstracts
only. Do not scrape or store paywalled full text. If a call cannot be made from
title, venue, and abstract, that is itself the answer, and the row goes to T4.

Never infer or invent a job title. The raw data has affiliations, not titles. A
paper does not tell you someone is a "Principal Thermal Engineer," and writing
that down creates a fake fact that will end up in an email.

## Step 1: reject

Reject and log a reason:

- **Competitors and their affiliates.** Element Six, De Beers, Diamond Foundry,
  Arm. The mining script drops the obvious cases; catch what it missed, including
  subsidiaries and joint labs.
- **Jewelry and gemology.** Gem grading, colored diamond, inclusion imaging for
  gemstones, jewelry supply chain. Reason: `gemology / jewelry`.
- **Diamond as abrasive or gemstone with no device angle.** Cutting tools, drill
  bits, polishing compounds, diamond-like carbon as a wear coating with no
  electronic or thermal-management framing. Reason: `abrasive / non-device diamond`.
- **Review-only authors.** The author's only relevant appearance is a review,
  survey, perspective, or book chapter, with no primary work. They are writing
  about the field, not building in it. Reason: `review-only, no primary work`.
- **Off-topic capture.** The search matched on a stray phrase and the paper has
  nothing to do with thermal management of devices. Reason: `off-topic match`.

**Export-restricted countries are flagged, not dropped.** Set
`export_review = TRUE` and keep the row in `authors_qualified.csv` with a note in
`export_note`. A human decides. Silently deleting people by nationality is both a
compliance decision we are not qualified to make automatically and a good way to
delete the wrong people. No draft goes out to a flagged row until the flag is
cleared by a human.

## Step 2: map to a product line

Map from **paper subject matter**, never from job title or employer.

| Signal in the paper | Product line |
| --- | --- |
| GaN HEMT self-heating, near-junction thermal, GaN/diamond interface, TBR at a GaN boundary | `GaN-on-diamond` |
| Small-area high heat flux, laser diode submount, RF die attach, spreader directly under a die | `single-crystal-CVD-diamond-plate` |
| Quantum sensing, NV centers, color centers, optical-grade or low-nitrogen diamond, diamond photonics | `UHP-and-engineered-SCD` |
| Wafer-level integration, larger-area spreaders, packaging substrates, thick film diamond | `polycrystalline-CVD-diamond-wafer` |
| Heat sinks and baseplates where CTE mismatch and thermal fatigue dominate, power modules | `copper-diamond-composite` |
| Same as above but weight-constrained: airborne, space, portable, mobile platforms | `aluminum-diamond-composite` |

If two fit, pick the one closest to the thermal path the paper actually studies.
If none fit, `product_line = NONE` and the row goes to T4.

## Step 3: assign an asset

One of A1 to A6 from `claims/verified_claims.md`, or `NONE`.

| Asset | Assign when the paper is about |
| --- | --- |
| A1 | GaN RF and radar power amplifiers |
| A2 | AI accelerators, chiplets, 2.5D/3D package thermals |
| A3 | High-power laser diodes, submounts, optical pump sources |
| A4 | IGBT modules, EV traction inverters, baseplates |
| A5 | Co-packaged optics, photonic integration thermals |
| A6 | Quantum devices, NV centers, ultra-high-purity SCD |

An asset that is unchecked in the ledger does not exist yet. Assign it as a
routing label, but a draft may not offer to send it until the box is checked.

## Step 4: tier

| Tier | Rule |
| --- | --- |
| T1 | Industry affiliation, first or last author, and 2 or more relevant papers |
| T2 | Industry affiliation, any author position |
| T3 | Academic affiliation, first or last author |
| T4 | Everything else |

**T3 academics get a non-commercial research note, never a sales email.** The
note acknowledges the specific work, says what Kara makes, and offers material
for research use or a technical conversation. No pitch, no asset offer, no
call-to-action about buying. Academics talk to each other, and a sales email into
a research group is how a materials startup gets a reputation before it has
customers.

T4 rows stay in `authors_qualified.csv` but are not drafted.

## Step 5: write the hook

`hook` is a **single clause** naming the specific finding or device in their
paper. Not the field, not the topic. The specific thing.

Good:
- `measured thermal boundary resistance at the GaN/diamond interface with an AlN nucleation layer`
- `modeled hotspot spreading in a 3D-stacked accelerator package`
- `characterized submount thermal droop in a 976 nm pump diode`

Bad:
- `works on thermal management` (topic, not finding)
- `is a leading expert in GaN` (flattery, and unverifiable)
- `is probably evaluating substrate options` (speculation)

Hard rule: **the hook must be defensible from the title and abstract alone.** If
you cannot write it without speculating about what they concluded, what they need,
or what they are working on now, leave `hook` blank and drop the row to T4. A blank
hook is a fine outcome. A hallucinated hook is an unrecoverable one, because the
recipient is the person who wrote the paper and will notice immediately.

## Output columns

All input columns, plus:

| Column | Contents |
| --- | --- |
| `tier` | T1, T2, T3, T4 |
| `product_line` | one of the six, or NONE |
| `asset` | A1 to A6, or NONE |
| `hook` | single clause, or blank |
| `export_review` | TRUE / FALSE |
| `export_note` | why it was flagged, if flagged |

## Self-check before finishing

- Every input row appears in exactly one output file.
- Every rejected row has a specific reason.
- No row has an invented job title.
- No hook contains a number (numbers are the ledger's business, not the hook's).
- No hook asserts anything not in the title or abstract.
- Every T3 row is marked for the research-note path, not the sales path.
- Report counts by tier and the reject breakdown to the user.
