#!/bin/bash
set -e

echo "=========================================="
echo "REBUILDING INSTITUTION CARDS - COMPREHENSIVE"
echo "Using grant_scorecard_v2 (ALL award types)"
echo "=========================================="
echo ""

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.institution_cards_comprehensive` AS
WITH institution_base AS (
  SELECT
    primary_org as institution,
    primary_state as state,
    core_project_num,
    administering_ic,
    activity,
    first_fiscal_year,
    last_fiscal_year,
    total_lifetime_funding,
    publication_count,
    is_mpi,
    agency
  FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_scorecard_v2`
  WHERE primary_org IS NOT NULL
),
institution_metrics AS (
  SELECT
    institution,
    state,
    COUNT(DISTINCT core_project_num) as total_awards,
    ROUND(SUM(total_lifetime_funding)/1e9, 2) as total_funding_billions,
    COUNT(DISTINCT administering_ic) as num_ics,
    MIN(first_fiscal_year) as earliest_year,
    MAX(last_fiscal_year) as latest_year,
    SUM(publication_count) as total_publications,
    COUNTIF(is_mpi) as total_mpi_awards,
    ROUND(COUNTIF(is_mpi) * 100.0 / COUNT(*), 1) as pct_collaborative
  FROM institution_base
  GROUP BY institution, state
  HAVING total_awards >= 10
),
institution_award_types AS (
  SELECT
    institution,
    
    -- RPG
    COUNTIF(activity IN ('R01', 'R03', 'R15', 'R21', 'R33', 'R34', 'R37', 'R56')) as rpg_total,
    ROUND(SUM(CASE WHEN activity IN ('R01', 'R03', 'R15', 'R21', 'R33', 'R34', 'R37', 'R56') THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as rpg_funding_b,
    
    -- High-Risk
    COUNTIF(activity IN ('R35', 'DP1', 'DP2', 'DP5', 'RF1')) as high_risk_total,
    
    -- Centers
    COUNTIF(activity LIKE 'P%') as center_total,
    ROUND(SUM(CASE WHEN activity LIKE 'P%' THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as center_funding_b,
    COUNTIF(activity = 'P30') as p30_core_grants,
    COUNTIF(activity = 'P50') as p50_specialized_centers,
    
    -- Cooperative Agreements
    COUNTIF(activity LIKE 'U%') as coop_agreement_total,
    ROUND(SUM(CASE WHEN activity LIKE 'U%' THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as coop_agreement_funding_b,
    COUNTIF(activity = 'UL1') as ul1_ctsa_awards,
    COUNTIF(activity = 'U54') as u54_awards,
    
    -- Training
    COUNTIF(activity LIKE 'T%') as training_total,
    COUNTIF(activity = 'T32') as t32_awards,
    
    -- Career
    COUNTIF(activity LIKE 'K%' OR activity = 'R00') as career_total,
    
    -- Fellowship
    COUNTIF(activity LIKE 'F%') as fellowship_total,
    
    -- SBIR
    COUNTIF(activity IN ('R41', 'R42', 'R43', 'R44')) as sbir_total,
    
    -- Infrastructure (minority-serving institutions)
    COUNTIF(activity LIKE 'G%' OR activity LIKE 'S%' OR activity LIKE 'C%') as infrastructure_total,
    COUNTIF(activity = 'G12') as g12_rcmi_awards,
    COUNTIF(activity = 'S06') as s06_mbrs_awards,
    COUNTIF(activity = 'C06') as c06_construction_awards
    
  FROM institution_base
  GROUP BY institution
)
SELECT
  m.*,
  a.* EXCEPT(institution)
FROM institution_metrics m
LEFT JOIN institution_award_types a ON m.institution = a.institution
ORDER BY m.total_funding_billions DESC;

-- Show top institutions
SELECT 
  institution,
  state,
  total_awards,
  total_funding_billions,
  rpg_total,
  center_total,
  coop_agreement_total,
  training_total,
  ul1_ctsa_awards,
  t32_awards,
  p30_core_grants,
  g12_rcmi_awards,
  ROUND(rpg_funding_b * 100.0 / NULLIF(total_funding_billions, 0), 1) as pct_rpg,
  ROUND(center_funding_b * 100.0 / NULLIF(total_funding_billions, 0), 1) as pct_centers
FROM `od-cl-odss-conroyri-f75a.nih_analytics.institution_cards_comprehensive`
ORDER BY total_funding_billions DESC
LIMIT 20;
EOSQL

echo ""
echo "✅ INSTITUTION CARDS COMPREHENSIVE CREATED"
echo ""
