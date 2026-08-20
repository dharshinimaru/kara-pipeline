---
name: draft-outreach
description: Draft personalized outreach for T1 and T2 rows from data/authors_qualified.csv into Gmail drafts or an Instantly-compatible CSV. Drafts only, never sends. Enforces the claims ledger on every number and logs the source paper DOI for human verification.
---

# Draft outreach

**Input:** `data/authors_qualified.csv` (tier T1 and T2 only)
**Outputs:** Gmail drafts, or `data/instantly_drafts.csv`, plus `data/draft_log.csv`

## Absolute rules

1. **Never send.** No send action, no scheduled send, no sequence activation, no
   Apollo or Instantly campaign start. Gmail drafts stay drafts. CSV rows stay in
   a file. A human presses send. If asked to send, decline and explain.
2. **The claims ledger governs every number.** Read `claims/verified_claims.md`
   before drafting. A thermal, dimensional, pricing, lead-time, or qualification
   figure may appear only if it is a VERIFIED row. If a draft wants a number that
   is not cleared, write the sentence without the number and append a line to
   `data/claims_gaps.csv`. Never approximate, never hedge into it ("roughly",
   "on the order of", "several times"), never move a blocked number into the
   subject line.
3. **Dedupe first.** Check `data/already_drafted.csv` before drafting anything.
   Match on ORCID where present, otherwise on normalized name plus affiliation.
   Skip anyone already there. A second cold email from the same company reads as
   a machine.
4. **T3 and T4 are out of scope here.** T3 gets a non-commercial research note
   (see `qualify-authors`). T4 gets nothing.
5. **Export-flagged rows are skipped** until a human clears `export_review`.

## Email structure

Five beats. **80 to 100 words total**, sign-off excluded. Count them.

1. **Credibility opener.** One line. Names Kara Labs as YC-backed. That is the
   whole job of this line: establish we are a real company in one sentence and
   move on.
2. **The paper hook.** Name their actual paper or the device in it. Use the `hook`
   column. This is the sentence that proves a human read something.
3. **What Kara makes**, framed to sit in the thermal path they wrote about. Use
   the `product_line` column. Not a product catalog. The one thing that belongs
   where their heat is going.
4. **A direct question** about whether diamond has come up as a substrate or
   spreader option in their work.
5. **Closer.**

**If the closer is "worth a quick conversation?", the very next line must be
"Happy to send a short technical brief!"** No exceptions, no rewording.

## Sign-off

Exactly this, on its own lines, with no title of any kind:

```
Dharshini / Kara Labs / https://karalabs.ai
```

## Prohibited in copy

- **Em dashes.** Anywhere. Use a comma, a period, or a rewrite.
- **Any title after my name.** Not Founder, not Co-founder, not BD, not nothing
  in a nice font. The sign-off is the sign-off.
- The phrase **"as X pushes power density higher each generation"** and any close
  variant of it.
- **Any uncleared number.** See rule 2.
- **More than one question per email.** Beat 4 is the question. Beat 5 may end in
  a question mark only if it replaces beat 4's question rather than adding to it.
  Count the question marks. There is one.
- **Flattery about the paper.** No "fascinating", "impressive", "excellent work",
  "I really enjoyed", "great paper". Naming what the paper did is the compliment.
  Saying it was interesting is filler that every templated email also contains.
- Offering an asset whose box is unchecked in the ledger.

## Subject lines

Reference the device or the paper topic, never Kara, never a product. Should read
like a colleague wrote it, not a marketer. Lowercase or sentence case. No
brackets, no emoji, no "Quick question", no company name.

Good:
- `GaN/diamond interface resistance`
- `submount thermal in your 976nm pump work`
- `hotspot spreading in stacked accelerator packages`

Bad:
- `Kara Labs x [Company]`
- `Solving your thermal challenges`
- `Quick question about heat spreaders`

## LinkedIn DM variant

Different medium, different register. Short chat bubbles, casual, no sign-off, no
subject, no links.

- Opens with 👋 and a personal acknowledgment of the paper.
- Two or three short bubbles maximum.
- Same ledger rules on numbers. Same prohibition on em dashes and flattery.
- Closes with exactly this binary question:

```
has diamond ever come up as a substrate option in your work, or is copper/ceramic still the default assumption?
```

The binary question does its work by being answerable in four words. Do not add a
second question after it.

## Logging

Every draft appends a row to `data/draft_log.csv`:

```
date,author,orcid,affiliation,tier,product_line,asset,channel,subject,paper_doi,hook,word_count,claims_used,drafted_by
```

`paper_doi` is the point of the log. A human opens the DOI, reads the real paper,
and checks the hook against it. A hook that cannot be checked this way should not
have been written. `claims_used` lists the ledger row IDs (V1, V5, and so on) that
appear in the copy, or `none`.

After drafting, append the drafted people to `data/already_drafted.csv`.

## Self-check before handing drafts over

Run this on every draft. Report failures rather than quietly fixing and moving on.

- [ ] 80 to 100 words, sign-off excluded
- [ ] Exactly one question mark in the body
- [ ] Zero em dashes
- [ ] Sign-off is exactly `Dharshini / Kara Labs / https://karalabs.ai`, no title
- [ ] Every number traces to a VERIFIED ledger row, listed in `claims_used`
- [ ] If closer is "worth a quick conversation?", next line is "Happy to send a short technical brief!"
- [ ] Hook names a specific finding or device and matches the DOI in the log
- [ ] No flattery adjectives about the paper
- [ ] Subject references the device or topic, not Kara
- [ ] Not present in `already_drafted.csv`
- [ ] Nothing was sent

Report to the user: how many drafts, by tier and channel, how many people were
skipped as duplicates, and every line written to `data/claims_gaps.csv`. The gaps
list is the most useful output of a drafting run, because it says what engineering
should go measure next.
