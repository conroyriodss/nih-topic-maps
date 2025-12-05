# NIH Analytics Data Inventory
**Updated: December 4, 2025**

## Summary
- **Total Projects:** 513,419
- **Total Funding:** $861.3B (2000-2024)
- **Complete Portfolio:** Extramural + Intramural + Contracts

## Production Tables

### Entity Cards (Comprehensive)
| Table | Records | Description |
|-------|---------|-------------|
| `ic_cards_comprehensive` | 114 ICs | All award types including N/Z-series |
| `pi_cards_comprehensive` | 49,619 PIs | Cleaned names, 3+ awards minimum |
| `institution_cards_comprehensive` | 2,230 institutions | Excludes NIH ICOs |
| `temporal_trends_comprehensive` | 25 years | Annual trends 2000-2024 |

### Award Type Coverage
✅ **RPG** (R01, R03, R15, R21, R33, R34, R37, R56)
✅ **High-Risk/High-Reward** (R35, DP1, DP2, DP5, RF1)
✅ **Centers** (P01, P30, P50, P-series)
✅ **Cooperative Agreements** (U01, U19, U54, UL1-CTSA)
✅ **Training** (T32, T35, T-series)
✅ **Career Development** (K-series, R00)
✅ **Fellowships** (F-series)
✅ **SBIR/STTR** (R41-R44, U43-U44)
✅ **Infrastructure** (G12-RCMI, S06-MBRS, C06)
✅ **Contracts** (N01, N03, N-series)
✅ **Intramural** (Z01, ZIA, Z-series)

### Specialized Identifiers
- **CTSA Institutions:** 260 (UL1 awards)
- **T32 Training Programs:** 5,328
- **RCMI Institutions:** 57 (G12 awards)
- **P30 Core Grants:** Tracked by institution

## Source Tables
- `grant_scorecard_v2` - Comprehensive portfolio (513k projects, 358 activity codes)
- `grant_cards_v2_0_complete` - Clustered research awards (282k projects, 27 activity codes)
- `phase2_cluster_assignments` - ML clustering results (253k assignments, 35% complete)

## Data Quality
- PI names cleaned (removed "(contact)" suffix)
- NIH ICO institutions excluded
- All award types retained (N/Z-series included)
- 25-year temporal coverage (2000-2024)
