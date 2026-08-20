# Per-query yield: company-affiliated authors

Run: search-mode=`title-abstract`, from 2024, 1 pages per query.

Total unique authors in run: 4842. Industry-classified: 417.

`authors` is distinct industry-classified authors the query surfaced. `unique` is those no other query surfaced. A query with high `authors` and near-zero `unique` is redundant and can be cut.

| # | query | class | works | authors | unique |
| --- | --- | --- | ---: | ---: | ---: |
| 1 | chiplet package thermal | displacement | 103 | 105 | 98 |
| 2 | diamond thermal conductivity substrate | core | 163 | 59 | 30 |
| 3 | wide bandgap power device packaging | displacement | 91 | 50 | 50 |
| 4 | die attach thermal resistance | displacement | 38 | 46 | 39 |
| 5 | diamond heat spreader | core | 68 | 41 | 20 |
| 6 | copper diamond composite | core | 130 | 34 | 23 |
| 7 | thermal boundary resistance GaN | displacement | 79 | 34 | 6 |
| 8 | GaN HEMT thermal management | displacement | 84 | 32 | 11 |
| 9 | co-packaged optics thermal | displacement | 34 | 31 | 24 |
| 10 | GaN diamond thermal | core | 147 | 28 | 10 |
| 11 | IGBT module thermal fatigue | displacement | 32 | 23 | 22 |
| 12 | power module baseplate thermal | displacement | 24 | 16 | 16 |
| 13 | near-junction thermal management | displacement | 61 | 14 | 6 |
| 14 | single crystal diamond MPCVD | core | 39 | 9 | 5 |
| 15 | laser diode submount thermal | displacement | 0 | 0 | 0 |

## Zero-yield queries

These produced no industry-classified authors in this run. At a low `--max-pages` that may mean the query is genuinely empty, or simply that page 1 held no company authors. The `works` column tells those apart: a zero there is a real miss, a healthy number is a sampling artifact.

- `laser diode submount thermal` (displacement, 0 matching works)

## By class

| class | queries | authors (union) |
| --- | ---: | ---: |
| core | 5 | 131 |
| displacement | 10 | 322 |

