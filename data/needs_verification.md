# Needs verification: numbers the drafts wanted and could not use

Generated from the first 50-draft batch. Every draft in `data/review_batch.csv`
was written with `claims_used = none`, because the claims ledger
(`claims/verified_claims.md`) is unsigned: every VERIFIED row has a blank Owner
and Date, so nothing in it is actually cleared for outbound.

The result is that all 50 emails carry the paper hook and no evidence. That is
the correct behaviour under the design constraint, and it is also the single
biggest weakness in the batch. This file is the engineering queue that would fix
it.

Ordered by how many drafts each gap affected.

---

## 1. Bulk thermal conductivity, all product lines

**Affected:** all 50 drafts.
**What the copy wanted:** one sentence establishing that diamond conducts heat
better than what they use now.
**What it says instead:** "We make polycrystalline diamond wafers and single
crystal plates" with no performance statement at all.

The values already exist in the ledger as V1, V5, V7, V8 (SCD 2200+ W/m·K,
polycrystalline 1800+ W/m·K, Cu-diamond 500 to 800+, Al-diamond 350 to 500+).
**They are blocked only because no human has signed the rows.**

**To clear:** an owner initials and dates V1, V5, V7, V8 in the ledger, confirming
the July 2026 spec booklet numbers are current and that the booklet's own
"suggested starting points, not fixed design limits" caveat is reflected in how
copy phrases them. This is a signature, not a measurement, and it unblocks the
entire batch.

---

## 2. A comparison against the incumbent material

**Affected:** 27 drafts (every copper-diamond, aluminum-diamond, and baseplate
draft, plus the die attach and power module ones).
**What the copy wanted:** "against the AlN or CuMo you are using now, this
changes X."
**What it says instead:** the drafts assert a CTE target and stop.

Blocked as N1, N3, N4, N5. These are genuine measurements, not signatures.

**To clear:** one side-by-side against a named incumbent, same method, same lab,
with footprint, dissipated power, and boundary conditions stated. A single
credible A/B on one representative geometry would serve most of these 27 drafts.
Priority: AlN first, since it appears most often in the target papers, then CuMo.

---

## 3. Junction temperature delta on a real device

**Affected:** 12 drafts (GaN HEMT, SLCFET, GaN-on-diamond, RF, laser diode).
**What the copy wanted:** the number that actually persuades a device engineer,
a junction temperature reduction on a device like theirs.
**What it says instead:** general statements about where the diamond sits.

Blocked as N3, N4, N5. Related: I1, the internal <0.1 K/W GaN-on-diamond figure,
which is unusable as written because it carries no footprint and no heat load.

**To clear:** measure or simulate one representative GaN device with and without
a diamond substrate, and publish footprint, dissipated power, boundary
conditions, and method alongside the result. Restating I1 with those three
quantities attached would convert it from INTERNAL to usable, and it is probably
the highest-leverage single item on this list for the GaN audience.

---

## 4. Reliability and thermal cycling data

**Affected:** 9 drafts (IGBT lifetime, power cycling, creep fatigue, wind
converter, sintered die attach).

Every one of these recipients studies failure over cycles. Their entire paper is
about what breaks and when. A materials claim with no cycling data behind it is
weak in front of exactly this audience.

Blocked as N8.

**To clear:** thermal cycling or power cycling on a diamond composite baseplate
with protocol, sample size, and failure criterion documented. Until then these
nine drafts are asking a question rather than making an argument, which is
survivable but not strong.

---

## 5. Available sizes and formats

**Affected:** 18 drafts (anything where the recipient works at wafer scale or
with a specific die footprint).
**What the copy wanted:** whether we can supply at the size their process needs.
**What it says instead:** "supplied to a specified thickness and finish rather
than as a standard part", which is a dimensional claim carefully phrased to avoid
stating a dimension.

Values exist as V2, V3, V4, V6. Blocked only for lack of signature.

**To clear:** same as item 1, sign V2, V3, V4, V6. Note that V6 (up to 4 inch
as-grown, up to 6 inch) is the one most likely to decide whether a wafer-scale
recipient keeps reading, and it is also the one most likely to be out of date, so
confirm it against current capability rather than the booklet.

---

## 6. Lead time

**Affected:** 0 drafts directly, but it is the first question a positive reply
will ask.

Blocked as N6. No draft mentions timing.

**To clear:** a written statement from ops on current queue by product line and
volume tier. Needed before replies start arriving, not after.

---

## 7. Comparison assets A1 to A6

**Affected:** all 50 drafts.

Every asset box in the ledger is unchecked, so no draft offers one. The drafts
offer "a short technical brief", which is approved copy and a different artifact.

**To clear:** build the assets. On this batch's distribution, priority order is
A2 (AI accelerator and chiplet package, 21 drafts), A4 (IGBT and EV power module
baseplate, 15 drafts), A5 (co-packaged optics, 4 drafts), A6 (quantum and UHP
SCD, 3 drafts), A1 (GaN RF and radar, 1 draft). A3 did not appear in this batch.

Each asset is subject to this same ledger. An asset containing a NEEDS SOURCE
number is a blocked asset.

---

## Summary for the engineering conversation

Two signatures and one measurement would transform this batch:

1. **Sign the ledger rows that already have values** (V1 to V11). Cost: an hour
   of someone's attention. Unblocks a performance statement in all 50 drafts.
2. **One A/B against AlN** on a representative geometry, fully specified. Cost:
   one test campaign. Unblocks 27 drafts.
3. **One GaN junction temperature result** with footprint and power stated. Cost:
   one device measurement. Unblocks the 12 drafts aimed at the highest-value
   audience, and rescues the I1 figure.

Everything else on this list can wait.
