#!/bin/bash
set -e

echo "=========================================="
echo "CREATING FULL IC CARDS"
echo "With temporal trends & award breakdowns"
echo "=========================================="
echo ""

# Step 1: Create temporal trends table
echo "[1/3] Creating IC temporal trends..."

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.ic_temporal_trends` AS
WITH award_classifications AS (
  SELECT
    *,
    -- Classify award types
    CASE
      WHEN ACTIVITY IN ('R01', 'R03', 'R15', 'R21', 'R34', 'R35', 'R37', 'R56', 'RF1', 'RM1', 'DP1', 'DP2', 'DP5') 
        THEN 'Research Project Grants (RPG)'
      WHEN ACTIVITY LIKE 'P%' 
        THEN 'Program Projects & Centers'
      WHEN ACTIVITY IN ('F30', 'F31', 'F32', 'F33', 'K01', 'K02', 'K07', 'K08', 'K22', 'K23', 'K24', 'K25', 'K99', 'R00')
        THEN 'Fellowships & Career Awards'
      WHEN ACTIVITY IN ('T32', 'T34', 'T35', 'T36', 'T37', 'T90', 'TL1', 'TU2')
        THEN 'Training Grants'
      WHEN ACTIVITY IN ('R41', 'R42', 'R43', 'R44', 'U43', 'U44')
        THEN 'SBIR/STTR'
      ELSE 'Other'
    END as award_category,
    
    -- ESI/NI flags (approximate based on activity codes)
    CASE 
      WHEN ACTIVITY IN ('R21', 'R03', 'K99', 'R00', 'DP2') THEN TRUE
      ELSE FALSE
    END as likely_early_investigator
  FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`
  WHERE cluster_id IS NOT NULL
)
SELECT
  ADMINISTERING_IC,
  fiscal_year,
  
  -- Overall metrics
  COUNT(DISTINCT CORE_PROJECT_NUM) as num_awards,
  ROUND(SUM(FY_TOTAL_COST)/1e6, 2) as funding_millions,
  
  -- Scientific output
  SUM(publication_count) as num_publications,
  
  -- People metrics
  COUNT(DISTINCT contact_pi_name) as num_unique_pis,
  COUNT(DISTINCT PRIMARY_ORG) as num_institutions,
  COUNTIF(likely_early_investigator) as num_likely_esi_ni,
  
  -- Award type breakdown
  COUNTIF(award_category = 'Research Project Grants (RPG)') as rpg_awards,
  ROUND(SUM(CASE WHEN award_category = 'Research Project Grants (RPG)' THEN FY_TOTAL_COST ELSE 0 END)/1e6, 2) as rpg_funding_m,
  
  COUNTIF(award_category = 'Program Projects & Centers') as center_awards,
  ROUND(SUM(CASE WHEN award_category = 'Program Projects & Centers' THEN FY_TOTAL_COST ELSE 0 END)/1e6, 2) as center_funding_m,
  
  COUNTIF(award_category = 'Fellowships & Career Awards') as fellowship_awards,
  ROUND(SUM(CASE WHEN award_category = 'Fellowships & Career Awards' THEN FY_TOTAL_COST ELSE 0 END)/1e6, 2) as fellowship_funding_m,
  
  COUNTIF(award_category = 'Training Grants') as training_awards,
  ROUND(SUM(CASE WHEN award_category = 'Training Grants' THEN FY_TOTAL_COST ELSE 0 END)/1e6, 2) as training_funding_m,
  
  COUNTIF(award_category = 'SBIR/STTR') as sbir_awards,
  ROUND(SUM(CASE WHEN award_category = 'SBIR/STTR' THEN FY_TOTAL_COST ELSE 0 END)/1e6, 2) as sbir_funding_m,
  
  -- Top topics this year
  APPROX_TOP_COUNT(cluster_label, 5) as top_topics,
  
  -- Collaboration
  COUNTIF(is_mpi) as mpi_awards,
  ROUND(AVG(pi_count), 2) as avg_pis_per_award

FROM award_classifications
WHERE fiscal_year BETWEEN 1985 AND 2024
GROUP BY ADMINISTERING_IC, fiscal_year
ORDER BY ADMINISTERING_IC, fiscal_year;
EOSQL

echo "✓ Created ic_temporal_trends"

# Step 2: Create comprehensive IC cards
echo ""
echo "[2/3] Creating comprehensive IC cards..."

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.ic_cards_complete` AS
WITH base_metrics AS (
  SELECT
    ADMINISTERING_IC,
    organizational_category,
    
    -- Overall metrics
    COUNT(DISTINCT CORE_PROJECT_NUM) as total_awards,
    ROUND(SUM(TOTAL_LIFETIME_FUNDING)/1e9, 2) as total_funding_billions,
    
    -- Coverage
    COUNT(DISTINCT domain_id) as num_domains,
    COUNT(DISTINCT cluster_id) as num_topics,
    
    -- People
    COUNT(DISTINCT contact_pi_name) as total_unique_pis,
    COUNT(DISTINCT PRIMARY_ORG) as total_institutions,
    
    -- Scientific output
    SUM(publication_count) as total_publications,
    ROUND(AVG(publication_count), 1) as avg_pubs_per_award,
    
    -- Collaboration
    COUNTIF(is_mpi) as total_mpi_awards,
    ROUND(COUNTIF(is_mpi) * 100.0 / COUNT(*), 1) as pct_mpi,
    ROUND(AVG(pi_count), 2) as avg_pis_per_award,
    
    -- Timespan
    MIN(FIRST_FISCAL_YEAR) as earliest_year,
    MAX(LAST_FISCAL_YEAR) as latest_year,
    
    -- Top research areas
    APPROX_TOP_COUNT(domain_name, 5) as top_domains,
    APPROX_TOP_COUNT(cluster_label, 10) as top_clusters
    
  FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`
  WHERE cluster_id IS NOT NULL
  GROUP BY ADMINISTERING_IC, organizational_category
),
award_type_totals AS (
  SELECT
    ADMINISTERING_IC,
    COUNTIF(ACTIVITY IN ('R01', 'R03', 'R15', 'R21', 'R34', 'R35', 'R37', 'R56', 'RF1', 'RM1', 'DP1', 'DP2', 'DP5')) as rpg_total_awards,
    ROUND(SUM(CASE WHEN ACTIVITY IN ('R01', 'R03', 'R15', 'R21', 'R34', 'R35', 'R37', 'R56', 'RF1', 'RM1', 'DP1', 'DP2', 'DP5') THEN TOTAL_LIFETIME_FUNDING ELSE 0 END)/1e9, 2) as rpg_total_funding_b,
    
    COUNTIF(ACTIVITY LIKE 'P%') as center_total_awards,
    ROUND(SUM(CASE WHEN ACTIVITY LIKE 'P%' THEN TOTAL_LIFETIME_FUNDING ELSE 0 END)/1e9, 2) as center_total_funding_b,
    
    COUNTIF(ACTIVITY IN ('F30', 'F31', 'F32', 'F33', 'K01', 'K02', 'K07', 'K08', 'K22', 'K23', 'K24', 'K25', 'K99', 'R00')) as fellowship_total_awards,
    ROUND(SUM(CASE WHEN ACTIVITY IN ('F30', 'F31', 'F32', 'F33', 'K01', 'K02', 'K07', 'K08', 'K22', 'K23', 'K24', 'K25', 'K99', 'R00') THEN TOTAL_LIFETIME_FUNDING ELSE 0 END)/1e9, 2) as fellowship_total_funding_b,
    
    COUNTIF(ACTIVITY IN ('T32', 'T34', 'T35', 'T36', 'T37', 'T90', 'TL1', 'TU2')) as training_total_awards,
    ROUND(SUM(CASE WHEN ACTIVITY IN ('T32', 'T34', 'T35', 'T36', 'T37', 'T90', 'TL1', 'TU2') THEN TOTAL_LIFETIME_FUNDING ELSE 0 END)/1e9, 2) as training_total_funding_b,
    
    COUNTIF(ACTIVITY IN ('R41', 'R42', 'R43', 'R44', 'U43', 'U44')) as sbir_total_awards,
    ROUND(SUM(CASE WHEN ACTIVITY IN ('R41', 'R42', 'R43', 'R44', 'U43', 'U44') THEN TOTAL_LIFETIME_FUNDING ELSE 0 END)/1e9, 2) as sbir_total_funding_b
    
  FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`
  WHERE cluster_id IS NOT NULL
  GROUP BY ADMINISTERING_IC
)
SELECT
  b.*,
  a.rpg_total_awards,
  a.rpg_total_funding_b,
  a.center_total_awards,
  a.center_total_funding_b,
  a.fellowship_total_awards,
  a.fellowship_total_funding_b,
  a.training_total_awards,
  a.training_total_funding_b,
  a.sbir_total_awards,
  a.sbir_total_funding_b
FROM base_metrics b
LEFT JOIN award_type_totals a ON b.ADMINISTERING_IC = a.ADMINISTERING_IC
ORDER BY b.total_funding_billions DESC;
EOSQL

echo "✓ Created ic_cards_complete"

# Step 3: Summary
echo ""
echo "[3/3] Generating summary..."

bq query --use_legacy_sql=false << 'EOSQL'
SELECT 
  ADMINISTERING_IC,
  total_funding_billions,
  total_awards,
  total_unique_pis,
  total_institutions,
  CONCAT(earliest_year, '-', latest_year) as active_period,
  rpg_total_awards,
  center_total_awards,
  fellowship_total_awards,
  training_total_awards,
  sbir_total_awards
FROM `od-cl-odss-conroyri-f75a.nih_analytics.ic_cards_complete`
ORDER BY total_funding_billions DESC
LIMIT 10;
EOSQL

echo ""
echo "=========================================="
echo "✅ FULL IC CARDS CREATED"
echo "=========================================="
echo ""
echo "Tables created:"
echo "  - ic_temporal_trends (IC × Year data)"
echo "  - ic_cards_complete (IC summary with award types)"
echo ""
echo "Query examples:"
echo "  bq query 'SELECT * FROM \`od-cl-odss-conroyri-f75a.nih_analytics.ic_cards_complete\` WHERE ADMINISTERING_IC = \"CA\"'"
echo "  bq query 'SELECT * FROM \`od-cl-odss-conroyri-f75a.nih_analytics.ic_temporal_trends\` WHERE ADMINISTERING_IC = \"CA\" AND fiscal_year >= 2020'"
echo ""
