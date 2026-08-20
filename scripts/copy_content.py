#!/usr/bin/env python3
"""Hand-authored copy, in Dharshini's voice.

Voice reference, taken from her own sent outreach:

    Hi Crt,

    For Red Pitaya's compact test and measurement instruments, has diamond
    come up as a way to improve the local thermal path where density and
    stability matter? Kara's single-crystal CVD diamond runs 2200+ W/m/K ...

    Happy to share more if it's relevant.

    Best,
    Dharshini Maru

Shape: no preamble, straight into the question, names their company and their
product, one question, roughly 50 to 70 words.

Per paper we author only two things:
    work    what they build or study, in their words not ours
    benefit the thermal outcome, phrased as "improve X where Y matters"

The product sentence is per product line, not per paper, the same way she
reuses one standard line.

CLEARED NUMBERS: only claims signed in claims/verified_claims.md may appear.
As of 2026-08-20 that is V1 alone (SCD 2200+ W/m/K), signed by Dharshini.
The "5x copper" and "under 0.1 K/W" claims are NOT cleared and must not appear.
"""

# Claims cleared for use in copy. Key is the ledger row id.
CLEARED_CLAIMS = {
    "V1": "2200+ W/m·K",          # single-crystal CVD diamond
    "V5": "1800+ W/m·K",          # polycrystalline CVD diamond wafer
    "V7": "500 to 800+ W/m·K",    # copper-diamond, configuration-dependent
    "V8": "350 to 500+ W/m·K",    # aluminum-diamond, configuration-dependent
    "V11": "under 5 ppb",         # UHP SCD nitrogen
}

# One standard sentence per product line. Numbers appear only where a ledger
# row is signed; the rest describe fit without claiming performance.
PRODUCT_SENTENCES = {
    "single-crystal-CVD-diamond-plate": (
        "Kara's single-crystal CVD diamond runs 2200+ W/m·K, and our metallized "
        "submounts are built to slot into existing designs.", ["V1"]),
    "polycrystalline-CVD-diamond-wafer": (
        "Kara's polycrystalline CVD diamond wafers run 1800+ W/m·K, built to slot "
        "into existing package designs.", ["V5"]),
    "copper-diamond-composite": (
        "Kara's copper-diamond composite runs 500 to 800+ W/m·K depending on "
        "configuration, with CTE targeted to the die rather than the baseplate.",
        ["V7"]),
    "aluminum-diamond-composite": (
        "Kara's aluminum-diamond composite runs 350 to 500+ W/m·K depending on "
        "configuration, with CTE targeted to the die where weight is the "
        "constraint.", ["V8"]),
    "GaN-on-diamond": (
        "Kara works on GaN-on-diamond, with the diamond under the device rather "
        "than added on top.", []),
    "UHP-and-engineered-SCD": (
        "Kara grows ultra-high-purity single-crystal diamond with nitrogen under "
        "5 ppb, for cases where the substrate itself has to stop adding noise.",
        ["V11"]),
}

# work / benefit / hook / subject, keyed by DOI where stable, else by title.
BY_DOI = {
    "https://doi.org/10.5281/zenodo.18816182": dict(
        work="HBM chiplet integration work",
        benefit="improve the near-die thermal path where your telemetry shows the hotspots",
        hook="co-designed HBM integration and telemetry driven optimization for AI and HPC chiplet architectures",
        subject="thermal headroom in HBM chiplet co-design"),
    "https://doi.org/10.5281/zenodo.17709213": dict(
        work="fault-tolerant quantum architecture work",
        benefit="hold coherence where the host substrate is what limits it",
        hook="proposed a cryogenically stabilized lattice architecture for fault tolerant quantum computing",
        subject="substrate purity in cryogenic qubit lattices"),
    "https://doi.org/10.4071/001c.128390": dict(
        ask="For %s %s, has buying finished diamond composite come up alongside depositing it in house?",
        work="cold-sprayed copper-diamond work",
        benefit="get diamond loading into the package without owning the deposition step",
        hook="built cold sprayed copper diamond composites for semiconductor package thermal management",
        subject="cold spray copper diamond for package spreading"),
    "https://doi.org/10.4071/001c.124091": dict(
        ask="For %s %s, has buying finished diamond composite come up alongside depositing it in house?",
        work="copper-diamond composite work",
        benefit="get diamond into the thermal path as a finished part rather than a deposited layer",
        hook="worked on cold sprayed copper diamond composites for semiconductor package thermal management",
        subject="copper diamond composite in package thermal paths"),
    "https://doi.org/10.35848/1347-4065/adc699": dict(
        ask="For %s %s, are you sourcing diamond externally, or is growth in house the committed route?",
        work="low-temperature diamond bonding work",
        benefit="source spreaders where flatness and finish are specified for the bond rather than left as grown",
        hook="demonstrated low temperature bonding of diamond heat spreaders for advanced thermal management",
        subject="low temperature bonding of diamond spreaders"),
    "https://doi.org/10.37665/smctrsc40814": dict(
        work="chiplet packaging roadmap",
        benefit="handle the hotspots that chiplet stacking concentrates",
        hook="argued that chiplet architecture is the future of electronics packaging",
        subject="thermal limits on chiplet packaging"),
    "https://doi.org/10.1109/jetcas.2025.3590744": dict(
        work="co-packaged optics integration",
        benefit="hold the gradient flat where wavelength stability depends on it",
        hook="worked on heterogeneous integration for co-packaged optics",
        subject="thermal path in co-packaged optics integration"),
    "https://doi.org/10.1109/tpel.2025.3530991": dict(
        work="IGBT die-attach reliability work",
        benefit="cut the CTE mismatch that drives creep fatigue in the solder",
        hook="investigated creep fatigue interaction failure in IGBT die attach solder layers under power cycling",
        subject="die attach creep fatigue under power cycling"),
    "https://doi.org/10.4071/001c.129015": dict(
        work="wafer-level interconnect work",
        benefit="add spreading at package level without fighting the interconnect scheme",
        hook="advanced vertical wire bonding for shielding and wafer level interconnect",
        subject="wafer level interconnect and package thermal path"),
    "https://doi.org/10.1093/mam/ozaf048.166": dict(
        work="chiplet failure analysis work",
        benefit="flatten the gradients that leave the damage you are imaging",
        hook="built a multi-modal quality control and failure analysis approach for metal lines in chiplet integration",
        subject="failure analysis of metal lines in chiplet integration"),
    "https://doi.org/10.1115/1.4068767": dict(
        work="hybrid bonding work for chiplets",
        benefit="add spreading where surface finish has to meet the bonding window",
        hook="laid out the manufacturing challenges of hybrid bonding for chiplet heterogeneous integration",
        subject="hybrid bonding and chiplet thermal budgets"),
    "https://doi.org/10.1109/tpel.2026.3688002": dict(
        work="power module lifetime work",
        benefit="reduce the thermomechanical stress that sets service life",
        hook="estimated power module lifetime under compound test conditions",
        subject="power module lifetime under compound tests"),
    "https://doi.org/10.1016/j.microrel.2025.115665": dict(
        work="wind converter power modules",
        benefit="flatten the temperature spread across a large-area substrate",
        hook="predicted power module lifetime in wind energy converters from temperature variation across a large area substrate",
        subject="large area substrate temperature spread in converters"),
}

BY_TITLE = {
    "Heterogeneous Packaging Technologies for Chiplet and Memory Integration": dict(
        work="chiplet and memory integration work",
        benefit="pull heat out of the stack where memory sits beside logic",
        hook="worked on heterogeneous packaging for chiplet and memory integration",
        subject="chiplet and memory integration thermal path"),
    "Effects of the pin-fins cooler roughness on the thermo-fluid dynamics performance of a SiC power module": dict(
        work="SiC power module cooling work",
        benefit="change how much heat reaches the fins, and how evenly it arrives",
        hook="quantified how pin fin cooler roughness changes thermo-fluid performance in a SiC power module",
        subject="pin fin roughness in SiC module cooling"),
    "SiC Power Module Packaging Using Printed Electronics Materials and Processes": dict(
        work="printed SiC module packaging",
        benefit="put a CTE-matched layer under the die in a rebuilt stack",
        hook="built SiC power module packaging from printed electronics materials and processes",
        subject="printed process routes for SiC module packaging"),
    "Enhancing Semiconductor Package Reliability through Mechanical Property Optimization of Pressureless Sintering Die Attach": dict(
        work="sintered die-attach reliability work",
        benefit="cut the mismatch the sintered joint has to absorb",
        hook="optimized the mechanical properties of pressureless sintered die attach for package reliability",
        subject="sintered die attach and what sits under it"),
    "Direct Integration of Polycrystalline Diamond With 3C‐SiC for Enhanced Thermal Management in GaN HEMTs: Impact of Grain Structure": dict(
        ask="For %s %s, has sourcing diamond externally come up alongside growing it, or is in-house growth the committed route?",
        work="diamond-on-SiC integration for GaN HEMTs",
        benefit="source diamond where nucleation-side grain quality is specified rather than inherited",
        hook="integrated polycrystalline diamond with SiC for GaN HEMT thermal management and tracked the effect of grain structure",
        subject="grain structure in diamond integrated GaN HEMTs"),
    "Performance Enhancement of GaN Super-Lattice Castellated Field-Effect Transistors (SLCFETs) via Topside Integration of Nanocrystalline Diamond": dict(
        ask="For %s %s, has a substrate-side diamond route been evaluated alongside the topside one?",
        work="topside diamond work on GaN castellated FETs",
        benefit="take the heat from underneath instead of across the stack",
        hook="integrated nanocrystalline diamond on the topside of GaN super-lattice castellated FETs",
        subject="topside diamond on GaN castellated FETs"),
    "Advances and Future Challenges in Monolithic 3D Integrated Logic, Power, and Optoelectronics Technologies for Tightly Integrated Systems": dict(
        work="monolithic three-dimensional integration work",
        benefit="move heat sideways where a stack gives it nowhere else to go",
        hook="mapped the challenges of monolithic three dimensional integration across logic, power and optoelectronics",
        subject="thermal ceiling in monolithic 3D integration"),
    "MPCVD diamond thin films as heat spreaders for back end of the line (BEOL) silicon chip fabrication": dict(
        ask="For %s %s, has sourcing plates to a specified thickness and finish come up alongside growing them in line?",
        work="BEOL diamond heat spreader work",
        benefit="source plates to a specified thickness and finish rather than growing every one in line",
        hook="used MPCVD diamond thin films as heat spreaders in back end of line silicon fabrication",
        subject="diamond thin films in the BEOL stack"),
    "Advanced Mechanical Analysis Workflow for Chiplets Integration Predictive Design": dict(
        work="predictive mechanical modelling for chiplets",
        benefit="cut the CTE mismatch your warpage models have to absorb",
        hook="built a predictive mechanical analysis workflow for chiplet integration",
        subject="predictive mechanical modelling for chiplet stacks"),
    "Low-loss polymeric waveguides for co-packaged optics on glass substrates": dict(
        work="polymer waveguide work on glass",
        benefit="hold the gradient flat around the optical path",
        hook="developed low loss polymeric waveguides for co-packaged optics on glass substrates",
        subject="thermal stability around polymer waveguides on glass"),
    "Thermal-Stress-Induced Degradation Monitoring and Deep-Neural-Network-Driven Lifetime Prediction of IGBT Modules in a Two-Level Converter": dict(
        work="IGBT degradation and lifetime work",
        benefit="reduce the thermal stress your models are tracking",
        hook="monitored thermal stress degradation and predicted IGBT module lifetime in a two level converter",
        subject="thermal stress degradation in IGBT modules"),
    "Synergistic optimization of plasma uniformity and active species density in MPCVD systems: A study based on multiphysics simulation": dict(
        ask="For %s %s, is the focus the reactor itself, or the devices the diamond ends up in?",
        work="MPCVD reactor modelling",
        benefit="source finished plates rather than carrying the growth step yourselves",
        hook="simulated plasma uniformity and active species density in MPCVD reactors",
        subject="plasma uniformity in MPCVD reactors"),
    "Optimizing MPCVD systems for diamond growth through advanced microwave transmission theory": dict(
        ask="For %s %s, is the focus the reactor itself, or the devices the diamond ends up in?",
        work="MPCVD reactor design work",
        benefit="source finished plates rather than carrying the growth step yourselves",
        hook="optimized MPCVD reactor design for diamond growth using microwave transmission theory",
        subject="microwave coupling in MPCVD growth"),
}
