#!/bin/bash
set -e

echo "=========================================="
echo "CREATING FULL INSTITUTION CARDS (FIXED)"
echo "With temporal trends & specialization"
echo "=========================================="
echo ""

# Step 1: Institutional Temporal Trends
echo "[1/4] Creating institutional temporal trends..."

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.institution_temporal_trends` AS
WITH year_expanded AS (
  SELECT
    PRIMARY_ORG as institution,
    year_num as fiscal_year,
    CORE_PROJECT_NUM,
    contact_pi_name,
    cluster_label,
    ACTIVITY,
    TOTAL_LIFETIME_FUNDING / GREATEST(1, LAST_FISCAL_YEAR - FIRST_FISCAL_YEAR + 1) as annual_funding
  FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`,
  UNNEST(GENERATE_ARRAY(FIRST_FISCAL_YEAR, LAST_FISCAL_YEAR)) as year_num
  WHERE cluster_id IS NOT NULL
    AND PRIMARY_ORG IS NOT NULL
    AND year_num BETWEEN 1985 AND 2024
),
award_classifications AS (
  SELECT
    institution,
    fiscal_year,
    CORE_PROJECT_NUM,
    annual_funding,
    contact_pi_name,
    cluster_label,
    
    -- Award type classification
    CASE
      WHEN ACTIVITY IN ('R01', 'R03', 'R15', 'R21', 'R34', 'R35', 'R37', 'R56', 'RF1', 'RM1', 'DP1', 'DP2', 'DP5') 
        THEN 'RPG'
      WHEN ACTIVITY LIKE 'P%' 
        THEN 'Centers'
      WHEN ACTIVITY IN ('F30', 'F31', 'F32', 'F33', 'K01', 'K02', 'K07', 'K08', 'K22', 'K23', 'K24', 'K25', 'K99', 'R00')
        THEN 'Fellowship/Career'
      WHEN ACTIVITY IN ('T32', 'T34', 'T35', 'T36', 'T37', 'T90', 'TL1', 'TU2')
        THEN 'Training'
      WHEN ACTIVITY IN ('R41', 'R42', 'R43', 'R44', 'U43', 'U44')
        THEN 'SBIR/STTR'
      WHEN ACTIVITY = 'R15'
        THEN 'AREA'
      ELSE 'Other'
    END as award_category,
    
    -- Specialized award flags
    CASE WHEN ACTIVITY = 'R15' THEN TRUE ELSE FALSE END as is_area_award,
    CASE WHEN ACTIVITY IN ('G12', 'U54', 'S06') THEN TRUE ELSE FALSE END as is_minority_serving,
    CASE WHEN ACTIVITY = 'UL1' THEN TRUE ELSE FALSE END as is_ctsa
    
  FROM year_expanded
)
SELECT
  institution,
  fiscal_year,
  
  -- Overall metrics
  COUNT(DISTINCT CORE_PROJECT_NUM) as num_awards,
  ROUND(SUM(annual_funding)/1e6, 2) as funding_millions,
  COUNT(DISTINCT contact_pi_name) as num_active_pis,
  
  -- Award type breakdown
  COUNTIF(award_category = 'RPG') as rpg_awards,
  ROUND(SUM(CASE WHEN award_category = 'RPG' THEN annual_funding ELSE 0 END)/1e6, 2) as rpg_funding_m,
  
  COUNTIF(award_category = 'Centers') as center_awards,
  ROUND(SUM(CASE WHEN award_category = 'Centers' THEN annual_funding ELSE 0 END)/1e6, 2) as center_funding_m,
  
  COUNTIF(award_category = 'Fellowship/Career') as fellowship_awards,
  ROUND(SUM(CASE WHEN award_category = 'Fellowship/Career' THEN annual_funding ELSE 0 END)/1e6, 2) as fellowship_funding_m,
  
  COUNTIF(award_category = 'Training') as training_awards,
  ROUND(SUM(CASE WHEN award_category = 'Training' THEN annual_funding ELSE 0 END)/1e6, 2) as training_funding_m,
  
  COUNTIF(award_category = 'SBIR/STTR') as sbir_awards,
  ROUND(SUM(CASE WHEN award_category = 'SBIR/STTR' THEN annual_funding ELSE 0 END)/1e6, 2) as sbir_funding_m,
  
  -- Specialized awards
  COUNTIF(is_area_award) as area_awards,
  ROUND(SUM(CASE WHEN is_area_award THEN annual_funding ELSE 0 END)/1e6, 2) as area_funding_m,
  
  COUNTIF(is_minority_serving) as minority_serving_awards,
  ROUND(SUM(CASE WHEN is_minority_serving THEN annual_funding ELSE 0 END)/1e6, 2) as minority_serving_funding_m,
  
  COUNTIF(is_ctsa) as ctsa_awards,
  ROUND(SUM(CASE WHEN is_ctsa THEN annual_funding ELSE 0 END)/1e6, 2) as ctsa_funding_m,
  
  -- Top topics this year
  APPROX_TOP_COUNT(cluster_label, 5) as top_topics_this_year

FROM award_classifications
GROUP BY institution, fiscal_year
ORDER BY institution, fiscal_year;
EOSQL

echo "✓ Created institution_temporal_trends"

# Step 2: Institutional Specialization Profile
echo ""
echo "[2/4] Analyzing institutional specialization..."

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.institution_specialization` AS
WITH total_portfolio AS (
  SELECT
    PRIMARY_ORG as institution,
    COUNT(*) as total_awards,
    SUM(TOTAL_LIFETIME_FUNDING) as total_funding
  FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`
  WHERE cluster_id IS NOT NULL
    AND PRIMARY_ORG IS NOT NULL
  GROUP BY institution
),
specialized_awards AS (
  SELECT
    PRIMARY_ORG as institution,
    
    -- AREA (undergraduate institutions)
    COUNTIF(ACTIVITY = 'R15') as area_total_awards,
    ROUND(SUM(CASE WHEN ACTIVITY = 'R15' THEN TOTAL_LIFETIME_FUNDING ELSE 0 END)/1e6, 2) as area_total_funding_m,
    
    -- Minority-serving institutions
    COUNTIF(ACTIVITY IN ('G12', 'U54', 'S06')) as minority_serving_awards,
    ROUND(SUM(CASE WHEN ACTIVITY IN ('G12', 'U54', 'S06') THEN TOTAL_LIFETIME_FUNDING ELSE 0 END)/1e6, 2) as minority_serving_funding_m,
    
    -- CTSA
    COUNTIF(ACTIVITY = 'UL1') as ctsa_awards,
    ROUND(SUM(CASE WHEN ACTIVITY = 'UL1' THEN TOTAL_LIFETIME_FUNDING ELSE 0 END)/1e6, 2) as ctsa_funding_m,
    
    -- Specialized Centers
    COUNTIF(ACTIVITY IN ('P50', 'P30', 'P60')) as specialized_center_awards,
    ROUND(SUM(CASE WHEN ACTIVITY IN ('P50', 'P30', 'P60') THEN TOTAL_LIFETIME_FUNDING ELSE 0 END)/1e6, 2) as specialized_center_funding_m,
    
    -- Infrastructure
    COUNTIF(ACTIVITY IN ('C06', 'G20')) as infrastructure_awards,
    ROUND(SUM(CASE WHEN ACTIVITY IN ('C06', 'G20') THEN TOTAL_LIFETIME_FUNDING ELSE 0 END)/1e6, 2) as infrastructure_funding_m

  FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`
  WHERE cluster_id IS NOT NULL
    AND PRIMARY_ORG IS NOT NULL
  GROUP BY institution
)
SELECT
  t.institution,
  t.total_awards,
  ROUND(t.total_funding/1e9, 2) as total_funding_billions,
  
  s.area_total_awards,
  s.area_total_funding_m,
  ROUND(s.area_total_awards * 100.0 / NULLIF(t.total_awards, 0), 1) as pct_area,
  
  s.minority_serving_awards,
  s.minority_serving_funding_m,
  ROUND(s.minority_serving_awards * 100.0 / NULLIF(t.total_awards, 0), 1) as pct_minority_serving,
  
  s.ctsa_awards,
  s.ctsa_funding_m,
  
  s.specialized_center_awards,
  s.specialized_center_funding_m,
  
  s.infrastructure_awards,
  s.infrastructure_funding_m,
  
  -- Classification
  CASE
    WHEN s.ctsa_awards > 0 THEN 'Academic Medical Center'
    WHEN s.area_total_awards > 5 THEN 'Undergraduate-Focused'
    WHEN s.minority_serving_awards > 0 THEN 'Minority-Serving Institution'
    WHEN s.specialized_center_awards >= 3 THEN 'Specialized Research Center'
    ELSE 'Research University'
  END as institution_type

FROM total_portfolio t
LEFT JOIN specialized_awards s ON t.institution = s.institution
ORDER BY t.total_funding DESC;
EOSQL

echo "✓ Created institution_specialization"

# Step 3: Geographic Analysis
echo ""
echo "[3/4] Analyzing geographic patterns..."

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.institution_geography` AS
SELECT
  PRIMARY_ORG as institution,
  ORG_STATE as state,
  ORG_CITY as city,
  ORG_COUNTRY as country,
  ORG_ZIPCODE as zipcode,
  
  COUNT(DISTINCT CORE_PROJECT_NUM) as awards_in_location,
  ROUND(SUM(TOTAL_LIFETIME_FUNDING)/1e6, 2) as funding_millions,
  COUNT(DISTINCT contact_pi_name) as pis_in_location

FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`
WHERE cluster_id IS NOT NULL
  AND PRIMARY_ORG IS NOT NULL
GROUP BY institution, state, city, country, zipcode
ORDER BY institution, funding_millions DESC;
EOSQL

echo "✓ Created institution_geography"

# Step 4: Comprehensive Institution Cards
echo ""
echo "[4/4] Assembling comprehensive institution cards..."

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.institution_cards_complete` AS
WITH base_metrics AS (
  SELECT
    PRIMARY_ORG as institution,
    
    -- Overall metrics
    COUNT(DISTINCT CORE_PROJECT_NUM) as total_awards,
    ROUND(SUM(TOTAL_LIFETIME_FUNDING)/1e9, 2) as total_funding_billions,
    
    -- Research profile
    COUNT(DISTINCT domain_id) as num_domains,
    COUNT(DISTINCT cluster_id) as num_topics,
    APPROX_TOP_COUNT(domain_name, 5) as top_domains,
    APPROX_TOP_COUNT(cluster_label, 10) as top_topics,
    
    -- People
    COUNT(DISTINCT contact_pi_name) as total_unique_pis,
    
    -- Temporal
    MIN(FIRST_FISCAL_YEAR) as first_award_year,
    MAX(LAST_FISCAL_YEAR) as last_award_year,
    
    -- Collaboration
    COUNTIF(is_mpi) as total_mpi_awards,
    ROUND(COUNTIF(is_mpi) * 100.0 / COUNT(*), 1) as pct_collaborative,
    
    -- Output
    SUM(publication_count) as total_publications,
    ROUND(AVG(publication_count), 1) as avg_pubs_per_award,
    
    -- Funding sources
    COUNT(DISTINCT ADMINISTERING_IC) as num_funding_ics

  FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`
  WHERE cluster_id IS NOT NULL
    AND PRIMARY_ORG IS NOT NULL
  GROUP BY institution
),
award_portfolio AS (
  SELECT
    PRIMARY_ORG as institution,
    COUNTIF(ACTIVITY IN ('R01', 'R03', 'R15', 'R21', 'R34', 'R35', 'R37', 'R56', 'RF1', 'RM1', 'DP1', 'DP2', 'DP5')) as rpg_total,
    ROUND(SUM(CASE WHEN ACTIVITY IN ('R01', 'R03', 'R15', 'R21', 'R34', 'R35', 'R37', 'R56', 'RF1', 'RM1', 'DP1', 'DP2', 'DP5') THEN TOTAL_LIFETIME_FUNDING ELSE 0 END)/1e9, 2) as rpg_funding_b,
    
    COUNTIF(ACTIVITY LIKE 'P%') as center_total,
    ROUND(SUM(CASE WHEN ACTIVITY LIKE 'P%' THEN TOTAL_LIFETIME_FUNDING ELSE 0 END)/1e9, 2) as center_funding_b,
    
    COUNTIF(ACTIVITY IN ('F30', 'F31', 'F32', 'F33', 'K01', 'K02', 'K07', 'K08', 'K22', 'K23', 'K24', 'K25', 'K99', 'R00')) as fellowship_total,
    ROUND(SUM(CASE WHEN ACTIVITY IN ('F30', 'F31', 'F32', 'F33', 'K01', 'K02', 'K07', 'K08', 'K22', 'K23', 'K24', 'K25', 'K99', 'R00') THEN TOTAL_LIFETIME_FUNDING ELSE 0 END)/1e9, 2) as fellowship_funding_b,
    
    COUNTIF(ACTIVITY IN ('T32', 'T34', 'T35', 'T36', 'T37', 'T90', 'TL1', 'TU2')) as training_total,
    ROUND(SUM(CASE WHEN ACTIVITY IN ('T32', 'T34', 'T35', 'T36', 'T37', 'T90', 'TL1', 'TU2') THEN TOTAL_LIFETIME_FUNDING ELSE 0 END)/1e9, 2) as training_funding_b,
    
    COUNTIF(ACTIVITY IN ('R41', 'R42', 'R43', 'R44', 'U43', 'U44')) as sbir_total,
    ROUND(SUM(CASE WHEN ACTIVITY IN ('R41', 'R42', 'R43', 'R44', 'U43', 'U44') THEN TOTAL_LIFETIME_FUNDING ELSE 0 END)/1e9, 2) as sbir_funding_b
    
  FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`
  WHERE cluster_id IS NOT NULL
    AND PRIMARY_ORG IS NOT NULL
  GROUP BY institution
)
SELECT
  b.*,
  p.rpg_total,
  p.rpg_funding_b,
  p.center_total,
  p.center_funding_b,
  p.fellowship_total,
  p.fellowship_funding_b,
  p.training_total,
  p.training_funding_b,
  p.sbir_total,
  p.sbir_funding_b,
  
  -- Specialization
  s.institution_type,
  s.area_total_awards,
  s.area_total_funding_m,
  s.pct_area,
  s.minority_serving_awards,
  s.pct_minority_serving,
  s.ctsa_awards,
  s.specialized_center_awards,
  
  -- Geography
  g.state,
  g.city,
  g.country

FROM base_metrics b
LEFT JOIN award_portfolio p ON b.institution = p.institution
LEFT JOIN `od-cl-odss-conroyri-f75a.nih_analytics.institution_specialization` s ON b.institution = s.institution
LEFT JOIN (
  SELECT institution, ANY_VALUE(state) as state, ANY_VALUE(city) as city, ANY_VALUE(country) as country
  FROM `od-cl-odss-conroyri-f75a.nih_analytics.institution_geography`
  GROUP BY institution
) g ON b.institution = g.institution
WHERE b.total_awards >= 10
ORDER BY b.total_funding_billions DESC
LIMIT 500;
EOSQL

echo "✓ Created institution_cards_complete (top 500 institutions)"

echo ""
echo "=========================================="
echo "✅ FULL INSTITUTION CARDS CREATED"
echo "=========================================="
echo ""
echo "Tables created:"
echo "  - institution_temporal_trends (Institution × Year)"
echo "  - institution_specialization (AREA, CTSA, MSI)"
echo "  - institution_geography (Location data)"
echo "  - institution_cards_complete (Comprehensive profiles)"
echo ""
echo "Note: Department hierarchy not available in source data"
echo ""
