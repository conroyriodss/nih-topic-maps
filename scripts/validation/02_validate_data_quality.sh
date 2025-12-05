#!/bin/bash
# Check for data quality issues: nulls, duplicates, anomalies

PROJECT="od-cl-odss-conroyri-f75a"
DATASET="nih_exporter"

echo "=========================================="
echo "NIH ExPORTER Data Quality Checks"
echo "Generated: $(date)"
echo "=========================================="
echo ""

echo "=== NULL VALUE ANALYSIS (PROJECTS) ==="
echo ""
bq query --use_legacy_sql=false --format=pretty \
"SELECT 
  COUNTIF(CORE_PROJECT_NUM IS NULL) as null_core_project,
  COUNTIF(FY IS NULL) as null_fy,
  COUNTIF(ADMINISTERING_IC IS NULL) as null_ic,
  COUNTIF(PROJECT_TITLE IS NULL) as null_title,
  COUNTIF(TOTAL_COST IS NULL) as null_cost,
  COUNTIF(PI_NAMEs IS NULL) as null_pi,
  COUNT(*) as total_rows,
  ROUND(COUNTIF(CORE_PROJECT_NUM IS NULL) * 100.0 / COUNT(*), 2) as pct_null_core
FROM \`${PROJECT}.${DATASET}.projects\`;"

echo ""
echo "=== DUPLICATE CHECK (PROJECTS) ==="
echo ""
bq query --use_legacy_sql=false --format=pretty \
"SELECT 
  COUNT(*) as total_records,
  COUNT(DISTINCT FULL_PROJECT_NUM) as unique_full_project_nums,
  COUNT(*) - COUNT(DISTINCT FULL_PROJECT_NUM) as duplicate_count
FROM \`${PROJECT}.${DATASET}.projects\`;"

echo ""
echo "=== FUNDING ANOMALIES ==="
echo ""
bq query --use_legacy_sql=false --format=pretty \
"SELECT 
  CAST(FY AS INT64) as fiscal_year,
  COUNT(*) as projects_with_cost,
  MIN(TOTAL_COST) as min_cost,
  APPROX_QUANTILES(TOTAL_COST, 100)[OFFSET(50)] as median_cost,
  MAX(TOTAL_COST) as max_cost,
  AVG(TOTAL_COST) as avg_cost
FROM \`${PROJECT}.${DATASET}.projects\`
WHERE TOTAL_COST IS NOT NULL AND TOTAL_COST > 0
GROUP BY fiscal_year
ORDER BY fiscal_year DESC
LIMIT 10;"

echo ""
echo "=== ABSTRACTS-PROJECTS JOIN COVERAGE ==="
echo ""
bq query --use_legacy_sql=false --format=pretty \
"WITH project_apps AS (
  SELECT DISTINCT APPLICATION_ID 
  FROM \`${PROJECT}.${DATASET}.projects\`
  WHERE APPLICATION_ID IS NOT NULL
),
abstract_apps AS (
  SELECT DISTINCT APPLICATION_ID 
  FROM \`${PROJECT}.${DATASET}.abstracts\`
  WHERE APPLICATION_ID IS NOT NULL
)
SELECT
  (SELECT COUNT(*) FROM project_apps) as total_project_apps,
  (SELECT COUNT(*) FROM abstract_apps) as total_abstract_apps,
  (SELECT COUNT(*) FROM project_apps p INNER JOIN abstract_apps a ON p.APPLICATION_ID = a.APPLICATION_ID) as matched_apps,
  ROUND((SELECT COUNT(*) FROM project_apps p INNER JOIN abstract_apps a ON p.APPLICATION_ID = a.APPLICATION_ID) * 100.0 / 
        (SELECT COUNT(*) FROM project_apps), 2) as match_percentage;"

echo ""
echo "=== CLINICAL STUDIES LINKAGE ==="
echo ""
bq query --use_legacy_sql=false --format=pretty \
"SELECT 
  COUNT(*) as total_clinical_studies,
  COUNT(DISTINCT Core_Project_Number) as unique_projects_linked,
  COUNT(DISTINCT ClinicalTrials_gov_ID) as unique_trial_ids
FROM \`${PROJECT}.${DATASET}.clinicalstudies\`;"

echo ""
echo "Data quality checks complete!"
