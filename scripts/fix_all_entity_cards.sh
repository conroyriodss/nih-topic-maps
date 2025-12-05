#!/bin/bash
set -e

echo "=========================================="
echo "FIXING ALL ENTITY CARDS"
echo "Removing (contact), NIH ICOs, Intramural (Z-series)"
echo "=========================================="
echo ""

echo "[1/4] Fixing IC Cards - Remove intramural ICs..."
bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.ic_cards_comprehensive` AS
SELECT *
FROM `od-cl-odss-conroyri-f75a.nih_analytics.ic_cards_comprehensive`
WHERE administering_ic NOT IN (
  'AI', 'CA', 'HL', 'GM', 'HD', 'DK', 'NS', 'AG', 'MH', 'DA', 'ES', 'EY', 'EB', 'RR'
) OR administering_ic IS NULL
ORDER BY total_funding_billions DESC;
EOSQL

echo ""
echo "[2/4] Fixing PI Cards - Remove (contact) and clean names..."
bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.pi_cards_comprehensive` AS
WITH cleaned_base AS (
  SELECT
    -- Remove "(contact)" and other suffixes from PI names
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
    AND activity NOT LIKE 'Z%'  -- Exclude intramural
    AND activity NOT LIKE 'N%'  -- Exclude contracts
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
    AND contact_pi_name_clean NOT LIKE '%,%  %'  -- Remove malformed names
  GROUP BY contact_pi_name
  HAVING total_awards >= 3
),
pi_award_types AS (
  SELECT
    contact_pi_name_clean as contact_pi_name,
    COUNTIF(activity IN ('R01', 'R03', 'R15', 'R21', 'R33', 'R34', 'R37', 'R56')) as rpg_awards,
    ROUND(SUM(CASE WHEN activity IN ('R01', 'R03', 'R15', 'R21', 'R33', 'R34', 'R37', 'R56') THEN total_lifetime_funding ELSE 0 END)/1e6, 2) as rpg_funding_m,
    COUNTIF(activity IN ('R35', 'DP1', 'DP2', 'DP5', 'RF1')) as high_risk_awards,
    ROUND(SUM(CASE WHEN activity IN ('R35', 'DP1', 'DP2', 'DP5', 'RF1') THEN total_lifetime_funding ELSE 0 END)/1e6, 2) as high_risk_funding_m,
    COUNTIF(activity LIKE 'P%') as center_awards,
    ROUND(SUM(CASE WHEN activity LIKE 'P%' THEN total_lifetime_funding ELSE 0 END)/1e6, 2) as center_funding_m,
    COUNTIF(activity LIKE 'U%') as coop_agreement_awards,
    ROUND(SUM(CASE WHEN activity LIKE 'U%' THEN total_lifetime_funding ELSE 0 END)/1e6, 2) as coop_agreement_funding_m,
    COUNTIF(activity LIKE 'T%') as training_awards,
    COUNTIF(activity LIKE 'K%' OR activity = 'R00') as career_awards,
    COUNTIF(activity = 'K99') as k99_awards,
    COUNTIF(activity LIKE 'F%') as fellowship_awards,
    COUNTIF(activity IN ('R41', 'R42', 'R43', 'R44')) as sbir_awards,
    COUNTIF(activity LIKE 'G%' OR activity LIKE 'S%' OR activity LIKE 'C%') as infrastructure_awards
  FROM cleaned_base
  WHERE contact_pi_name_clean IS NOT NULL
    AND contact_pi_name_clean != ''
  GROUP BY contact_pi_name
)
SELECT
  m.*,
  a.* EXCEPT(contact_pi_name)
FROM pi_metrics m
LEFT JOIN pi_award_types a ON m.contact_pi_name = a.contact_pi_name
ORDER BY m.total_funding_millions DESC;
EOSQL

echo ""
echo "[3/4] Fixing Institution Cards - Remove NIH ICOs and intramural..."
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
    AND activity NOT LIKE 'Z%'  -- Exclude intramural
    AND activity NOT LIKE 'N%'  -- Exclude contracts
    -- Exclude NIH ICO names
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
EOSQL

echo ""
echo "[4/4] Show cleaned results..."
bq query --use_legacy_sql=false << 'EOSQL'
SELECT 'PI Cards' as card_type, COUNT(*) as num_records
FROM `od-cl-odss-conroyri-f75a.nih_analytics.pi_cards_comprehensive`
UNION ALL
SELECT 'Institution Cards', COUNT(*)
FROM `od-cl-odss-conroyri-f75a.nih_analytics.institution_cards_comprehensive`;
EOSQL

echo ""
echo "=========================================="
echo "✅ ALL CARDS CLEANED!"
echo "=========================================="
echo ""
echo "Exclusions applied:"
echo "  ✓ PI names: Removed '(contact)' suffix"
echo "  ✓ PI names: Removed 'TBD, TBD' and malformed entries"
echo "  ✓ Institutions: Removed NIH ICO names"
echo "  ✓ All cards: Excluded Z-series (intramural)"
echo "  ✓ All cards: Excluded N-series (contracts)"
echo ""
