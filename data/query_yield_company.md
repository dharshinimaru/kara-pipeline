# Per-query yield: company-affiliated authors

Run: search-mode=`title-abstract`, `--company-only`, from 2024, 1 pages per query.

Total unique authors in run: 1136. Industry-classified: 375.

`authors` is distinct industry-classified authors the query surfaced. `unique` is those no other query surfaced. A query with high `authors` and near-zero `unique` is redundant and can be cut.

| # | query | class | works | authors | unique |
| --- | --- | --- | ---: | ---: | ---: |
| 1 | chiplet package thermal | displacement | 34 | 79 | 72 |
| 2 | diamond thermal conductivity substrate | core | 20 | 46 | 17 |
| 3 | die attach thermal resistance | displacement | 11 | 42 | 35 |
| 4 | wide bandgap power device packaging | displacement | 13 | 39 | 39 |
| 5 | diamond heat spreader | core | 16 | 38 | 17 |
| 6 | thermal boundary resistance GaN | displacement | 15 | 32 | 7 |
| 7 | co-packaged optics thermal | displacement | 11 | 30 | 23 |
| 8 | copper diamond composite | core | 17 | 30 | 20 |
| 9 | GaN HEMT thermal management | displacement | 11 | 27 | 6 |
| 10 | laser diode thermal management | displacement | 9 | 25 | 25 |
| 11 | GaN diamond thermal | core | 18 | 22 | 8 |
| 12 | IGBT module thermal fatigue | displacement | 7 | 19 | 18 |
| 13 | power module baseplate thermal | displacement | 6 | 16 | 16 |
| 14 | near-junction thermal management | displacement | 8 | 13 | 5 |
| 15 | single crystal diamond MPCVD | core | 6 | 9 | 5 |

## By class

| class | queries | authors (union) |
| --- | ---: | ---: |
| core | 5 | 106 |
| displacement | 10 | 293 |

