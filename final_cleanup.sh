#!/bin/bash

PROJECT_ID="od-cl-odss-conroyri-f75a"
SOURCE_DATASET="nih_analytics"
TARGET_DATASET="nih_processed"
EXPORT_BUCKET="gs://od-cl-odss-conroyri-nih-processed"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=== Final Cleanup & Export ==="

# ============================================
# STEP 1: Export Entity Cards to GCS
# ============================================

echo ""
echo "1. Exporting entity cards to GCS..."

# Export grant cards
bq extract --destination_format=PARQUET \
  ${PROJECT_ID}:${SOURCE_DATASET}.grant_cards_deduped \
  ${EXPORT_BUCKET}/entity_cards/grant_cards_2000_2024_${TIMESTAMP}.parquet

# Export PI cards
bq extract --destination_format=PARQUET \
  ${PROJECT_ID}:${TARGET_DATASET}.pi_cards_phase2 \
  ${EXPORT_BUCKET}/entity_cards/pi_cards_2000_2024_${TIMESTAMP}.parquet

# Export Institution cards
bq extract --destination_format=PARQUET \
  ${PROJECT_ID}:${TARGET_DATASET}.institution_cards_phase2 \
  ${EXPORT_BUCKET}/entity_cards/institution_cards_2000_2024_${TIMESTAMP}.parquet

# Export IC cards
bq extract --destination_format=PARQUET \
  ${PROJECT_ID}:${TARGET_DATASET}.ic_cards_phase2 \
  ${EXPORT_BUCKET}/entity_cards/ic_cards_2000_2024_${TIMESTAMP}.parquet

echo "✓ Entity cards exported"

# ============================================
# STEP 2: Export Supporting Tables
# ============================================

echo ""
echo "2. Exporting supporting tables..."

# Export transitions
bq extract --destination_format=PARQUET \
  ${PROJECT_ID}:${SOURCE_DATASET}.award_transitions_complete \
  ${EXPORT_BUCKET}/supporting_tables/award_transitions_${TIMESTAMP}.parquet

# Export clinical studies
bq extract --destination_format=PARQUET \
  ${PROJECT_ID}:${SOURCE_DATASET}.award_clinical_studies \
  ${EXPORT_BUCKET}/supporting_tables/award_clinical_studies_${TIMESTAMP}.parquet

# Export patents
bq extract --destination_format=PARQUET \
  ${PROJECT_ID}:${SOURCE_DATASET}.award_patents \
  ${EXPORT_BUCKET}/supporting_tables/award_patents_${TIMESTAMP}.parquet

echo "✓ Supporting tables exported"

# ============================================
# STEP 3: Create Documentation
# ============================================

echo ""
echo "3. Creating documentation..."

cat > /tmp/ENTITY_CARDS_README.md << 'EOF'
# NIH Entity Cards - Complete 2000-2024 Dataset

## Overview
Complete entity card system covering 25 years of NIH awards (2000-2024) with enhanced metadata.

## Statistics
- **Grant Cards**: 516,386 awards across 21 activity code prefixes
- **PI Cards**: 174,440 unique principal investigators
- **Institution Cards**: 19,279 organizations
- **IC Cards**: 91 institutes/centers

## Coverage
- **Years**: 2000-2024 (25 years)
- **Activity Codes**: R, F, K, U, P, T, Z, N, I, H, S, D, Y, G, C, O, B, X, V, M (21 prefixes, 288 unique codes)
- **Geographic**: All 50 US states + international
- **Funding**: $852 billion total

## Features

### Grant Cards
- Complete award lifecycle (start/end dates, funding)
- PI information (cleaned, no "(contact)" suffix)
- Organization details
- Clinical trials (25,845 awards linked)
- Patents (31,512 awards linked)
- FOA numbers (35 years of data)
- Research context (16 fields)
- Award transitions (7 official pathways)

### PI Cards
- Career span and progression
- Award portfolio by type (R, K, F, U, P, T, Z, N, I)
- Multi-PI participation
- Institution history
- IC distribution
- Clinical trials and patents
- Transition pathways

### Institution Cards
- Complete award portfolio
- PI count
- Activity code distribution
- Geographic location
- Funding totals

### IC Cards
- Portfolio by activity code
- PI and institution counts
- Funding distribution
- Clinical trials and patents

## Data Quality

### Known Issues Documented
1. **RILEY, WILLIAM T.**: 7,773 awards from Personal Improvement Computer Systems contract (2000-2005) - legitimate
2. **Zero-funded awards**: VA (I01), SAMHSA (H79, U79), resource access (X02) - expected
3. **Intramural research** (Z01, ZIA): Internal NIH budget, not extramural funding

### Cleaning Applied
- Removed "(contact)" suffix from 379,986 PI names
- Fixed 100x inflation in older funding data
- Removed duplicate records
- Validated all activity codes

## Transition Pathways (55,099 total)
1. R43→R44: 51,351 (SBIR Phase I→II)
2. R21→R33: 1,876 (Exploratory→Full)
3. K99→R00: 1,079 (Career transition)
4. R41→R42: 486 (SBIR alternative)
5. R61→R33: 286 (Phased innovation)
6. UH2→UH3: 21 (Cooperative agreement)
7. R43→U44: 7 (SBIR Phase II Enhanced)

## File Locations
- Grant Cards: `entity_cards/grant_cards_2000_2024_*.parquet`
- PI Cards: `entity_cards/pi_cards_2000_2024_*.parquet`
- Institution Cards: `entity_cards/institution_cards_2000_2024_*.parquet`
- IC Cards: `entity_cards/ic_cards_2000_2024_*.parquet`

## Supporting Tables
- Transitions: `supporting_tables/award_transitions_*.parquet`
- Clinical Studies: `supporting_tables/award_clinical_studies_*.parquet`
- Patents: `supporting_tables/award_patents_*.parquet`

## Schema

### Grant Cards (72 fields)
Key fields:
- `CORE_PROJECT_NUM`: Unique award identifier
- `ACTIVITY`: Activity code (R01, K99, etc.)
- `contact_pi_name`: Cleaned PI name
- `FIRST_FISCAL_YEAR`, `LAST_FISCAL_YEAR`: Award span
- `TOTAL_LIFETIME_FUNDING`: Total funding across all years
- `clinical_trial_count`, `patent_count`: Linked outputs
- `transition_type`: Transition pathway if applicable

### PI Cards (23 fields)
Key fields:
- `pi_name`: Cleaned PI name
- `total_awards`: Award count
- `r_awards`, `k_awards`, `f_awards`, `u_awards`, `p_awards`, etc.: Awards by type
- `career_span_years`: First to last award
- `total_lifetime_funding`: Total funding received

### Institution Cards (20 fields)
Key fields:
- `institution_name`: Organization name
- `org_state`: State location
- `total_awards`: Award count
- Activity breakdowns (r_awards, k_awards, etc.)
- `total_pis`: Unique PI count

### IC Cards (18 fields)
Key fields:
- `ic_code`: Institute/center code
- `ic_name`: Full name
- Activity breakdowns
- `total_pis`, `total_institutions`: Portfolio reach

## Generation Date
December 5, 2025

## Contact
NIH ODSS Analytics Team
EOF

gsutil cp /tmp/ENTITY_CARDS_README.md ${EXPORT_BUCKET}/ENTITY_CARDS_README.md

echo "✓ Documentation created"

# ============================================
# STEP 4: Delete Temporary Tables
# ============================================

echo ""
echo "4. Cleaning up temporary tables..."

# List of temporary tables to delete
TEMP_TABLES=(
  "grant_cards_complete_rebuild"
  "grant_cards_complete_2000_2024"
  "grant_cards_cleaned_2000_2024"
  "grant_cards_final"
  "grant_cards_all_activities"
  "grant_cards_complete_all_activities"
  "grant_cards_final_with_transitions"
  "pi_cards_complete_rebuild"
  "institution_cards_complete_rebuild"
  "ic_cards_complete_rebuild"
  "projects_complete_2000_2024"
  "data_quality_investigation"
)

for table in "${TEMP_TABLES[@]}"; do
  echo "  Deleting ${table}..."
  bq rm -f ${PROJECT_ID}:${SOURCE_DATASET}.${table} 2>/dev/null || true
  bq rm -f ${PROJECT_ID}:${TARGET_DATASET}.${table} 2>/dev/null || true
done

echo "✓ Temporary tables deleted"

# ============================================
# STEP 5: Summary Report
# ============================================

echo ""
echo "=== FINAL SUMMARY ==="

bq query --project_id=${PROJECT_ID} --use_legacy_sql=false --format=pretty \
"
SELECT
  table_name,
  ROUND(size_bytes / 1024 / 1024 / 1024, 2) as size_gb,
  row_count
FROM \`${PROJECT_ID}.${SOURCE_DATASET}.__TABLES__\`
WHERE table_name IN ('grant_cards_deduped', 'award_transitions_complete', 
                     'award_clinical_studies', 'award_patents')
UNION ALL
SELECT
  table_name,
  ROUND(size_bytes / 1024 / 1024 / 1024, 2),
  row_count
FROM \`${PROJECT_ID}.${TARGET_DATASET}.__TABLES__\`
WHERE table_name IN ('pi_cards_phase2', 'institution_cards_phase2', 'ic_cards_phase2')
ORDER BY size_gb DESC
"

echo ""
echo "Exported files in GCS:"
gsutil ls -lh ${EXPORT_BUCKET}/entity_cards/
gsutil ls -lh ${EXPORT_BUCKET}/supporting_tables/

echo ""
echo "=== 🎉 CLEANUP COMPLETE ==="
echo ""
echo "Production Tables:"
echo "  ✅ grant_cards_deduped (516K awards)"
echo "  ✅ pi_cards_phase2 (174K PIs)"
echo "  ✅ institution_cards_phase2 (19K institutions)"
echo "  ✅ ic_cards_phase2 (91 ICs)"
echo ""
echo "Backups & Exports:"
echo "  ✅ ${EXPORT_BUCKET}/entity_cards/"
echo "  ✅ ${EXPORT_BUCKET}/supporting_tables/"
echo "  ✅ ${EXPORT_BUCKET}/ENTITY_CARDS_README.md"
echo ""
echo "Documentation updated!"
