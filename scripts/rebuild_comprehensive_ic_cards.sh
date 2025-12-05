#!/bin/bash
set -e

echo "=========================================="
echo "REBUILDING IC CARDS - COMPLETE PORTFOLIO"
echo "Using grant_scorecard_v2 (ALL 358 activity codes)"
echo "=========================================="
echo ""

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.ic_cards_comprehensive` AS
WITH base_metrics AS (
  SELECT
    administering_ic,
    agency,
    COUNT(DISTINCT CORE_PROJECT_NUM) as total_awards,
    COUNT(DISTINCT pi_name_normalized) as total_unique_pis,
    COUNT(DISTINCT org_name) as total_institutions,
    MIN(fy_start) as earliest_year,
    MAX(fy_end) as latest_year
  FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_scorecard_v2`
  WHERE administering_ic IS NOT NULL
  GROUP BY administering_ic, agency
),
award_types AS (
  SELECT
    administering_ic,
    
    -- RPG (Standard investigator-initiated)
    COUNTIF(activity IN ('R01', 'R03', 'R15', 'R21', 'R33', 'R34', 'R37', 'R56')) as rpg_standard,
    
    -- High-Risk/High-Reward
    COUNTIF(activity IN ('R35', 'DP1', 'DP2', 'DP5', 'RF1')) as high_risk,
    
    -- Program Projects & Centers (P-series)
    COUNTIF(activity LIKE 'P%') as centers_p_series,
    COUNTIF(activity = 'P01') as p01_program_projects,
    COUNTIF(activity = 'P30') as p30_center_core,
    COUNTIF(activity = 'P50') as p50_specialized_centers,
    
    -- Cooperative Agreements (U-series)
    COUNTIF(activity LIKE 'U%') as coop_agreements_u_series,
    COUNTIF(activity = 'U01') as u01_research_coop,
    COUNTIF(activity = 'UL1') as ul1_ctsa,
    COUNTIF(activity = 'U54') as u54_specialized_centers,
    
    -- Training Grants (T-series)
    COUNTIF(activity LIKE 'T%') as training_t_series,
    COUNTIF(activity = 'T32') as t32_institutional_training,
    
    -- Career Development (K-series)
    COUNTIF(activity LIKE 'K%' OR activity = 'R00') as career_development,
    COUNTIF(activity = 'K99') as k99_pathway_independence,
    
    -- Fellowships (F-series)
    COUNTIF(activity LIKE 'F%') as fellowships,
    COUNTIF(activity = 'F31') as f31_predoctoral,
    COUNTIF(activity = 'F32') as f32_postdoctoral,
    
    -- SBIR/STTR
    COUNTIF(activity IN ('R41', 'R42', 'R43', 'R44', 'U43', 'U44')) as sbir_sttr,
    
    -- Infrastructure
    COUNTIF(activity LIKE 'C%' OR activity LIKE 'G%' OR activity LIKE 'S%') as infrastructure,
    COUNTIF(activity = 'G12') as g12_rcmi_minority,
    COUNTIF(activity = 'S06') as s06_mbrs_minority
    
  FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_scorecard_v2`
  WHERE administering_ic IS NOT NULL
  GROUP BY administering_ic
)
SELECT
  b.*,
  a.* EXCEPT(administering_ic)
FROM base_metrics b
LEFT JOIN award_types a ON b.administering_ic = a.administering_ic
ORDER BY b.total_awards DESC;

-- Show results
SELECT 
  administering_ic,
  agency,
  total_awards,
  total_unique_pis,
  rpg_standard,
  centers_p_series,
  coop_agreements_u_series,
  training_t_series,
  career_development,
  fellowships,
  ul1_ctsa,
  t32_institutional_training
FROM `od-cl-odss-conroyri-f75a.nih_analytics.ic_cards_comprehensive`
ORDER BY total_awards DESC
LIMIT 15;
EOSQL

echo ""
echo "=========================================="
echo "✅ COMPREHENSIVE IC CARDS CREATED"
echo "=========================================="
echo ""
echo "Table: ic_cards_comprehensive"
echo "Includes ALL award types (R/P/U/T/K/F/SBIR/Infrastructure)"
echo ""
