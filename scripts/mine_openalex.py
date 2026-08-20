#!/usr/bin/env python3
"""Mine author records from OpenAlex works metadata.

Sources people from publication metadata rather than job titles: the authors who
publish on near-junction thermal management are the people who actually evaluate
substrate materials.

OpenAlex is free, requires no API key, and its metadata is CC0. We only ever touch
the works API. We never fetch or store paywalled full text.

Standard library only. No pip installs.

Usage:
    export OPENALEX_MAILTO=you@yourdomain.com
    python3 scripts/mine_openalex.py --max-pages 1 --out data/authors_raw.csv
"""

import argparse
import csv
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API_URL = "https://api.openalex.org/works"
PER_PAGE = 200

# Politeness: OpenAlex asks for a real contact address in exchange for the fast pool.
DEFAULT_SLEEP = 0.4
MAX_RETRIES = 6
BACKOFF_BASE = 3.0
# OpenAlex answers a burst with 429 and expects a real pause, not another poke.
RATE_LIMIT_MIN_WAIT = 20.0
# A Retry-After longer than this means a spent daily budget, not a burst.
BUDGET_EXHAUSTED_SECONDS = 600.0
TIMEOUT = 45

# ---------------------------------------------------------------------------
# Affiliation classification
# ---------------------------------------------------------------------------

# Substring match, lowercased. Deliberately broad: a false "academic" label costs
# us a scoring point, a false "industry" label wastes a founder's afternoon.
ACADEMIC_KEYWORDS = (
    "university",
    "universite",
    "université",
    "universidad",
    "universidade",
    "universita",
    "università",
    "universitat",
    "universität",
    "universiteit",
    "universitet",
    "univ.",
    "college",
    "institute of technology",
    "institut de technologie",
    "polytechnic",
    "politecnico",
    "polytechnique",
    "école",
    "ecole",
    "escuela",
    "hochschule",
    "fachhochschule",
    "academy of sciences",
    "chinese academy",
    "russian academy",
    "cnrs",
    "inria",
    "cea ",
    "cea-",
    "max planck",
    "fraunhofer",
    "helmholtz",
    "leibniz",
    "national laboratory",
    "national lab",
    "sandia",
    "oak ridge",
    "los alamos",
    "lawrence livermore",
    "lawrence berkeley",
    "argonne",
    "brookhaven",
    "naval research laboratory",
    "air force research laboratory",
    "army research laboratory",
    "kaist",
    "kist",
    "postech",
    "tsinghua",
    "peking",
    "zhejiang",
    "fudan",
    "jiao tong",
    "harbin institute",
    "tokyo institute",
    "riken",
    "aist",
    "nims",
    "csic",
    "cnr ",
    "imec",
    "vtt",
    "sintef",
    "tno",
    "etri",
    "itri",
    "a*star",
    "nanyang technological",
    "national institute",
    "research center",
    "research centre",
    "research institute",
    "institute of physics",
    "institute of materials",
    "school of engineering",
    "faculty of",
    "department of physics",
    "graduate school",
    "epfl",
    "eth zurich",
    "kth royal",
    "chalmers",
    "tu delft",
    "tu wien",
    "tu dresden",
    "rwth",
    "karlsruhe institute",
    "indian institute",
    "iit ",
    "academia sinica",
    "istituto",
    "instituto",
    "institut ",
    "institute of science and technology",
    "nanosystems institute",
    "paul scherrer",
    "national academies",
    "foundation for research",
    "state key laboratory",
    "key laboratory",
    "department of",
    "school of",
    "centre for",
    "center for",
    "academy of",
    "observatory",
    "teaching hospital",
)

# Checked BEFORE the academic list. A corporate marker wins, so "Toyota Research
# Institute" or "Raith GmbH, Institute Park" does not get filed as academic.
CORPORATE_MARKERS = (
    " inc.",
    " inc,",
    " inc)",
    " ltd",
    " llc",
    " gmbh",
    " corp",
    " corporation",
    " co., ltd",
    " plc",
    " s.p.a",
    " s.a.",
    " a/s",
    " ab,",
    " oy,",
    " pte",
    " b.v.",
    " n.v.",
    " sas",
    " kk",
    "technologies",
    "semiconductor",
    "microelectronics",
    "electronics co",
)

# OpenAlex institution.type values. Only `company` is industry for our purposes:
# national labs, government research centers, and nonprofits behave like academia
# for outreach, in that they publish and do not purchase like a product team.
INDUSTRY_INSTITUTION_TYPES = ("company",)

# Direct competitors and firms we do not want in a prospect list. Any authorship
# whose affiliation matches is dropped outright, not just downscored.
BLOCKED_AFFILIATIONS = (
    "element six",
    "element 6",
    "de beers",
    "debeers",
    "diamond foundry",
    "arm ltd",
    "arm limited",
    "arm holdings",
)


def classify_affiliation(affiliation, institution_type=None):
    """Return 'academic' or 'industry' for an affiliation.

    OpenAlex publishes an institution `type` (education, facility, government,
    company, nonprofit, ...). Where we have it, it is far more reliable than
    string matching and is used first. The keyword list below is the fallback for
    authorships that only carry a raw affiliation string.
    """
    if institution_type:
        return "industry" if institution_type in INDUSTRY_INSTITUTION_TYPES else "academic"
    if not affiliation:
        return "unknown"
    low = " " + affiliation.lower() + " "
    if any(m in low for m in CORPORATE_MARKERS):
        return "industry"
    for kw in ACADEMIC_KEYWORDS:
        if kw in low:
            return "academic"
    return "industry"


def is_blocked(affiliation):
    if not affiliation:
        return False
    low = affiliation.lower()
    # Bare "arm" is too common a substring to match safely, so ARM is only matched
    # in its company forms above.
    return any(b in low for b in BLOCKED_AFFILIATIONS)


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------


def build_ssl_context():
    """Default system trust store, falling back to certifi if present.

    Some Python.org macOS builds ship without a populated trust store, which makes
    every HTTPS call fail with CERTIFICATE_VERIFY_FAILED. certifi is not required;
    it is used only if it already happens to be installed.
    """
    ctx = ssl.create_default_context()
    try:
        ctx.load_verify_locations(cafile=os.environ["SSL_CERT_FILE"])
        return ctx
    except (KeyError, OSError):
        pass
    try:
        import certifi  # noqa: PLC0415

        ctx.load_verify_locations(cafile=certifi.where())
    except Exception:
        pass
    return ctx


SSL_CONTEXT = build_ssl_context()


def fetch(url, mailto):
    """GET a URL with retry and exponential backoff. Returns parsed JSON."""
    ua = "kara-pipeline/1.0"
    if mailto:
        ua += " (mailto:%s)" % mailto
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "application/json"})

    last_err = None
    min_wait = 0.0
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT, context=SSL_CONTEXT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # 4xx other than 429 will not fix themselves.
            if e.code in (429, 500, 502, 503, 504):
                last_err = e
                if e.code == 429:
                    retry_after = 0.0
                    try:
                        retry_after = float(e.headers.get("Retry-After") or 0)
                    except (TypeError, ValueError):
                        pass
                    # OpenAlex meters a daily credit budget as well as burst rate.
                    # A multi-hour Retry-After means the budget is spent, and no
                    # amount of retrying inside this run will fix it.
                    if retry_after > BUDGET_EXHAUSTED_SECONDS:
                        try:
                            detail = json.loads(e.read().decode("utf-8")).get("message", "")
                        except Exception:
                            detail = ""
                        raise RuntimeError(
                            "OpenAlex daily budget exhausted. Retry-After is %.0fs "
                            "(about %.1f hours); the budget resets at midnight UTC.\n"
                            "  %s\n"
                            "Partial results were not written. Re-run after the reset, "
                            "or add funds at https://openalex.org/pricing."
                            % (retry_after, retry_after / 3600.0, detail)) from e
                    min_wait = max(RATE_LIMIT_MIN_WAIT, retry_after)
            else:
                body = ""
                try:
                    body = e.read().decode("utf-8", "replace")[:400]
                except Exception:
                    pass
                raise RuntimeError("HTTP %s from OpenAlex: %s\n%s" % (e.code, url, body)) from e
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
            last_err = e
        wait = max(BACKOFF_BASE ** attempt, min_wait)
        print("  retry %d/%d after %s (%.0fs)" % (attempt + 1, MAX_RETRIES, last_err, wait),
              file=sys.stderr)
        time.sleep(wait)
    raise RuntimeError("gave up on %s after %d attempts: %s" % (url, MAX_RETRIES, last_err))


def build_params(query, from_year, search_mode, company_only):
    """Build the OpenAlex query parameters for one search query.

    search_mode 'title-abstract' uses the `title_and_abstract.search` filter,
    which matches only the title and the abstract. The default `search`
    parameter searches full text, which is why it returns concentrated solar
    power and corrosion coating papers on thermal queries: the phrase appears
    somewhere in the body rather than in the subject matter.
    """
    filters = ["from_publication_date:%d-01-01" % from_year, "type:article"]
    params = {}
    if search_mode == "title-abstract":
        # Filter values are comma-joined, so a query containing a comma would be
        # parsed as two filters.
        if "," in query:
            raise ValueError("query may not contain a comma in title-abstract mode: %r" % query)
        filters.append("title_and_abstract.search:%s" % query)
    else:
        params["search"] = query
    if company_only:
        filters.append("authorships.institutions.type:company")
    params["filter"] = ",".join(filters)
    return params


def iter_works(query, from_year, max_pages, mailto, search_mode, company_only, stats=None):
    """Yield works for one search query, following OpenAlex cursor pagination.

    max_pages of 0 means no cap: paginate until the cursor is exhausted.
    """
    cursor = "*"
    pages = 0
    total = None
    while cursor and (max_pages == 0 or pages < max_pages):
        params = dict(build_params(query, from_year, search_mode, company_only))
        params.update({
            "per-page": str(PER_PAGE),
            "cursor": cursor,
        })
        if mailto:
            params["mailto"] = mailto
        url = API_URL + "?" + urllib.parse.urlencode(params)
        payload = fetch(url, mailto)
        results = payload.get("results") or []
        meta = payload.get("meta") or {}
        pages += 1
        if total is None:
            total = meta.get("count")
            if stats is not None:
                stats["total_works"] = total
            print("  %s works match" % total, file=sys.stderr)
        print("  page %d: %d works" % (pages, len(results)), file=sys.stderr)
        for work in results:
            yield work
        cursor = meta.get("next_cursor")
        if not results:
            break
        time.sleep(DEFAULT_SLEEP)


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------


def work_fields(work):
    title = work.get("title") or work.get("display_name") or ""
    year = work.get("publication_year") or ""
    doi = work.get("doi") or ""
    loc = work.get("primary_location") or {}
    source = loc.get("source") or {}
    venue = source.get("display_name") or ""
    return title, year, doi, venue


def authorship_affiliation(authorship):
    """Return (affiliation, country_code, institution_type) for an authorship.

    Prefers the first resolved institution. Falls back to the raw affiliation
    string, in which case institution_type is None and classification drops to
    keyword matching.
    """
    institutions = authorship.get("institutions") or []
    for inst in institutions:
        name = (inst.get("display_name") or "").strip()
        if name:
            return name, (inst.get("country_code") or ""), (inst.get("type") or "")
    raw = authorship.get("raw_affiliation_strings") or []
    for r in raw:
        r = (r or "").strip()
        if r:
            return r, "", None
    single = (authorship.get("raw_affiliation_string") or "").strip()
    return single, "", None


def score_author(row, company_only=False):
    """Score an author row.

    Under --company-only the +40 industry term is dropped: every row in the set
    is industry, so a constant term only compresses the usable range.
    """
    score = 0
    if not company_only and row["industry_flag"] == 1:
        score += 40
    if row["author_position"] in ("first", "last"):
        score += 20
    score += min(8 * row["n_relevant_papers"], 32)
    try:
        if int(row["paper_year"]) >= 2025:
            score += 8
    except (TypeError, ValueError):
        pass
    return score


def better_record(new, old):
    """True if `new` should replace `old` as an author's representative row.

    Prefer a first/last authorship over a middle one, then prefer the more recent
    paper. Everything else is a tie and the incumbent keeps the slot.
    """
    rank = {"first": 2, "last": 2, "middle": 0}
    n_rank = rank.get(new["author_position"], 1)
    o_rank = rank.get(old["author_position"], 1)
    if n_rank != o_rank:
        return n_rank > o_rank
    try:
        return int(new["paper_year"] or 0) > int(old["paper_year"] or 0)
    except (TypeError, ValueError):
        return False


COLUMNS = [
    "author",
    "orcid",
    "affiliation",
    "affiliation_type",
    "country",
    "paper_title",
    "paper_year",
    "paper_doi",
    "paper_venue",
    "author_position",
    "topic_query",
    "n_relevant_papers",
    "industry_flag",
    "score",
]


def sort_key(row):
    """Score desc, then papers desc, then year desc, then name.

    Enrichment works this list top-down, so ordering inside a score band has to
    carry information rather than falling back to the alphabet.
    """
    try:
        year = int(row["paper_year"] or 0)
    except (TypeError, ValueError):
        year = 0
    return (-row["score"], -row["n_relevant_papers"], -year, row["author"])


def mine(queries, from_year, max_pages, mailto, search_mode, company_only):
    by_author = {}
    paper_counts = {}
    seen_author_work = set()
    dropped_blocked = 0
    # query -> set of author keys classified industry, for the yield table
    query_industry_authors = {q: set() for q in queries}
    query_works = {}

    for query in queries:
        print("[query] %s" % query, file=sys.stderr)
        stats = {}
        query_works[query] = stats
        for work in iter_works(query, from_year, max_pages, mailto,
                               search_mode, company_only, stats):
            title, year, doi, venue = work_fields(work)
            work_id = work.get("id") or doi or title
            for authorship in work.get("authorships") or []:
                author = authorship.get("author") or {}
                name = (author.get("display_name") or "").strip()
                if not name:
                    continue
                affiliation, country, inst_type = authorship_affiliation(authorship)
                if is_blocked(affiliation):
                    dropped_blocked += 1
                    continue

                key = author.get("id") or name.lower()

                # One relevant-paper credit per author per work, even if the same
                # work is returned by several queries.
                if (key, work_id) not in seen_author_work:
                    seen_author_work.add((key, work_id))
                    paper_counts[key] = paper_counts.get(key, 0) + 1

                aff_type = classify_affiliation(affiliation, inst_type)
                if aff_type == "industry":
                    query_industry_authors[query].add(key)
                row = {
                    "author": name,
                    "orcid": (author.get("orcid") or "").replace("https://orcid.org/", ""),
                    "affiliation": affiliation,
                    "affiliation_type": aff_type,
                    "country": country,
                    "paper_title": title,
                    "paper_year": year,
                    "paper_doi": doi,
                    "paper_venue": venue,
                    "author_position": authorship.get("author_position") or "",
                    "topic_query": query,
                    "n_relevant_papers": 0,
                    "industry_flag": 1 if aff_type == "industry" else 0,
                    "score": 0,
                }
                if key not in by_author or better_record(row, by_author[key]):
                    by_author[key] = row

    for key, row in by_author.items():
        row["n_relevant_papers"] = paper_counts.get(key, 1)
        row["score"] = score_author(row, company_only)

    rows = sorted(by_author.values(), key=sort_key)
    return rows, dropped_blocked, query_industry_authors, query_works


def load_queries(config):
    """Return (queries, query_class) from a config dict.

    Accepts either form of entry:
        "diamond heat spreader"
        {"query": "diamond heat spreader", "class": "core"}

    `class` labels what a query is for. `core` queries name our materials
    directly. `displacement` queries name the thermal problem we would displace
    an incumbent material from, and are where the non-obvious prospects live.
    """
    queries = []
    query_class = {}
    for entry in config.get("queries") or []:
        if isinstance(entry, str):
            q, cls = entry, ""
        elif isinstance(entry, dict):
            q, cls = (entry.get("query") or "").strip(), (entry.get("class") or "").strip()
        else:
            raise ValueError("unsupported query entry: %r" % (entry,))
        if not q:
            continue
        if q in query_class:
            print("WARNING: duplicate query dropped: %r" % q, file=sys.stderr)
            continue
        queries.append(q)
        query_class[q] = cls
    return queries, query_class


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description="Mine candidate authors from OpenAlex.")
    ap.add_argument("--config", default=os.path.join(here, "config", "queries.json"))
    ap.add_argument("--out", default=os.path.join(here, "data", "authors_raw.csv"))
    ap.add_argument("--from-year", type=int, default=2024)
    ap.add_argument("--max-pages", type=int, default=3,
                    help="max cursor pages per query (%d works per page); "
                         "0 means no cap" % PER_PAGE)
    ap.add_argument("--search-mode", choices=("full", "title-abstract"),
                    default="title-abstract",
                    help="'title-abstract' filters on title_and_abstract.search "
                         "(precise); 'full' uses the full-text search parameter "
                         "(higher recall, much more off-topic capture)")
    ap.add_argument("--company-only", action="store_true",
                    help="server-side filter to works with at least one "
                         "company-affiliated author; also drops the +40 industry "
                         "scoring term, which is constant across such a set")
    ap.add_argument("--yield-table",
                    help="write a per-query company-author yield table to this "
                         "markdown path")
    args = ap.parse_args()

    mailto = os.environ.get("OPENALEX_MAILTO", "").strip()
    if not mailto:
        print("WARNING: OPENALEX_MAILTO is unset. Falling back to the slow, "
              "rate-limited common pool. Set it to a real address before any "
              "full run.", file=sys.stderr)

    with open(args.config, "r", encoding="utf-8") as fh:
        queries, query_class = load_queries(json.load(fh))
    if not queries:
        sys.exit("no queries found in %s" % args.config)

    print("mining %d queries, from %d, %s page(s) each, search-mode=%s%s"
          % (len(queries), args.from_year,
             "unlimited" if args.max_pages == 0 else args.max_pages,
             args.search_mode,
             ", company-only" if args.company_only else ""), file=sys.stderr)

    rows, dropped_blocked, query_yield, query_works = mine(
        queries, args.from_year, args.max_pages, mailto,
        args.search_mode, args.company_only)

    out_dir = os.path.dirname(os.path.abspath(args.out))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    industry = sum(1 for r in rows if r["industry_flag"] == 1)
    academic = sum(1 for r in rows if r["affiliation_type"] == "academic")
    unknown = len(rows) - industry - academic
    print("", file=sys.stderr)
    print("wrote %d unique authors to %s" % (len(rows), args.out), file=sys.stderr)
    print("  industry: %d" % industry, file=sys.stderr)
    print("  academic: %d" % academic, file=sys.stderr)
    if unknown:
        print("  unknown affiliation: %d" % unknown, file=sys.stderr)
    print("  dropped (competitor affiliation): %d" % dropped_blocked, file=sys.stderr)

    if args.yield_table:
        write_yield_table(args.yield_table, queries, query_yield, args, len(rows),
                          industry, query_class, query_works)
        print("  wrote yield table to %s" % args.yield_table, file=sys.stderr)

    print("NOTE: affiliations come from papers and can be up to two years stale. "
          "Verify current employer before drafting.", file=sys.stderr)


def write_yield_table(path, queries, query_yield, args, n_rows, n_industry,
                      query_class=None, query_works=None):
    """Per-query company-affiliated author yield.

    `authors` counts distinct industry-classified authors a query surfaced.
    `unique` counts those no other query surfaced, which is what says whether a
    query is earning its slot in the config or just re-finding the same people.
    """
    counts = {q: query_yield.get(q, set()) for q in queries}
    unique = {}
    for q, authors in counts.items():
        others = set()
        for other_q, other_authors in counts.items():
            if other_q != q:
                others |= other_authors
        unique[q] = len(authors - others)

    ordered = sorted(queries, key=lambda q: (-len(counts[q]), q))
    out_dir = os.path.dirname(os.path.abspath(path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# Per-query yield: company-affiliated authors\n\n")
        fh.write("Run: search-mode=`%s`%s, from %d, %s pages per query.\n\n"
                 % (args.search_mode,
                    ", `--company-only`" if args.company_only else "",
                    args.from_year,
                    "unlimited" if args.max_pages == 0 else str(args.max_pages)))
        fh.write("Total unique authors in run: %d. Industry-classified: %d.\n\n"
                 % (n_rows, n_industry))
        fh.write("`authors` is distinct industry-classified authors the query surfaced. "
                 "`unique` is those no other query surfaced. A query with high "
                 "`authors` and near-zero `unique` is redundant and can be cut.\n\n")
        fh.write("| # | query | class | works | authors | unique |\n")
        fh.write("| --- | --- | --- | ---: | ---: | ---: |\n")
        for i, q in enumerate(ordered, 1):
            cls = (query_class or {}).get(q, "") or "-"
            works = (query_works or {}).get(q, {}).get("total_works")
            works_s = "-" if works is None else str(works)
            fh.write("| %d | %s | %s | %s | %d | %d |\n"
                     % (i, q, cls, works_s, len(counts[q]), unique[q]))
        fh.write("\n")

        zero = [q for q in queries if len(counts[q]) == 0]
        if zero:
            fh.write("## Zero-yield queries\n\n")
            fh.write("These produced no industry-classified authors in this run. "
                     "At a low `--max-pages` that may mean the query is genuinely "
                     "empty, or simply that page 1 held no company authors. The "
                     "`works` column tells those apart: a zero there is a real "
                     "miss, a healthy number is a sampling artifact.\n\n")
            for q in zero:
                works = (query_works or {}).get(q, {}).get("total_works")
                fh.write("- `%s` (%s, %s matching works)\n"
                         % (q, (query_class or {}).get(q, "") or "-",
                            "unknown" if works is None else works))
            fh.write("\n")

        if query_class and any(query_class.values()):
            fh.write("## By class\n\n")
            fh.write("| class | queries | authors (union) |\n")
            fh.write("| --- | ---: | ---: |\n")
            for cls in sorted({c for c in query_class.values() if c}):
                qs = [q for q in queries if query_class.get(q) == cls]
                union = set()
                for q in qs:
                    union |= counts[q]
                fh.write("| %s | %d | %d |\n" % (cls, len(qs), len(union)))
            fh.write("\n")


if __name__ == "__main__":
    main()
