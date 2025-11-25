# NIH ExPORTER Data Quality Notes

**Last Updated:** 2025-11-25
**Data Currency:** Through FY2024

## Validation Against NIH Reporter

| Check | BigQuery | NIH Reporter | Status |
|-------|----------|--------------|--------|
| Johns Hopkins grants | 45,020 | 44,998 | OK |
| R01 FY2023 | 30,429 | 30,442 | OK |
| NCI FY2023 (combined) | 9,902 | 12,055 | See notes |
| Francis Collins | 91 awards | 102 | OK (FY lag) |

## Multi-IC Funding

FUNDING_ICs format: IC_CODE:AMOUNT backslash IC_CODE:AMOUNT
Use REGEXP_CONTAINS for multi-IC detection

## PI Name Cleaning

- pi_scorecard: Original with (contact) suffix
- pi_scorecard_clean: Normalized, (contact) removed
