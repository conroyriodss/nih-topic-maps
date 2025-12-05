#!/bin/bash
set -e

echo "=========================================="
echo "REBUILDING PI CARDS - COMPREHENSIVE"
echo "Using grant_scorecard_v2 (ALL award types)"
echo "=========================================="
echo ""

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.pi_cards_comprehensive` AS
WITH pi_base AS (
  SELECT
    -- Extract first PI from all_pis field
    TRIM(SPLIT(all_pis, '|')[SAFE_OFFSET(0)]) as contact_pi_name,
    core_project_num,
    administering_ic,
    primary_org,
    activity,
    first_fiscal_year,
    last_fiscal_year,
    total_lifetime_funding,
    publication_count,
    is_mpi,
    agency
  FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_scorecard_v2`
  WHERE all_pis IS NOT NULL
    AND all_pis != ''
),
pi_metrics AS (
  SELECT
    contact_pi_name,
    COUNT(DISTINCT core_project_num) as total_awards,
    ROUND(SUM(total_lifetime_funding)/1e6, 2) as total_funding_millions,
    COUNT(DISTINCT administering_ic) as num_ics_funded_by,
    COUNT(DISTINCT primary_org) as num_institutions_worked,
    MIN(first_fiscal_year) as career_start_year,
    MAX(last_fiscal_year) as career_last_active_year,
    MAX(last_fiscal_year) - MIN(first_fiscal_year) as career_span_years,
    SUM(publication_count) as total_publications,
    COUNTIF(is_mpi) as total_mpi_awards,
    ROUND(COUNTIF(is_mpi) * 100.0 / COUNT(*), 1) as pct_collaborative,
    STRING_AGG(DISTINCT primary_org, ' | ' ORDER BY primary_org LIMIT 5) as institutions,
    STRING_AGG(DISTINCT administering_ic, ', ' ORDER BY administering_ic) as ics_funded_by
  FROM pi_base
  GROUP BY contact_pi_name
  HAVING total_awards >= 3  -- Filter for substantive PIs
),
pi_award_types AS (
  SELECT
    contact_pi_name,
    
    -- RPG
    COUNTIF(activity IN ('R01', 'R03', 'R15', 'R21', 'R33', 'R34', 'R37', 'R56')) as rpg_awards,
    ROUND(SUM(CASE WHEN activity IN ('R01', 'R03', 'R15', 'R21', 'R33', 'R34', 'R37', 'R56') THEN total_lifetime_funding ELSE 0 END)/1e6, 2) as rpg_funding_m,
    
    -- High-Risk
    COUNTIF(activity IN ('R35', 'DP1', 'DP2', 'DP5', 'RF1')) as high_risk_awards,
    ROUND(SUM(CASE WHEN activity IN ('R35', 'DP1', 'DP2', 'DP5', 'RF1') THEN total_lifetime_funding ELSE 0 END)/1e6, 2) as high_risk_funding_m,
    
    -- Centers
    COUNTIF(activity LIKE 'P%') as center_awards,
    ROUND(SUM(CASE WHEN activity LIKE 'P%' THEN total_lifetime_funding ELSE 0 END)/1e6, 2) as center_funding_m,
    
    -- Cooperative Agreements
    COUNTIF(activity LIKE 'U%') as coop_agreement_awards,
    ROUND(SUM(CASE WHEN activity LIKE 'U%' THEN total_lifetime_funding ELSE 0 END)/1e6, 2) as coop_agreement_funding_m,
    
    -- Training
    COUNTIF(activity LIKE 'T%') as training_awards,
    
    -- Career
    COUNTIF(activity LIKE 'K%' OR activity = 'R00') as career_awards,
    COUNTIF(activity = 'K99') as k99_awards,
    
    -- Fellowship
    COUNTIF(activity LIKE 'F%') as fellowship_awards,
    
    -- SBIR
    COUNTIF(activity IN ('R41', 'R42', 'R43', 'R44')) as sbir_awards,
    
    -- Infrastructure
    COUNTIF(activity LIKE 'G%' OR activity LIKE 'S%' OR activity LIKE 'C%') as infrastructure_awards
    
  FROM pi_base
  GROUP BY contact_pi_name
)
SELECT
  m.*,
  a.* EXCEPT(contact_pi_name)
FROM pi_metrics m
LEFT JOIN pi_award_types a ON m.contact_pi_name = a.contact_pi_name
ORDER BY m.total_funding_millions DESC;

-- Show top PIs
SELECT 
  contact_pi_name,
  total_awards,
  total_funding_millions,
  career_span_years,
  num_institutions_worked,
  rpg_awards,
  center_awards,
  coop_agreement_awards,
  training_awards,
  career_awards,
  pct_collaborative,
  total_publications
FROM `od-cl-odss-conroyri-f75a.nih_analytics.pi_cards_comprehensive`
ORDER BY total_funding_millions DESC
LIMIT 20;
EOSQL

echo ""
echo "✅ PI CARDS COMPREHENSIVE CREATED"
echo ""
