#!/bin/bash
set -e

echo "=========================================="
echo "REBUILDING TEMPORAL TRENDS - COMPREHENSIVE"
echo "Using grant_scorecard_v2 (ALL award types)"
echo "=========================================="
echo ""

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.temporal_trends_comprehensive` AS
WITH fiscal_year_expanded AS (
  SELECT
    core_project_num,
    administering_ic,
    activity,
    primary_org,
    fy,
    total_lifetime_funding / distinct_fiscal_years as annual_funding,
    publication_count,
    is_mpi
  FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_scorecard_v2`,
  UNNEST(GENERATE_ARRAY(first_fiscal_year, last_fiscal_year)) as fy
  WHERE fiscal_years_funded LIKE CONCAT('%', CAST(fy AS STRING), '%')
)
SELECT
  fy as fiscal_year,
  COUNT(DISTINCT core_project_num) as total_awards,
  ROUND(SUM(annual_funding)/1e9, 2) as total_funding_billions,
  
  -- By award type
  COUNTIF(activity IN ('R01', 'R03', 'R15', 'R21', 'R33', 'R34', 'R37', 'R56')) as rpg_awards,
  COUNTIF(activity LIKE 'P%') as center_awards,
  COUNTIF(activity LIKE 'U%') as coop_agreement_awards,
  COUNTIF(activity LIKE 'T%') as training_awards,
  COUNTIF(activity LIKE 'K%' OR activity = 'R00') as career_awards,
  COUNTIF(activity LIKE 'F%') as fellowship_awards,
  
  -- Funding by type
  ROUND(SUM(CASE WHEN activity IN ('R01', 'R03', 'R15', 'R21', 'R33', 'R34', 'R37', 'R56') THEN annual_funding ELSE 0 END)/1e9, 2) as rpg_funding_b,
  ROUND(SUM(CASE WHEN activity LIKE 'P%' THEN annual_funding ELSE 0 END)/1e9, 2) as center_funding_b,
  ROUND(SUM(CASE WHEN activity LIKE 'U%' THEN annual_funding ELSE 0 END)/1e9, 2) as coop_agreement_funding_b,
  ROUND(SUM(CASE WHEN activity LIKE 'T%' THEN annual_funding ELSE 0 END)/1e9, 2) as training_funding_b
  
FROM fiscal_year_expanded
GROUP BY fy
HAVING fy >= 2000 AND fy <= 2024
ORDER BY fy;

-- Show recent trends
SELECT *
FROM `od-cl-odss-conroyri-f75a.nih_analytics.temporal_trends_comprehensive`
WHERE fiscal_year >= 2015
ORDER BY fiscal_year;
EOSQL

echo ""
echo "✅ TEMPORAL TRENDS COMPREHENSIVE CREATED"
echo ""
