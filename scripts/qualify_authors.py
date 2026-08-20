#!/usr/bin/env python3
"""Deterministic implementation of skills/qualify-authors/SKILL.md.

The skill is the spec; this script implements the mechanical parts of it
(rejection, product-line mapping, asset assignment, tiering, suspect-affiliation
detection) so that a thousand rows get the same rules applied the same way.

The `hook` column is NOT written here. A hook requires reading the paper title
and judging what is defensible, which is the part the skill deliberately leaves
to a human or an agent. Hooks are adjudicated separately and merged in.

Standard library only.

Usage:
    python3 scripts/qualify_authors.py \
        --in data/authors_raw.csv \
        --out data/authors_qualified.csv \
        --rejected data/rejected.csv
"""

import argparse
import csv
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Rejection
# ---------------------------------------------------------------------------

# Direct competitors, plus other firms that already grow or sell CVD diamond.
# An author at a diamond supplier is not a prospect, whatever their paper says.
COMPETITOR_PAT = re.compile(
    r"element\s*six|element\s*6|de\s*beers|debeers|diamond\s*foundry|"
    r"\barm\s*(ltd|limited|holdings)|"
    r"applied\s+diamond|diamond\s+materials|akash\s+systems|"
    r"advanced\s+diamond\s+tech|sp3\s+diamond|audiatec|"
    r"\bii-vi\b|diamond\s+(product|technolog|innovat)", re.I)

GEMOLOGY_PAT = re.compile(
    r"\bgemolog|\bgemstone|\bjewel|\bgem\s+(quality|grade|grading|trade)|"
    r"\bcut\s+diamond\b|\bfancy\s+colou?r|\bdiamond\s+grading", re.I)

ABRASIVE_PAT = re.compile(
    r"\babrasive|\bgrinding\b|\bpolishing\s+(pad|slurry|compound)|"
    r"\bdrill\s+bit|\bcutting\s+tool|\bwear\s+resistan|\btribolog|"
    r"\bsaw\s+blade|\bmachining\s+of\b|"
    r"\bcutting\s+of\b|\btungsten\s+carbide|\bpcd\s+tool|"
    r"water\s*jet|\bturning\b|\bmilling\b|\btool\s+wear", re.I)

REVIEW_PAT = re.compile(
    r"^\s*(a\s+)?(review|survey|overview|perspective|tutorial)\b|"
    r"\breview\s*:|\b(a|systematic|comprehensive|critical|brief)\s+review\b|"
    r"\breview\s+(of|on)\b|\bstate[\s-]of[\s-]the[\s-]art\s+review\b|"
    r"\brecent\s+(advances|progress|developments)\b|"
    r"\badvances\s+and\s+challenges\b|\bopportunities\s+and\s+challenges\b|"
    r"\bchallenges\s+and\s+opportunities\b|\broadmap\b", re.I)

# Subject matter with no plausible device thermal path.
OFFTOPIC_PAT = re.compile(
    r"\bsolar\s+(thermal|collector|pond)|\bconcentrated\s+solar|"
    r"\bbuilding\s+(envelope|energy)|\bnuclear\s+(core|reactor|fuel)\b|"
    r"\bfood\b|\bagricultur|\btextile\b|\bpharmaceutic|\bdrug\s+delivery|"
    r"\bcorrosion\s+protection\s+coating|\bfertiliz|\bbiodiesel|"
    r"\bwastewater|\bsoil\b|\bcement\b|\bconcrete\b", re.I)

# ---------------------------------------------------------------------------
# Suspect affiliations (OpenAlex disambiguation errors)
# ---------------------------------------------------------------------------

# A journal role parsed into the institution field, and similar non-employers.
EDITOR_PAT = re.compile(
    r"\beditor|\beditorial|\bjournal\b|\bpublish|\bpress\b|\bproceedings\b|"
    r"\bconference\b|\bsociety\s+of\b|\bassociation\s+of\b", re.I)

# Phantom institutions observed in this corpus.
PHANTOM_AFFILIATIONS = (
    "innovation team",
    "research team",
    "research group",
    "project team",
    "study group",
    "working group",
    "breakthrough",
    "at bristol",
    "independent researcher",
    "retired",
    "freelance",
    "private",
    "none",
    "n/a",
    "unknown",
)

CORPORATE_MARKER_PAT = re.compile(
    r"\b(inc|ltd|llc|gmbh|corp|corporation|co|plc|s\.?p\.?a|s\.?a|a/s|ab|oy|"
    r"pte|b\.?v|n\.?v|sas|kk|kabushiki|holdings|group|technologies|systems|"
    r"semiconductor|electronics|laboratories|labs|industries|solutions)\b"
    r"|\(.*\)", re.I)

# Reused from the miner: an affiliation the miner classified as a company whose
# NAME reads academic is a type/name mismatch and therefore suspect.
ACADEMIC_NAME_PAT = re.compile(
    r"\buniversity|universit|\bcollege\b|\binstitute\s+of\s+technology|"
    r"\bpolytechnic|politecnico|\bécole|\becole\b|hochschule|"
    r"\bacademy\s+of\s+sciences|\bcnrs\b|max\s+planck|fraunhofer|"
    r"national\s+lab|state\s+key\s+laborator|key\s+laborator|"
    r"\bfaculty\s+of|\bschool\s+of|\bdepartment\s+of|\bgraduate\s+school",
    re.I)


def affil_suspect(affiliation, affiliation_type, country):
    """Return (flag, reason). Flag is 'Y' or 'N'."""
    a = (affiliation or "").strip()
    if not a:
        return "Y", "empty affiliation"
    low = a.lower()

    if EDITOR_PAT.search(a):
        return "Y", "journal or editorial role parsed as institution"
    for p in PHANTOM_AFFILIATIONS:
        if low == p or low.startswith(p + " ") or low == p + ".":
            return "Y", "phantom institution: %s" % p
    if affiliation_type == "industry" and ACADEMIC_NAME_PAT.search(a):
        return "Y", "typed as company but named like an academic body"
    # A short generic name with no corporate marker and no country is usually a
    # mis-resolution rather than a real employer.
    if not country and len(a.split()) <= 3 and not CORPORATE_MARKER_PAT.search(a):
        return "Y", "generic short name, no country, no corporate marker"
    return "N", ""


# ---------------------------------------------------------------------------
# Product line and asset
# ---------------------------------------------------------------------------

PRODUCT_RULES = [
    ("GaN-on-diamond", re.compile(
        r"gan[\s\-/]*(on)?[\s\-/]*diamond|gan/diamond|hemt.*(diamond|near[\s-]junction)|"
        r"thermal\s+boundary\s+(resistance|conductance).*(gan|diamond)|"
        r"near[\s-]junction", re.I)),
    ("UHP-and-engineered-SCD", re.compile(
        r"\bnv\s+cent|nitrogen[\s-]vacancy|colou?r\s+cent|quantum\s+(sens|register|emitter|"
        r"comput|photonic|spin)|single\s+photon|spin\s+qubit|diamond\s+photonic|"
        r"ultra[\s-]high[\s-]purity", re.I)),
    ("single-crystal-CVD-diamond-plate", re.compile(
        r"single\s+crystal\s+diamond|\bscd\b|mpcvd|microwave\s+plasma.*diamond|"
        r"laser\s+diode.*(submount|thermal|package)|submount|die\s+attach|"
        r"heat\s+spreader", re.I)),
    ("polycrystalline-CVD-diamond-wafer", re.compile(
        r"polycrystalline\s+diamond|\bpcd\b|diamond\s+(wafer|film|coating).*"
        r"(thermal|heat|spread)|wafer[\s-]level|chiplet|2\.5d|3d\s+(stack|integrat)|"
        r"co[\s-]packaged\s+optic|photonic\s+(integrat|packag)", re.I)),
    ("aluminum-diamond-composite", re.compile(
        r"aluminum[\s-]diamond|aluminium[\s-]diamond|al[\s/-]diamond|"
        r"lightweight.*(heat\s+sink|thermal)|airborne|space[\s-]based|avionic", re.I)),
    ("copper-diamond-composite", re.compile(
        r"copper[\s-]diamond|cu[\s/-]diamond|metal\s+matrix\s+composite|"
        r"baseplate|igbt|power\s+module|traction\s+inverter|\bcte\b|"
        r"thermal\s+fatigue|heat\s+sink", re.I)),
]

ASSET_RULES = [
    ("A6", re.compile(
        r"\bnv\s+cent|nitrogen[\s-]vacancy|colou?r\s+cent|quantum|single\s+photon|"
        r"qubit|ultra[\s-]high[\s-]purity", re.I)),
    ("A5", re.compile(
        r"co[\s-]packaged\s+optic|photonic\s+(integrat|packag|chiplet)|"
        r"silicon\s+photonic|optical\s+(transceiver|interconnect)|\bcpo\b", re.I)),
    ("A3", re.compile(
        r"laser\s+diode|diode\s+laser|submount|pump\s+laser|vcsel|"
        r"semiconductor\s+laser", re.I)),
    ("A4", re.compile(
        r"\bigbt\b|power\s+module|traction\s+inverter|baseplate|\bev\b|"
        r"electric\s+vehicle|thermal\s+fatigue|\bsic\s+module", re.I)),
    ("A1", re.compile(
        r"\bgan\b.*(rf|radar|amplifier|hemt|power\s+amplifier)|\bmmic\b|"
        r"\brf\s+power|radar|\bpa\b\s+module", re.I)),
    ("A2", re.compile(
        r"chiplet|accelerator|\bhpc\b|\bai\b\s+(chip|package|accelerat)|"
        r"2\.5d|3d\s+(stack|integrat)|data\s+cent|advanced\s+packag|"
        r"heterogeneous\s+integrat", re.I)),
]

EXPORT_REVIEW_COUNTRIES = {
    "CN": "China",
    "RU": "Russia",
    "IR": "Iran",
    "KP": "North Korea",
    "SY": "Syria",
    "CU": "Cuba",
    "BY": "Belarus",
    "VE": "Venezuela",
}


def map_product_line(text):
    for name, pat in PRODUCT_RULES:
        if pat.search(text):
            return name
    return "NONE"


def map_asset(text):
    for name, pat in ASSET_RULES:
        if pat.search(text):
            return name
    return "NONE"


def assign_tier(row, suspect):
    """T1/T2/T3/T4 per the skill, with suspect rows forced to T4."""
    if suspect == "Y":
        return "T4"
    industry = row.get("industry_flag") == "1"
    first_last = row.get("author_position") in ("first", "last")
    try:
        n = int(row.get("n_relevant_papers") or 0)
    except ValueError:
        n = 0
    if industry and first_last and n >= 2:
        return "T1"
    if industry:
        return "T2"
    if row.get("affiliation_type") == "academic" and first_last:
        return "T3"
    return "T4"


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=os.path.join(here, "data", "authors_raw.csv"))
    ap.add_argument("--out", default=os.path.join(here, "data", "authors_qualified.csv"))
    ap.add_argument("--rejected", default=os.path.join(here, "data", "rejected.csv"))
    ap.add_argument("--config", default=os.path.join(here, "config", "queries.json"))
    args = ap.parse_args()

    with open(args.config, encoding="utf-8") as fh:
        cfg = json.load(fh)
    query_class = {}
    for e in cfg.get("queries") or []:
        if isinstance(e, dict):
            query_class[e.get("query", "")] = e.get("class", "")

    with open(args.inp, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    in_cols = list(rows[0].keys()) if rows else []
    extra = ["query_class", "tier", "product_line", "asset", "hook",
             "affil_suspect", "affil_suspect_reason", "export_review", "export_note"]
    out_cols = in_cols + extra
    rej_cols = in_cols + ["reject_reason"]

    qualified, rejected = [], []
    for r in rows:
        title = r.get("paper_title") or ""
        venue = r.get("paper_venue") or ""
        aff = r.get("affiliation") or ""
        subject = "%s %s" % (title, venue)

        reason = None
        if COMPETITOR_PAT.search(aff):
            reason = "competitor affiliation"
        elif GEMOLOGY_PAT.search(subject):
            reason = "gemology / jewelry"
        elif ABRASIVE_PAT.search(subject):
            reason = "abrasive / non-device diamond"
        elif OFFTOPIC_PAT.search(subject):
            reason = "off-topic match, no device thermal path"
        elif REVIEW_PAT.search(title):
            reason = "review-only, no primary work"

        if reason:
            out = dict(r)
            out["reject_reason"] = reason
            rejected.append(out)
            continue

        suspect, suspect_reason = affil_suspect(
            aff, r.get("affiliation_type"), r.get("country"))
        country = (r.get("country") or "").upper()

        out = dict(r)
        out["query_class"] = query_class.get(r.get("topic_query", ""), "")
        out["affil_suspect"] = suspect
        out["affil_suspect_reason"] = suspect_reason
        out["tier"] = assign_tier(r, suspect)
        out["product_line"] = map_product_line(subject)
        out["asset"] = map_asset(subject)
        out["hook"] = ""  # adjudicated separately, never auto-generated
        if country in EXPORT_REVIEW_COUNTRIES:
            out["export_review"] = "TRUE"
            out["export_note"] = ("affiliation country %s: human export review "
                                  "required before any contact"
                                  % EXPORT_REVIEW_COUNTRIES[country])
        else:
            out["export_review"] = "FALSE"
            out["export_note"] = ""
        if out["product_line"] == "NONE" and out["tier"] in ("T1", "T2"):
            out["tier"] = "T4"
        qualified.append(out)

    for path, cols, data in ((args.out, out_cols, qualified),
                             (args.rejected, rej_cols, rejected)):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(data)

    tiers = {}
    for r in qualified:
        tiers[r["tier"]] = tiers.get(r["tier"], 0) + 1
    print("input rows: %d" % len(rows), file=sys.stderr)
    print("qualified: %d -> %s" % (len(qualified), args.out), file=sys.stderr)
    for t in ("T1", "T2", "T3", "T4"):
        print("  %s: %d" % (t, tiers.get(t, 0)), file=sys.stderr)
    print("  suspect affiliations forced to T4: %d"
          % sum(1 for r in qualified if r["affil_suspect"] == "Y"), file=sys.stderr)
    print("  export review flagged: %d"
          % sum(1 for r in qualified if r["export_review"] == "TRUE"), file=sys.stderr)
    print("rejected: %d -> %s" % (len(rejected), args.rejected), file=sys.stderr)
    rj = {}
    for r in rejected:
        rj[r["reject_reason"]] = rj.get(r["reject_reason"], 0) + 1
    for k, v in sorted(rj.items(), key=lambda kv: -kv[1]):
        print("  %s: %d" % (k, v), file=sys.stderr)
    t1 = [r for r in qualified if r["tier"] == "T1"]
    cl = {}
    for r in t1:
        cl[r["query_class"]] = cl.get(r["query_class"], 0) + 1
    print("T1 by class: %s" % cl, file=sys.stderr)


if __name__ == "__main__":
    main()
