#!/usr/bin/env python3
"""Generate review-ready drafts per skills/draft-outreach/SKILL.md.

Drafts only. This script never sends and never touches Gmail.

Copy content is hand authored per paper, keyed by DOI, and hooks are written
only from the paper title. Nothing here generates a hook automatically, because
a hallucinated hook goes to the person who wrote the paper.

Every number is blocked. The claims ledger is unsigned, so no thermal,
dimensional, pricing, lead-time or qualification figure appears in any body.
The validator at the bottom enforces that mechanically, along with the em dash
ban, the one-question rule, the word count, and the sign-off.

Usage:
    python3 scripts/draft_outreach.py --sel /tmp/sel50.json \
        --out data/review_batch.csv --gaps data/needs_verification.md
"""

import argparse
import csv
import json
import os
import re
import sys

SIGNOFF = "Dharshini / Kara Labs / https://karalabs.ai"
OPENER = ("I am on the founding team at Kara Labs, a YC backed manufacturer of "
          "CVD diamond thermal materials.")

# Beat 5 variants. Pattern A ends on the approved question plus the approved
# brief line. Pattern B keeps the question in beat 4 and closes declaratively.
CLOSER_A = "Worth a quick conversation?\nHappy to send a short technical brief!"
CLOSER_B = "Happy to send a short technical brief either way."

# ---------------------------------------------------------------------------
# Hand-authored content, keyed by DOI.
#   hook   : single clause, defensible from the title alone
#   subject: device or topic, never Kara
#   beat2  : the paper hook sentence
#   beat3  : what Kara makes, sitting in their thermal path
#   beat4  : the diamond question, phrased as a statement under pattern A
#   pattern: A or B
# ---------------------------------------------------------------------------

PAPERS = {
    "https://doi.org/10.5281/zenodo.18816182": dict(
        hook="co-designed HBM integration and telemetry driven optimization for AI and HPC chiplet architectures",
        subject="thermal headroom in HBM chiplet co-design",
        beat2="Your work on HBM integration in AI and HPC chiplet architectures treats thermal telemetry as a design input rather than a downstream check.",
        beat3="We make polycrystalline diamond wafers and single crystal plates that sit in the package as a spreader, close to the die where the telemetry gets ugly.",
        beat4="I am curious whether diamond has come up as a spreader option there, or whether copper and ceramic remain the assumption.",
        pattern="A"),
    "https://doi.org/10.5281/zenodo.17709213": dict(
        hook="proposed a cryogenically stabilized lattice architecture for fault tolerant quantum computing",
        subject="substrate purity in cryogenic qubit lattices",
        beat2="Your architecture work on cryogenically stabilized lattices for fault tolerant quantum computing depends heavily on what the host substrate does to coherence.",
        beat3="We grow ultra high purity single crystal diamond with nitrogen held very low, which is the grade people use when the substrate itself has to stop being a noise source.",
        beat4="Has diamond come up as a substrate option in your architecture work, or is the platform settled on something else?",
        pattern="B"),
    "https://doi.org/10.4071/001c.128390": dict(
        hook="built cold sprayed copper diamond composites for semiconductor package thermal management",
        subject="cold spray copper diamond for package spreading",
        beat2="Your cold spray work on copper diamond composites for packages goes after the same problem we do, from the deposition side.",
        beat3="We supply copper diamond and aluminum diamond composite with CTE targeted to silicon or GaN, plus bulk diamond when the spreader carries more.",
        beat4="I am curious whether sourcing finished diamond composite has come up alongside growing it in house, or whether cold spray is the settled route.",
        pattern="A"),
    "https://doi.org/10.4071/001c.124091": dict(
        hook="worked on cold sprayed copper diamond composites for semiconductor package thermal management",
        subject="copper diamond composite in package thermal paths",
        beat2="Your cold spray work on copper diamond composites for semiconductor packages puts diamond loading right at the centre of the thermal path.",
        beat3="We manufacture copper diamond and aluminum diamond composite with CTE matched toward silicon or GaN, and bulk CVD diamond plates where the spreader needs more.",
        beat4="Has buying finished diamond composite come up as an alternative to depositing it, or is cold spray the direction you are committed to?",
        pattern="B"),
    "https://doi.org/10.35848/1347-4065/adc699": dict(
        hook="demonstrated low temperature bonding of diamond heat spreaders for advanced thermal management",
        subject="low temperature bonding of diamond spreaders",
        beat2="Your low temperature bonding work on diamond heat spreaders removes one of the practical reasons teams give up on diamond in the package.",
        beat3="We grow the spreaders themselves, single crystal CVD diamond plates and polycrystalline diamond wafers, with surface finish specified for bonding rather than left as grown.",
        beat4="I am curious what you are sourcing diamond from today, and whether plate flatness and finish are the limiting variables in that bond.",
        pattern="A"),
    "https://doi.org/10.37665/smctrsc40814": dict(
        hook="argued that chiplet architecture is the future of electronics packaging",
        subject="thermal limits on chiplet packaging",
        beat2="Your position on chiplet architecture as the direction for electronics packaging matches what we keep hearing from the thermal side of the same transition.",
        beat3="We make polycrystalline CVD diamond wafers and diamond plates that go into the package as spreaders, aimed at the hotspots that chiplet stacking concentrates.",
        beat4="Has diamond come up as a spreader option in the packaging roadmaps you work on, or is the assumption still copper and ceramic?",
        pattern="B"),
    "https://doi.org/10.1109/jetcas.2025.3590744": dict(
        hook="worked on heterogeneous integration for co-packaged optics",
        subject="thermal path in co-packaged optics integration",
        beat2="Your heterogeneous integration work for co-packaged optics sits where the optical engine and switch die share a thermal budget.",
        beat3="We make CVD diamond wafers and plates used as spreaders in that kind of package, where wavelength stability makes the gradient a functional problem, not just a reliability one.",
        beat4="I am curious whether diamond has come up as a spreader option there, or whether the default is still copper and ceramic.",
        pattern="A"),
    "https://doi.org/10.1109/tpel.2025.3530991": dict(
        hook="investigated creep fatigue interaction failure in IGBT die attach solder layers under power cycling",
        subject="die attach creep fatigue under power cycling",
        beat2="Your study of creep fatigue in IGBT die attach layers under power cycling points at the CTE mismatch driving the failure mode.",
        beat3="We make copper diamond and aluminum diamond composite with CTE targeted to the die rather than to the baseplate, which changes the strain the solder has to absorb.",
        beat4="Has a diamond composite baseplate come up as a route in your power cycling work, or is the material set fixed?",
        pattern="B"),
    "https://doi.org/10.4071/001c.129015": dict(
        hook="advanced vertical wire bonding for shielding and wafer level interconnect",
        subject="wafer level interconnect and package thermal path",
        beat2="Your vertical wire bonding work on shielding and wafer level interconnect touches the package real estate where the thermal path gets decided.",
        beat3="We supply diamond wafers and plates used as spreaders at wafer and package level, which has to coexist with the interconnect scheme.",
        beat4="I am curious whether diamond has come up as a spreader material in the packages you work on, or whether copper and ceramic are still the assumption.",
        pattern="A"),
    "https://doi.org/10.1093/mam/ozaf048.166": dict(
        hook="built a multi-modal quality control and failure analysis approach for metal lines in chiplet integration",
        subject="failure analysis of metal lines in chiplet integration",
        beat2="Your multi-modal failure analysis of metal lines in chiplet integration looks at exactly where thermal stress leaves its evidence.",
        beat3="We make diamond wafers and plates that go into these packages as spreaders, aimed at flattening the gradients that drive that damage.",
        beat4="Has diamond come up as a spreader option in the chiplet packages you analyse, or is the material set still copper and ceramic?",
        pattern="B"),
    "https://doi.org/10.1115/1.4068767": dict(
        hook="laid out the manufacturing challenges of hybrid bonding for chiplet heterogeneous integration",
        subject="hybrid bonding and chiplet thermal budgets",
        beat2="Your paper on the manufacturing challenges of hybrid bonding for chiplets is candid about how tight the process window gets.",
        beat3="We make polycrystalline diamond wafers and plates used as in package spreaders, where surface finish has to meet the bonding requirement.",
        beat4="I am curious whether diamond has come up as a spreader option in your hybrid bonding work, or whether copper and ceramic remain the default.",
        pattern="A"),
    "https://doi.org/10.1109/tpel.2026.3688002": dict(
        hook="estimated power module lifetime under compound test conditions",
        subject="power module lifetime under compound tests",
        beat2="Your lifetime estimation work on power modules under compound tests treats thermomechanical stress as the thing that actually sets service life.",
        beat3="We make copper diamond and aluminum diamond composite for baseplates, with CTE targeted toward the die stack so the cycling drives less strain into the joints.",
        beat4="Has a diamond composite baseplate come up as an option in your lifetime work, or is the material set fixed for now?",
        pattern="B"),
    "https://doi.org/10.1016/j.microrel.2025.115665": dict(
        hook="predicted power module lifetime in wind energy converters from temperature variation across a large area substrate",
        subject="large area substrate temperature spread in converters",
        beat2="Your lifetime work on wind converter modules keys off temperature variation across a large area substrate, a spreading problem before a cooling one.",
        beat3="We make copper diamond and aluminum diamond composite baseplates and bulk CVD diamond, aimed at flattening exactly that lateral spread.",
        beat4="I am curious whether diamond composite has come up as a baseplate option in that work, or whether the substrate set is fixed.",
        pattern="A"),
    "https://doi.org/10.1109/jssc.2025.0000000": dict(
        hook="worked on heterogeneous packaging for chiplet and memory integration",
        subject="chiplet and memory integration thermal path",
        beat2="Your work on heterogeneous packaging for chiplet and memory integration runs into the thermal ceiling that stacking memory next to logic creates.",
        beat3="We make polycrystalline CVD diamond wafers and single crystal plates used as in package spreaders, placed where the stack concentrates heat.",
        beat4="Has diamond come up as a spreader option in your packaging work, or is copper and ceramic still the default assumption?",
        pattern="B"),
}

# Papers whose DOI in the data differs from the placeholder above are filled in
# from the data at runtime; see PAPERS_BY_TITLE.
PAPERS_BY_TITLE = {
    "Heterogeneous Packaging Technologies for Chiplet and Memory Integration": dict(
        hook="worked on heterogeneous packaging for chiplet and memory integration",
        subject="chiplet and memory integration thermal path",
        beat2="Your work on heterogeneous packaging for chiplet and memory integration runs into the thermal ceiling that stacking memory beside logic creates.",
        beat3="We make polycrystalline CVD diamond wafers and single crystal plates used as in package spreaders, placed where the stack concentrates heat.",
        beat4="Has diamond come up as a spreader option in your packaging work, or is copper and ceramic still the default assumption?",
        pattern="B"),
    "Effects of the pin-fins cooler roughness on the thermo-fluid dynamics performance of a SiC power module": dict(
        hook="quantified how pin fin cooler roughness changes thermo-fluid performance in a SiC power module",
        subject="pin fin roughness in SiC module cooling",
        beat2="Your study on pin fin cooler roughness in a SiC power module works the convective side of a budget where the conduction path often dominates.",
        beat3="We make copper diamond and aluminum diamond composite baseplates, which change how much heat reaches those fins and how evenly it arrives.",
        beat4="I am curious whether diamond composite has come up as a baseplate option upstream of the cooler, or whether that layer is fixed.",
        pattern="A"),
    "SiC Power Module Packaging Using Printed Electronics Materials and Processes": dict(
        hook="built SiC power module packaging from printed electronics materials and processes",
        subject="printed process routes for SiC module packaging",
        beat2="Your work on SiC power module packaging with printed materials and processes rethinks the stack rather than optimising the existing one.",
        beat3="We make copper diamond and aluminum diamond composite with CTE targeted to the die, plus bulk CVD diamond where the spreader has to do more work.",
        beat4="Has a diamond composite layer come up as an option in that printed stack, or is the material set settled?",
        pattern="B"),
    "Enhancing Semiconductor Package Reliability through Mechanical Property Optimization of Pressureless Sintering Die Attach": dict(
        hook="optimized the mechanical properties of pressureless sintered die attach for package reliability",
        subject="sintered die attach and what sits under it",
        beat2="Your work on pressureless sintered die attach treats joint mechanics as the reliability lever, which puts weight on what the die is attached to.",
        beat3="We make single crystal diamond plates and diamond composite substrates with CTE targeted to the die, so the joint sees less mismatch.",
        beat4="I am curious whether diamond has come up as a substrate under the sintered joint in your work, or whether ceramic remains the default.",
        pattern="A"),
    "Direct Integration of Polycrystalline Diamond With 3C‐SiC for Enhanced Thermal Management in GaN HEMTs: Impact of Grain Structure": dict(
        hook="integrated polycrystalline diamond with SiC for GaN HEMT thermal management and tracked the effect of grain structure",
        subject="grain structure in diamond integrated GaN HEMTs",
        beat2="Your work integrating polycrystalline diamond with SiC for GaN HEMTs shows how much grain structure near the interface decides the result.",
        beat3="We grow polycrystalline CVD diamond wafers and single crystal plates, and we can talk concretely about nucleation side quality rather than just bulk numbers.",
        beat4="Has sourcing diamond externally come up alongside growing it in your process, or is in house growth the committed route?",
        pattern="B"),
    "Performance Enhancement of GaN Super-Lattice Castellated Field-Effect Transistors (SLCFETs) via Topside Integration of Nanocrystalline Diamond": dict(
        hook="integrated nanocrystalline diamond on the topside of GaN super-lattice castellated FETs",
        subject="topside diamond on GaN castellated FETs",
        beat2="Your topside nanocrystalline diamond work on GaN castellated FETs goes after the heat before it has to cross the whole stack.",
        beat3="We grow single crystal diamond plates and polycrystalline wafers, and we work on GaN on diamond where the diamond sits under the device.",
        beat4="I am curious whether a substrate side diamond route has been evaluated alongside the topside one, or whether topside is where the programme is committed.",
        pattern="A"),
    "Advances and Future Challenges in Monolithic 3D Integrated Logic, Power, and Optoelectronics Technologies for Tightly Integrated Systems": dict(
        hook="mapped the challenges of monolithic three dimensional integration across logic, power and optoelectronics",
        subject="thermal ceiling in monolithic 3D integration",
        beat2="Your work on monolithic three dimensional integration across logic, power and optoelectronics runs straight into the heat removal problem that stacking creates.",
        beat3="We make polycrystalline CVD diamond wafers and single crystal plates used as spreaders inside such stacks, where there is nowhere else for the heat to go sideways.",
        beat4="Has diamond come up as a spreader option in that integration work, or is the material set still copper and ceramic?",
        pattern="B"),
    "MPCVD diamond thin films as heat spreaders for back end of the line (BEOL) silicon chip fabrication": dict(
        hook="used MPCVD diamond thin films as heat spreaders in back end of line silicon fabrication",
        subject="diamond thin films in the BEOL stack",
        beat2="Your work putting MPCVD diamond thin films into back end of line fabrication moves the spreader inside the process flow rather than bolting it on later.",
        beat3="We grow single crystal diamond plates and polycrystalline wafers, supplied to a specified thickness and finish rather than as a standard part.",
        beat4="I am curious whether sourcing diamond externally has come up alongside growing it in line, or whether deposition is the committed route.",
        pattern="A"),
    "Advanced Mechanical Analysis Workflow for Chiplets Integration Predictive Design": dict(
        hook="built a predictive mechanical analysis workflow for chiplet integration",
        subject="predictive mechanical modelling for chiplet stacks",
        beat2="Your predictive mechanical workflow for chiplet integration models the warpage and stress that thermal mismatch drives through the stack.",
        beat3="We make CVD diamond wafers and diamond composite with CTE targeted to silicon or GaN, which changes the mismatch your model is being asked to absorb.",
        beat4="Has diamond come up as a material option in those workflows, or is the library still copper and ceramic?",
        pattern="B"),
    "Low-loss polymeric waveguides for co-packaged optics on glass substrates": dict(
        hook="developed low loss polymeric waveguides for co-packaged optics on glass substrates",
        subject="thermal stability around polymer waveguides on glass",
        beat2="Your low loss polymer waveguide work on glass sits in a package where a temperature gradient shows up directly as an optical penalty.",
        beat3="We make diamond wafers and plates used as in package spreaders, aimed at holding that gradient flat around the optical path.",
        beat4="I am curious whether diamond has come up as a spreader option next to the waveguide layer, or whether the thermal design stays with copper and ceramic.",
        pattern="A"),
    "Thermal-Stress-Induced Degradation Monitoring and Deep-Neural-Network-Driven Lifetime Prediction of IGBT Modules in a Two-Level Converter": dict(
        hook="monitored thermal stress degradation and predicted IGBT module lifetime in a two level converter",
        subject="thermal stress degradation in IGBT modules",
        beat2="Your degradation monitoring and lifetime prediction work on IGBT modules in a two level converter is built on how much thermal stress the stack accumulates.",
        beat3="We make copper diamond and aluminum diamond composite baseplates with CTE targeted to the die, which changes the stress the model is tracking.",
        beat4="Has a diamond composite baseplate come up as an option in that work, or is the module construction fixed?",
        pattern="B"),
    "Synergistic optimization of plasma uniformity and active species density in MPCVD systems: A study based on multiphysics simulation": dict(
        hook="simulated plasma uniformity and active species density in MPCVD reactors",
        subject="plasma uniformity in MPCVD reactors",
        beat2="Your multiphysics work on plasma uniformity and active species density in MPCVD systems is about the part of diamond growth that decides whether the result is usable.",
        beat3="We run MPCVD growth for single crystal plates and polycrystalline wafers aimed at thermal applications in electronics packaging.",
        beat4="I am curious whether your interest here is on the reactor side or the application side, since the two rarely sit in the same group.",
        pattern="A"),
    "Optimizing MPCVD systems for diamond growth through advanced microwave transmission theory": dict(
        hook="optimized MPCVD reactor design for diamond growth using microwave transmission theory",
        subject="microwave coupling in MPCVD growth",
        beat2="Your work optimizing MPCVD systems through microwave transmission theory targets the coupling that ends up limiting uniformity at scale.",
        beat3="We run MPCVD growth for single crystal diamond plates and polycrystalline wafers used as thermal materials in high power electronics.",
        beat4="Is your focus here on reactor design itself, or on the devices the diamond eventually goes into?",
        pattern="B"),
}

EM_DASH = "—"
EN_DASH = "–"


def build_body(first_name, paper):
    beat4 = paper["beat4"]
    closer = CLOSER_A if paper["pattern"] == "A" else CLOSER_B
    return "\n\n".join([
        "Hi %s," % first_name,
        OPENER,
        paper["beat2"],
        paper["beat3"],
        beat4,
        closer,
        SIGNOFF,
    ])


def body_word_count(body):
    """Words in the body, excluding the greeting line and the sign-off."""
    lines = body.split("\n\n")
    core = lines[1:-1]
    return len(" ".join(core).split())


def validate(body, row):
    """Return a list of rule violations. Empty means the draft is clean."""
    problems = []
    core = "\n".join(body.split("\n\n")[1:-1])

    wc = body_word_count(body)
    if not (80 <= wc <= 100):
        problems.append("word count %d outside 80-100" % wc)
    if EM_DASH in body or EN_DASH in body:
        problems.append("dash character present")
    qs = core.count("?")
    if qs != 1:
        problems.append("%d question marks, expected 1" % qs)
    if not body.endswith(SIGNOFF):
        problems.append("sign-off not exact")
    if re.search(r"\d", core):
        problems.append("digit in body, ledger is unsigned so no numbers allowed")
    for word in ("fascinating", "impressive", "excellent", "great paper",
                 "really enjoyed", "interesting paper"):
        if word in core.lower():
            problems.append("flattery: %s" % word)
    if re.search(r"pushes power density higher each generation", core, re.I):
        problems.append("banned phrase")
    if "one-pager" in core.lower() or "comparison sheet" in core.lower():
        problems.append("offers an unchecked asset")
    if paper_pattern_a(body) and "Happy to send a short technical brief!" not in body:
        problems.append("quick conversation closer without the brief line")
    return problems


def paper_pattern_a(body):
    return "Worth a quick conversation?" in body


def today():
    import datetime
    return datetime.date.today().isoformat()


def read_existing(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return [dict(r) for r in csv.DictReader(fh)]


def append_rows(path, cols, rows):
    """Append rows, writing a header only when creating the file."""
    if not rows:
        return
    new = not os.path.exists(path)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        if new:
            w.writeheader()
        w.writerows(rows)


def dedupe_keys(path):
    """Keys already drafted: ORCID where present, else name plus affiliation."""
    keys = set()
    for r in read_existing(path):
        orcid = (r.get("orcid") or "").strip()
        if orcid:
            keys.add(("orcid", orcid))
        keys.add(("name", (r.get("author") or "").strip().lower(),
                  (r.get("affiliation") or "").strip().lower()))
    return keys


def row_keys(r):
    out = []
    orcid = (r.get("orcid") or "").strip()
    if orcid:
        out.append(("orcid", orcid))
    out.append(("name", (r.get("author") or "").strip().lower(),
                (r.get("affiliation") or "").strip().lower()))
    return out


def norm_title(t):
    """Normalize a title for matching: unicode dashes, spacing, case."""
    t = (t or "")
    for ch in ("‐", "‑", "‒", "–", "—", "−"):
        t = t.replace(ch, "-")
    t = re.sub(r"\s+", " ", t).strip().lower()
    return t


PAPERS_BY_NORM_TITLE = None


def lookup_paper(row):
    """DOI first, then normalized-title prefix. Never guesses across papers."""
    global PAPERS_BY_NORM_TITLE
    if PAPERS_BY_NORM_TITLE is None:
        PAPERS_BY_NORM_TITLE = {norm_title(k): v for k, v in PAPERS_BY_TITLE.items()}
    p = PAPERS.get(row["paper_doi"])
    if p:
        return p
    nt = norm_title(row["paper_title"])
    p = PAPERS_BY_NORM_TITLE.get(nt)
    if p:
        return p
    # Titles in the data are sometimes truncated relative to the authored key.
    for key, val in PAPERS_BY_NORM_TITLE.items():
        if nt and (key.startswith(nt[:60]) or nt.startswith(key[:60])):
            return val
    return None


def first_name(full):
    full = full.strip()
    if "," in full:                       # "Surname, Given"
        part = full.split(",", 1)[1].strip()
    else:
        part = full.split()[0]
    part = part.split()[0] if part else full
    # Initials are not a usable greeting. Short given names like "Yu" are.
    if part.endswith(".") or len(part.strip(".")) <= 1:
        return ""
    return part


COLUMNS = ["rank", "tier", "class", "author", "affiliation", "affil_suspect",
           "product_line", "paper_title", "paper_doi", "paper_year", "hook",
           "subject", "body", "current_employer_verified", "email",
           "linkedin_url", "approved"]


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--sel", default="/tmp/sel50.json")
    ap.add_argument("--out", default=os.path.join(here, "data", "review_batch.csv"))
    ap.add_argument("--log", default=os.path.join(here, "data", "draft_log.csv"))
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--drafted", default=os.path.join(here, "data", "already_drafted.csv"))
    args = ap.parse_args()

    with open(args.sel, encoding="utf-8") as fh:
        sel = json.load(fh)

    seen = dedupe_keys(args.drafted)
    out_rows, log_rows, skipped, drafted_src = [], [], [], []
    already = 0
    rank = 0
    for r in sel:
        if rank >= args.limit:
            break
        if any(k in seen for k in row_keys(r)):
            already += 1
            continue
        paper = lookup_paper(r)
        fn = first_name(r["author"])
        if paper is None or not fn:
            skipped.append((r["author"], r["paper_title"],
                            "no adjudicated hook" if paper is None else "no usable first name"))
            continue
        body = build_body(fn, paper)
        problems = validate(body, r)
        if problems:
            skipped.append((r["author"], r["paper_title"], "; ".join(problems)))
            continue
        rank += 1
        for k in row_keys(r):
            seen.add(k)
        out_rows.append({
            "rank": rank,
            "tier": r["tier"],
            "class": r["query_class"],
            "author": r["author"],
            "affiliation": r["affiliation"],
            "affil_suspect": r["affil_suspect"],
            "product_line": r["product_line"],
            "paper_title": r["paper_title"],
            "paper_doi": r["paper_doi"],
            "paper_year": r["paper_year"],
            "hook": paper["hook"],
            "subject": paper["subject"],
            "body": body,
            "current_employer_verified": "",
            "email": "",
            "linkedin_url": "",
            "approved": "",
        })
        drafted_src.append(r)
        log_rows.append({
            "date": "", "author": r["author"], "orcid": r["orcid"],
            "affiliation": r["affiliation"], "tier": r["tier"],
            "product_line": r["product_line"], "asset": "NONE",
            "channel": "email-draft", "subject": paper["subject"],
            "paper_doi": r["paper_doi"], "hook": paper["hook"],
            "word_count": body_word_count(body), "claims_used": "none",
            "drafted_by": "draft_outreach.py",
        })

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)

    # Append, never overwrite. Existing rows keep the columns a human filled in
    # (email, approved, and so on), and new people continue the rank sequence.
    log_cols = ["date", "author", "orcid", "affiliation", "tier", "product_line",
                "asset", "channel", "subject", "paper_doi", "hook", "word_count",
                "claims_used", "drafted_by"]
    append_rows(args.log, log_cols, log_rows)

    # The dedupe ledger for every future run.
    append_rows(args.drafted, ["author", "orcid", "affiliation", "paper_doi", "date"],
                [{"author": r["author"], "orcid": r.get("orcid", ""),
                  "affiliation": r["affiliation"], "paper_doi": r["paper_doi"],
                  "date": today()} for r in drafted_src])

    existing = read_existing(args.out)
    for i, row in enumerate(out_rows):
        row["rank"] = len(existing) + i + 1
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(existing + out_rows)

    print("drafted %d new, skipped %d, already drafted %d"
          % (len(out_rows), len(skipped), already), file=sys.stderr)
    for a, t, why in skipped:
        print("  SKIP %-28s %-60s %s" % (a[:28], t[:60], why), file=sys.stderr)


if __name__ == "__main__":
    main()
