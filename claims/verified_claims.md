# Kara Labs claims ledger

This file governs every number that may appear in agent-written copy.

**Rule: if a thermal, dimensional, pricing, lead-time, or qualification figure is
not in this file with status VERIFIED, it may not appear in a draft.** A draft
that wants a blocked number gets written without the number, and the gap is
logged for engineering. There is no "round it down to be safe" path. The audience
is thermal engineers; one fabricated number permanently closes an account.

Status values:

| Status | Meaning | May appear in copy? |
| --- | --- | --- |
| VERIFIED | Sourced to a document a human has signed off on | Yes |
| INTERNAL | Real internal figure, but not defensible standing alone | No, unless a human explicitly approves the framing |
| NEEDS SOURCE | Claim we would like to make and cannot yet support | No |

Owner and Date are deliberately blank. A human fills them in. A blank Owner on a
VERIFIED row means the sign-off has not actually happened yet, and reviewers
should treat that row as suspect.

---

## VERIFIED

Source: Kara Labs preliminary spec booklet, July 2026.

| # | Claim | Value | Status | Source | Owner | Date |
| --- | --- | --- | --- | --- | --- | --- |
| V1 | Single-crystal CVD diamond plate thermal conductivity | 2200+ W/m·K | VERIFIED | Spec booklet, Jul 2026 | Dharshini | 2026-08-20 |
| V2 | SCD plate lateral size | 2 to 20 mm | VERIFIED | Spec booklet, Jul 2026 |  |  |
| V3 | SCD plate thickness | 0.3 to 0.5 mm | VERIFIED | Spec booklet, Jul 2026 |  |  |
| V4 | SCD plate polished surface roughness | Ra <2 to 30 nm | VERIFIED | Spec booklet, Jul 2026 |  |  |
| V5 | Polycrystalline CVD diamond wafer thermal conductivity | 1800+ W/m·K | VERIFIED | Spec booklet, Jul 2026 |  |  |
| V6 | Polycrystalline wafer diameter | Up to 4 inch as-grown, or up to 6 inch | VERIFIED | Spec booklet, Jul 2026 |  |  |
| V7 | Copper-diamond composite thermal conductivity | 500 to 800+ W/m·K, configuration-dependent | VERIFIED | Spec booklet, Jul 2026 |  |  |
| V8 | Aluminum-diamond composite thermal conductivity | 350 to 500+ W/m·K, configuration-dependent | VERIFIED | Spec booklet, Jul 2026 |  |  |
| V9 | Cu-diamond and Al-diamond CTE | Targets matched to Si or to GaN/GaAs | VERIFIED | Spec booklet, Jul 2026 |  |  |
| V10 | GaN layer thickness on diamond | 0.5 to 5 µm | VERIFIED | Spec booklet, Jul 2026 |  |  |
| V11 | Ultra-high-purity SCD nitrogen content | <5 ppb | VERIFIED | Spec booklet, Jul 2026 |  |  |

**Booklet caveat that copy must respect:** the spec booklet describes these as
*suggested starting points, not fixed design limits.* Copy must not present them
as guaranteed, contractual, or as a datasheet spec. Acceptable framing is "our
current plates run 2200+ W/m·K" or "typical starting point." Unacceptable framing
is "guaranteed 2200 W/m·K" or "spec'd at."

Configuration-dependent values (V7, V8) must never be quoted as a single number.
Quote the range, or quote nothing.

---

## INTERNAL

| # | Claim | Value | Status | Why it is not VERIFIED | Owner | Date |
| --- | --- | --- | --- | --- | --- | --- |
| I1 | GaN-on-diamond thermal resistance | <0.1 K/W | INTERNAL | A thermal resistance with no stated footprint and no stated heat load is meaningless to a thermal engineer, and quoting it bare reads as marketing innumeracy to exactly the audience we are targeting. **Must not lead an email.** May only be used by a human, in a technical brief, alongside the device footprint, the dissipated power, and the measurement or simulation method. |  |  |

---

## NEEDS SOURCE (blocked)

None of these may appear in any draft, in any paraphrase, in any subject line.

| # | Claim | Status | What would clear it | Owner | Date |
| --- | --- | --- | --- | --- | --- |
| N1 | "5x better than copper" | NEEDS SOURCE | A side-by-side measurement of a Kara part against a copper reference of stated geometry, same method, same lab, with the comparison basis (bulk k? spreading resistance? junction temperature?) stated explicitly. Bulk k ratio alone does not license "5x better," because "better" implies system performance. |  |  |
| N2 | "60% lighter than copper" | NEEDS SOURCE | Measured or computed mass for a specific Kara part geometry against the same geometry in copper, with the density figures and the part cited. |  |  |
| N3 | Junction-temperature delta vs AlN | NEEDS SOURCE | A thermal measurement or validated simulation on a named device, stated footprint, stated power, stated boundary conditions, with the AlN baseline described. |  |  |
| N4 | Junction-temperature delta vs CuMo | NEEDS SOURCE | Same as N3, with the CuMo grade and composition stated. |  |  |
| N5 | Junction-temperature delta vs copper | NEEDS SOURCE | Same as N3, with the copper alloy and thickness stated. |  |  |
| N6 | Any lead time (weeks, quarters, "fast turnaround") | NEEDS SOURCE | A written commitment from ops covering current queue, by product line and by volume tier. Until then, drafts say we can talk timelines, not what they are. |  |  |
| N7 | Any price, price range, or cost comparison | NEEDS SOURCE | An approved price list, by product line and volume, with validity dates. |  |  |
| N8 | Any reliability claim (cycles, hours, MTTF, delamination resistance) | NEEDS SOURCE | Completed reliability testing with the protocol, sample size, and failure criterion documented. |  |  |
| N9 | Any qualification claim (AEC-Q, MIL-STD, ISO, space heritage, "qualified for") | NEEDS SOURCE | The certificate or audit report, with scope and issuing body. Claiming a qualification we do not hold is not a copy problem, it is a legal one. |  |  |
| N10 | Yield, defect density, or process capability figures | NEEDS SOURCE | Production data over a stated window with the measurement definition. |  |  |
| N11 | Customer names, logos, design wins, or "used by" | NEEDS SOURCE | Written permission from the customer. |  |  |

**Gap logging.** When a draft would have wanted a blocked number, append a line to
`data/claims_gaps.csv` with columns `date,claim_id_or_description,draft_context,
prospect,requested_by`. That file is the engineering queue for what to go measure.
A blocked claim that gets requested ten times is a measurement worth funding.

---

## Approved comparison assets

One asset per application, not per prospect. Assets live in `claims/assets/`.
An unchecked box means the asset does not exist yet and may not be offered in a
draft.

| ID | Application | Exists |
| --- | --- | --- |
| A1 | GaN RF and radar power amplifier | [ ] |
| A2 | AI accelerator and chiplet package | [ ] |
| A3 | High-power laser diode submount | [ ] |
| A4 | IGBT and EV power module baseplate | [ ] |
| A5 | Co-packaged optics and photonics | [ ] |
| A6 | Quantum and UHP SCD | [ ] |

Every asset is subject to this same ledger. An asset containing a NEEDS SOURCE
number is a blocked asset, not an approved one.
