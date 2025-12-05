#!/bin/bash
set -e

echo "=========================================="
echo "REBUILDING IC CARDS - COMPLETE PORTFOLIO"
echo "Using grant_scorecard_v2 (correct schema)"
echo "=========================================="
echo ""

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.ic_cards_comprehensive` AS
WITH base_metrics AS (
  SELECT
    administering_ic,
    ic_name,
    agency,
    COUNT(DISTINCT core_project_num) as total_projects,
    SUM(total_lifetime_funding) as total_funding,
    ROUND(SUM(total_lifetime_funding)/1e9, 2) as total_funding_billions,
    COUNT(DISTINCT primary_org) as total_institutions,
    COUNTIF(is_mpi) as total_mpi_awards,
    ROUND(COUNTIF(is_mpi) * 100.0 / COUNT(*), 1) as pct_mpi,
    SUM(publication_count) as total_publications,
    ROUND(AVG(publication_count), 1) as avg_pubs_per_award,
    MIN(first_fiscal_year) as earliest_year,
    MAX(last_fiscal_year) as latest_year
  FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_scorecard_v2`
  WHERE administering_ic IS NOT NULL
  GROUP BY administering_ic, ic_name, agency
),
award_types AS (
  SELECT
    administering_ic,
    
    -- RPG (Standard investigator-initiated)
    COUNTIF(activity IN ('R01', 'R03', 'R15', 'R21', 'R33', 'R34', 'R37', 'R56')) as rpg_standard_count,
    ROUND(SUM(CASE WHEN activity IN ('R01', 'R03', 'R15', 'R21', 'R33', 'R34', 'R37', 'R56') THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as rpg_standard_funding_b,
    
    -- High-Risk/High-Reward
    COUNTIF(activity IN ('R35', 'DP1', 'DP2', 'DP5', 'RF1', 'RM1')) as high_risk_count,
    ROUND(SUM(CASE WHEN activity IN ('R35', 'DP1', 'DP2', 'DP5', 'RF1', 'RM1') THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as high_risk_funding_b,
    
    -- Program Projects & Centers (P-series)
    COUNTIF(activity LIKE 'P%') as centers_p_count,
    ROUND(SUM(CASE WHEN activity LIKE 'P%' THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as centers_p_funding_b,
    COUNTIF(activity = 'P01') as p01_program_projects,
    COUNTIF(activity = 'P30') as p30_center_core,
    COUNTIF(activity = 'P50') as p50_specialized_centers,
    
    -- Cooperative Agreements (U-series)
    COUNTIF(activity LIKE 'U%') as coop_agreements_u_count,
    ROUND(SUM(CASE WHEN activity LIKE 'U%' THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as coop_agreements_u_funding_b,
    COUNTIF(activity = 'U01') as u01_research_coop,
    COUNTIF(activity = 'UL1') as ul1_ctsa,
    COUNTIF(activity = 'U54') as u54_specialized_centers,
    COUNTIF(activity = 'U19') as u19_research_programs,
    
    -- Training Grants (T-series)
    COUNTIF(activity LIKE 'T%') as training_t_count,
    ROUND(SUM(CASE WHEN activity LIKE 'T%' THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as training_t_funding_b,
    COUNTIF(activity = 'T32') as t32_institutional_training,
    COUNTIF(activity = 'T35') as t35_short_term_training,
    
    -- Career Development (K-series + R00)
    COUNTIF(activity LIKE 'K%' OR activity = 'R00') as career_dev_count,
    ROUND(SUM(CASE WHEN activity LIKE 'K%' OR activity = 'R00' THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as career_dev_funding_b,
    COUNTIF(activity = 'K99') as k99_pathway_independence,
    COUNTIF(activity = 'K01') as k01_mentored_scientist,
    COUNTIF(activity = 'K08') as k08_clinical_scientist,
    COUNTIF(activity = 'K23') as k23_patient_oriented,
    
    -- Fellowships (F-series)
    COUNTIF(activity LIKE 'F%') as fellowship_count,
    ROUND(SUM(CASE WHEN activity LIKE 'F%' THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as fellowship_funding_b,
    COUNTIF(activity = 'F31') as f31_predoctoral,
    COUNTIF(activity = 'F32') as f32_postdoctoral,
    COUNTIF(activity = 'F30') as f30_md_phd,
    
    -- SBIR/STTR
    COUNTIF(activity IN ('R41', 'R42', 'R43', 'R44', 'U43', 'U44')) as sbir_sttr_count,
    ROUND(SUM(CASE WHEN activity IN ('R41', 'R42', 'R43', 'R44', 'U43', 'U44') THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as sbir_sttr_funding_b,
    
    -- Infrastructure
    COUNTIF(activity LIKE 'C%' OR activity LIKE 'G%' OR activity LIKE 'S%') as infrastructure_count,
    ROUND(SUM(CASE WHEN activity LIKE 'C%' OR activity LIKE 'G%' OR activity LIKE 'S%' THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as infrastructure_funding_b,
    COUNTIF(activity = 'G12') as g12_rcmi_minority,
    COUNTIF(activity = 'S06') as s06_mbrs_minority,
    COUNTIF(activity = 'C06') as c06_construction
    
  FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_scorecard_v2`
  WHERE administering_ic IS NOT NULL
  GROUP BY administering_ic
)
SELECT
  b.*,
  a.* EXCEPT(administering_ic)
FROM base_metrics b
LEFT JOIN award_types a ON b.administering_ic = a.administering_ic
ORDER BY b.total_funding_billions DESC;

-- Show comprehensive results
SELECT 
  administering_ic,
  ic_name,
  total_projects,
  total_funding_billions,
  rpg_standard_count,
  centers_p_count,
  coop_agreements_u_count,
  training_t_count,
  career_dev_count,
  fellowship_count,
  ROUND(rpg_standard_funding_b * 100.0 / NULLIF(total_funding_billions, 0), 1) as pct_rpg,
  ROUND(centers_p_funding_b * 100.0 / NULLIF(total_funding_billions, 0), 1) as pct_centers,
  ROUND(coop_agreements_u_funding_b * 100.0 / NULLIF(total_funding_billions, 0), 1) as pct_coop_agreements,
  ul1_ctsa,
  t32_institutional_training
FROM `od-cl-odss-conroyri-f75a.nih_analytics.ic_cards_comprehensive`
ORDER BY total_funding_billions DESC
LIMIT 15;
EOSQL

echo ""
echo "=========================================="
echo "✅ COMPREHENSIVE IC CARDS CREATED"
echo "=========================================="
echo ""
echo "Table: ic_cards_comprehensive"
echo "Includes ALL award types with funding breakdowns"
echo ""
