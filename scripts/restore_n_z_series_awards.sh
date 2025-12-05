#!/bin/bash
set -e

echo "=========================================="
echo "RESTORING N-SERIES & Z-SERIES AWARDS"
echo "Including Contracts and Intramural Research"
echo "=========================================="
echo ""

echo "[1/4] Rebuilding IC Cards with N/Z-series..."
bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.ic_cards_comprehensive` AS
WITH base_metrics AS (
  SELECT
    administering_ic,
    ic_name,
    agency,
    COUNT(DISTINCT core_project_num) as total_projects,
    ROUND(SUM(total_lifetime_funding)/1e9, 2) as total_funding_billions,
    COUNT(DISTINCT primary_org) as total_institutions,
    COUNTIF(is_mpi) as total_mpi_awards,
    ROUND(COUNTIF(is_mpi) * 100.0 / COUNT(*), 1) as pct_mpi,
    SUM(publication_count) as total_publications,
    MIN(first_fiscal_year) as earliest_year,
    MAX(last_fiscal_year) as latest_year
  FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_scorecard_v2`
  WHERE administering_ic IS NOT NULL
  GROUP BY administering_ic, ic_name, agency
),
award_types AS (
  SELECT
    administering_ic,
    
    -- RPG Standard
    COUNTIF(activity IN ('R01', 'R03', 'R15', 'R21', 'R33', 'R34', 'R37', 'R56')) as rpg_count,
    ROUND(SUM(CASE WHEN activity IN ('R01', 'R03', 'R15', 'R21', 'R33', 'R34', 'R37', 'R56') THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as rpg_funding_b,
    
    -- High-Risk/High-Reward
    COUNTIF(activity IN ('R35', 'DP1', 'DP2', 'DP5', 'RF1', 'RM1')) as high_risk_count,
    ROUND(SUM(CASE WHEN activity IN ('R35', 'DP1', 'DP2', 'DP5', 'RF1', 'RM1') THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as high_risk_funding_b,
    
    -- Centers (P-series)
    COUNTIF(activity LIKE 'P%') as centers_count,
    ROUND(SUM(CASE WHEN activity LIKE 'P%' THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as centers_funding_b,
    COUNTIF(activity = 'P01') as p01_count,
    COUNTIF(activity = 'P30') as p30_count,
    COUNTIF(activity = 'P50') as p50_count,
    
    -- Cooperative Agreements (U-series)
    COUNTIF(activity LIKE 'U%') as coop_agreements_count,
    ROUND(SUM(CASE WHEN activity LIKE 'U%' THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as coop_agreements_funding_b,
    COUNTIF(activity = 'U01') as u01_count,
    COUNTIF(activity = 'UL1') as ul1_ctsa_count,
    COUNTIF(activity = 'U54') as u54_count,
    
    -- Training (T-series)
    COUNTIF(activity LIKE 'T%') as training_count,
    ROUND(SUM(CASE WHEN activity LIKE 'T%' THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as training_funding_b,
    COUNTIF(activity = 'T32') as t32_count,
    
    -- Career Development
    COUNTIF(activity LIKE 'K%' OR activity = 'R00') as career_count,
    ROUND(SUM(CASE WHEN activity LIKE 'K%' OR activity = 'R00' THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as career_funding_b,
    
    -- Fellowships
    COUNTIF(activity LIKE 'F%') as fellowship_count,
    ROUND(SUM(CASE WHEN activity LIKE 'F%' THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as fellowship_funding_b,
    
    -- SBIR/STTR
    COUNTIF(activity IN ('R41', 'R42', 'R43', 'R44', 'U43', 'U44')) as sbir_count,
    ROUND(SUM(CASE WHEN activity IN ('R41', 'R42', 'R43', 'R44', 'U43', 'U44') THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as sbir_funding_b,
    
    -- Infrastructure
    COUNTIF(activity LIKE 'C%' OR activity LIKE 'G%' OR activity LIKE 'S%') as infrastructure_count,
    ROUND(SUM(CASE WHEN activity LIKE 'C%' OR activity LIKE 'G%' OR activity LIKE 'S%' THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as infrastructure_funding_b,
    COUNTIF(activity = 'G12') as g12_rcmi_count,
    COUNTIF(activity = 'S06') as s06_mbrs_count,
    
    -- Contracts (N-series) - RESTORED
    COUNTIF(activity LIKE 'N%') as contract_count,
    ROUND(SUM(CASE WHEN activity LIKE 'N%' THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as contract_funding_b,
    COUNTIF(activity = 'N01') as n01_research_contracts,
    
    -- Intramural (Z-series) - RESTORED
    COUNTIF(activity LIKE 'Z%') as intramural_count,
    ROUND(SUM(CASE WHEN activity LIKE 'Z%' THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as intramural_funding_b,
    COUNTIF(activity = 'Z01') as z01_intramural_research,
    COUNTIF(activity LIKE 'ZIA') as zia_intramural_research
    
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
EOSQL

echo "✓ IC cards updated with N/Z-series"

echo ""
echo "[2/4] Rebuilding PI Cards with N/Z-series..."
bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.pi_cards_comprehensive` AS
WITH cleaned_base AS (
  SELECT
    TRIM(REGEXP_REPLACE(
      REGEXP_REPLACE(all_pis, r'\(contact\)', ''),
      r'\s+', ' '
    )) as all_pis_cleaned,
    TRIM(SPLIT(
      REGEXP_REPLACE(
        REGEXP_REPLACE(all_pis, r'\(contact\)', ''),
        r'\s+', ' '
      ), '|')[SAFE_OFFSET(0)]
    ) as contact_pi_name_clean,
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
    contact_pi_name_clean as contact_pi_name,
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
  FROM cleaned_base
  WHERE contact_pi_name_clean IS NOT NULL
    AND contact_pi_name_clean != ''
    AND contact_pi_name_clean != 'TBD, TBD'
  GROUP BY contact_pi_name
  HAVING total_awards >= 3
),
pi_award_types AS (
  SELECT
    contact_pi_name_clean as contact_pi_name,
    COUNTIF(activity IN ('R01', 'R03', 'R15', 'R21', 'R33', 'R34', 'R37', 'R56')) as rpg_awards,
    ROUND(SUM(CASE WHEN activity IN ('R01', 'R03', 'R15', 'R21', 'R33', 'R34', 'R37', 'R56') THEN total_lifetime_funding ELSE 0 END)/1e6, 2) as rpg_funding_m,
    COUNTIF(activity IN ('R35', 'DP1', 'DP2', 'DP5', 'RF1')) as high_risk_awards,
    COUNTIF(activity LIKE 'P%') as center_awards,
    COUNTIF(activity LIKE 'U%') as coop_agreement_awards,
    COUNTIF(activity LIKE 'T%') as training_awards,
    COUNTIF(activity LIKE 'K%' OR activity = 'R00') as career_awards,
    COUNTIF(activity LIKE 'F%') as fellowship_awards,
    COUNTIF(activity IN ('R41', 'R42', 'R43', 'R44')) as sbir_awards,
    COUNTIF(activity LIKE 'G%' OR activity LIKE 'S%' OR activity LIKE 'C%') as infrastructure_awards,
    COUNTIF(activity LIKE 'N%') as contract_awards,
    COUNTIF(activity LIKE 'Z%') as intramural_awards
  FROM cleaned_base
  WHERE contact_pi_name_clean IS NOT NULL
  GROUP BY contact_pi_name
)
SELECT
  m.*,
  a.* EXCEPT(contact_pi_name)
FROM pi_metrics m
LEFT JOIN pi_award_types a ON m.contact_pi_name = a.contact_pi_name
ORDER BY m.total_funding_millions DESC;
EOSQL

echo "✓ PI cards updated with N/Z-series"

echo ""
echo "[3/4] Rebuilding Institution Cards with N/Z-series..."
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
    AND primary_org NOT LIKE '%NATIONAL INSTITUTE%'
    AND primary_org NOT LIKE '%NATIONAL CENTER FOR%'
    AND primary_org NOT LIKE '%DIVISION OF%NCI%'
    AND primary_org NOT LIKE '%DIVISION OF%NIH%'
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
    COUNTIF(activity IN ('R01', 'R03', 'R15', 'R21', 'R33', 'R34', 'R37', 'R56')) as rpg_total,
    ROUND(SUM(CASE WHEN activity IN ('R01', 'R03', 'R15', 'R21', 'R33', 'R34', 'R37', 'R56') THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as rpg_funding_b,
    COUNTIF(activity IN ('R35', 'DP1', 'DP2', 'DP5', 'RF1')) as high_risk_total,
    COUNTIF(activity LIKE 'P%') as center_total,
    ROUND(SUM(CASE WHEN activity LIKE 'P%' THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as center_funding_b,
    COUNTIF(activity = 'P30') as p30_core_grants,
    COUNTIF(activity = 'P50') as p50_specialized_centers,
    COUNTIF(activity LIKE 'U%') as coop_agreement_total,
    ROUND(SUM(CASE WHEN activity LIKE 'U%' THEN total_lifetime_funding ELSE 0 END)/1e9, 2) as coop_agreement_funding_b,
    COUNTIF(activity = 'UL1') as ul1_ctsa_awards,
    COUNTIF(activity = 'U54') as u54_awards,
    COUNTIF(activity LIKE 'T%') as training_total,
    COUNTIF(activity = 'T32') as t32_awards,
    COUNTIF(activity LIKE 'K%' OR activity = 'R00') as career_total,
    COUNTIF(activity LIKE 'F%') as fellowship_total,
    COUNTIF(activity IN ('R41', 'R42', 'R43', 'R44')) as sbir_total,
    COUNTIF(activity LIKE 'G%' OR activity LIKE 'S%' OR activity LIKE 'C%') as infrastructure_total,
    COUNTIF(activity = 'G12') as g12_rcmi_awards,
    COUNTIF(activity = 'S06') as s06_mbrs_awards,
    COUNTIF(activity = 'C06') as c06_construction_awards,
    COUNTIF(activity LIKE 'N%') as contract_total,
    COUNTIF(activity LIKE 'Z%') as intramural_total
  FROM institution_base
  GROUP BY institution
)
SELECT
  m.*,
  a.* EXCEPT(institution)
FROM institution_metrics m
LEFT JOIN institution_award_types a ON m.institution = a.institution
ORDER BY m.total_funding_billions DESC;
EOSQL

echo "✓ Institution cards updated with N/Z-series"

echo ""
echo "[4/4] Validation check..."
bq query --use_legacy_sql=false << 'EOSQL'
SELECT
  'IC Cards' as card_type,
  COUNT(*) as num_entities,
  SUM(contract_count) as total_contracts,
  SUM(intramural_count) as total_intramural
FROM `od-cl-odss-conroyri-f75a.nih_analytics.ic_cards_comprehensive`
UNION ALL
SELECT
  'PI Cards',
  COUNT(*),
  SUM(contract_awards),
  SUM(intramural_awards)
FROM `od-cl-odss-conroyri-f75a.nih_analytics.pi_cards_comprehensive`
UNION ALL
SELECT
  'Institution Cards',
  COUNT(*),
  SUM(contract_total),
  SUM(intramural_total)
FROM `od-cl-odss-conroyri-f75a.nih_analytics.institution_cards_comprehensive`;
EOSQL

echo ""
echo "=========================================="
echo "✅ N-SERIES & Z-SERIES RESTORED!"
echo "=========================================="
echo ""
echo "Award types now included:"
echo "  ✓ Contracts (N01, N03, N43, N44, etc.)"
echo "  ✓ Intramural (Z01, ZIA, ZIC, etc.)"
echo ""
