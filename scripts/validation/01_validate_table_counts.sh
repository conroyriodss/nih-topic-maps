#!/bin/bash
# Validate row counts and fiscal year coverage for all NIH ExPORTER tables

PROJECT="od-cl-odss-conroyri-f75a"
DATASET="nih_exporter"

echo "=========================================="
echo "NIH ExPORTER Data Validation Report"
echo "Generated: $(date)"
echo "=========================================="
echo ""

echo "=== TABLE ROW COUNTS ==="
echo ""
bq query --use_legacy_sql=false --format=pretty \
"SELECT 
  'projects' as table_name,
  COUNT(*) as total_rows,
  MIN(CAST(FY AS INT64)) as min_year,
  MAX(CAST(FY AS INT64)) as max_year,
  COUNT(DISTINCT CAST(FY AS INT64)) as year_count,
  ROUND(SUM(TOTAL_COST)/1e9, 2) as total_funding_billions
FROM \`${PROJECT}.${DATASET}.projects\`
UNION ALL
SELECT 
  'abstracts' as table_name,
  COUNT(*) as total_rows,
  MIN(YEAR) as min_year,
  MAX(YEAR) as max_year,
  COUNT(DISTINCT YEAR) as year_count,
  NULL as total_funding_billions
FROM \`${PROJECT}.${DATASET}.abstracts\`
UNION ALL
SELECT 
  'linktables' as table_name,
  COUNT(*) as total_rows,
  NULL as min_year,
  NULL as max_year,
  NULL as year_count,
  NULL as total_funding_billions
FROM \`${PROJECT}.${DATASET}.linktables\`
UNION ALL
SELECT 
  'patents' as table_name,
  COUNT(*) as total_rows,
  NULL as min_year,
  NULL as max_year,
  NULL as year_count,
  NULL as total_funding_billions
FROM \`${PROJECT}.${DATASET}.patents\`
UNION ALL
SELECT 
  'clinicalstudies' as table_name,
  COUNT(*) as total_rows,
  NULL as min_year,
  NULL as max_year,
  NULL as year_count,
  NULL as total_funding_billions
FROM \`${PROJECT}.${DATASET}.clinicalstudies\`
ORDER BY table_name;"

echo ""
echo "=== PROJECTS BY FISCAL YEAR ==="
echo ""
bq query --use_legacy_sql=false --format=pretty \
"SELECT 
  CAST(FY AS INT64) as fiscal_year,
  COUNT(*) as project_count,
  COUNT(DISTINCT CORE_PROJECT_NUM) as unique_cores,
  COUNT(DISTINCT ADMINISTERING_IC) as ic_count,
  ROUND(SUM(TOTAL_COST)/1e9, 2) as funding_billions
FROM \`${PROJECT}.${DATASET}.projects\`
GROUP BY fiscal_year
ORDER BY fiscal_year;"

echo ""
echo "=== ABSTRACTS BY YEAR ==="
echo ""
bq query --use_legacy_sql=false --format=pretty \
"SELECT 
  YEAR as fiscal_year,
  COUNT(*) as abstract_count,
  COUNT(DISTINCT APPLICATION_ID) as unique_applications
FROM \`${PROJECT}.${DATASET}.abstracts\`
GROUP BY YEAR
ORDER BY YEAR;"

echo ""
echo "=== MISSING YEARS CHECK ==="
echo ""
bq query --use_legacy_sql=false --format=pretty \
"WITH expected_years AS (
  SELECT year FROM UNNEST(GENERATE_ARRAY(1990, 2024)) as year
),
actual_years AS (
  SELECT DISTINCT CAST(FY AS INT64) as year FROM \`${PROJECT}.${DATASET}.projects\`
)
SELECT e.year as missing_year
FROM expected_years e
LEFT JOIN actual_years a ON e.year = a.year
WHERE a.year IS NULL
ORDER BY e.year;"

echo ""
echo "=== IC DISTRIBUTION ==="
echo ""
bq query --use_legacy_sql=false --format=pretty \
"SELECT 
  ADMINISTERING_IC as ic_code,
  COUNT(*) as project_count,
  ROUND(SUM(TOTAL_COST)/1e9, 2) as funding_billions,
  MIN(CAST(FY AS INT64)) as first_year,
  MAX(CAST(FY AS INT64)) as last_year
FROM \`${PROJECT}.${DATASET}.projects\`
WHERE ADMINISTERING_IC IS NOT NULL
GROUP BY ADMINISTERING_IC
ORDER BY project_count DESC
LIMIT 30;"

echo ""
echo "Validation complete!"
