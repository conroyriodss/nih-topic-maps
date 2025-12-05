#!/bin/bash
set -e

echo "=========================================="
echo "CREATING FULL PI CARDS"
echo "With mobility, collaboration & impact"
echo "=========================================="
echo ""

# Step 1: PI Institutional Mobility Tracking
echo "[1/5] Analyzing PI institutional mobility..."

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.pi_institutional_history` AS
WITH pi_institution_years AS (
  SELECT
    contact_pi_name,
    PRIMARY_ORG as institution,
    fiscal_year,
    COUNT(DISTINCT CORE_PROJECT_NUM) as num_awards_that_year,
    SUM(FY_TOTAL_COST) as funding_that_year
  FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`
  WHERE contact_pi_name IS NOT NULL
    AND cluster_id IS NOT NULL
  GROUP BY contact_pi_name, PRIMARY_ORG, fiscal_year
)
SELECT
  contact_pi_name,
  institution,
  MIN(fiscal_year) as first_year_at_institution,
  MAX(fiscal_year) as last_year_at_institution,
  COUNT(DISTINCT fiscal_year) as num_active_years,
  SUM(num_awards_that_year) as total_awards_at_institution,
  ROUND(SUM(funding_that_year)/1e6, 2) as total_funding_millions
FROM pi_institution_years
GROUP BY contact_pi_name, institution
ORDER BY contact_pi_name, first_year_at_institution;
EOSQL

echo "✓ Created pi_institutional_history"

# Step 2: PI Collaboration Networks
echo ""
echo "[2/5] Building PI collaboration networks..."

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.pi_collaborations` AS
WITH mpi_awards AS (
  SELECT
    CORE_PROJECT_NUM,
    contact_pi_name,
    all_pi_names,
    ADMINISTERING_IC,
    fiscal_year,
    FY_TOTAL_COST,
    cluster_label
  FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`
  WHERE is_mpi = TRUE
    AND contact_pi_name IS NOT NULL
    AND cluster_id IS NOT NULL
)
SELECT
  contact_pi_name as pi,
  
  -- Extract collaborators from all_pi_names
  -- Note: This is simplified - all_pi_names contains semicolon-separated list
  all_pi_names as all_collaborators,
  
  -- Collaboration metrics
  COUNT(DISTINCT CORE_PROJECT_NUM) as num_collaborative_projects,
  COUNT(DISTINCT ADMINISTERING_IC) as num_ics_collaborated,
  COUNT(DISTINCT cluster_label) as num_topics_collaborated,
  
  -- Temporal
  MIN(fiscal_year) as first_collaboration_year,
  MAX(fiscal_year) as latest_collaboration_year,
  
  -- Funding
  ROUND(SUM(FY_TOTAL_COST)/1e6, 2) as total_collaborative_funding_millions,
  
  -- Top collaboration topics
  APPROX_TOP_COUNT(cluster_label, 5) as top_collaboration_topics

FROM mpi_awards
GROUP BY contact_pi_name, all_pi_names
HAVING num_collaborative_projects >= 1;
EOSQL

echo "✓ Created pi_collaborations"

# Step 3: PI Award Type Portfolio
echo ""
echo "[3/5] Analyzing PI award portfolios..."

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.pi_award_portfolio` AS
WITH award_classifications AS (
  SELECT
    contact_pi_name,
    CORE_PROJECT_NUM,
    ACTIVITY,
    TOTAL_LIFETIME_FUNDING,
    fiscal_year,
    
    -- Award categories
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
      ELSE 'Other'
    END as award_category,
    
    -- Career stage indicators
    CASE
      WHEN ACTIVITY IN ('K99', 'R00', 'K01', 'K08', 'K23', 'DP2') THEN 'Early Career'
      WHEN ACTIVITY IN ('R35', 'R37', 'P01') THEN 'Senior/Established'
      ELSE 'Mid-Career'
    END as career_stage_indicator
    
  FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`
  WHERE contact_pi_name IS NOT NULL
    AND cluster_id IS NOT NULL
)
SELECT
  contact_pi_name,
  
  -- Award type counts
  COUNTIF(award_category = 'RPG') as rpg_awards,
  ROUND(SUM(CASE WHEN award_category = 'RPG' THEN TOTAL_LIFETIME_FUNDING ELSE 0 END)/1e6, 2) as rpg_funding_m,
  
  COUNTIF(award_category = 'Centers') as center_awards,
  ROUND(SUM(CASE WHEN award_category = 'Centers' THEN TOTAL_LIFETIME_FUNDING ELSE 0 END)/1e6, 2) as center_funding_m,
  
  COUNTIF(award_category = 'Fellowship/Career') as fellowship_awards,
  ROUND(SUM(CASE WHEN award_category = 'Fellowship/Career' THEN TOTAL_LIFETIME_FUNDING ELSE 0 END)/1e6, 2) as fellowship_funding_m,
  
  COUNTIF(award_category = 'Training') as training_awards,
  ROUND(SUM(CASE WHEN award_category = 'Training' THEN TOTAL_LIFETIME_FUNDING ELSE 0 END)/1e6, 2) as training_funding_m,
  
  COUNTIF(award_category = 'SBIR/STTR') as sbir_awards,
  ROUND(SUM(CASE WHEN award_category = 'SBIR/STTR' THEN TOTAL_LIFETIME_FUNDING ELSE 0 END)/1e6, 2) as sbir_funding_m,
  
  -- Career stage timeline
  MIN(CASE WHEN career_stage_indicator = 'Early Career' THEN fiscal_year END) as first_early_career_award,
  MIN(CASE WHEN career_stage_indicator = 'Senior/Established' THEN fiscal_year END) as first_senior_award,
  
  -- Top activity codes
  APPROX_TOP_COUNT(ACTIVITY, 5) as top_activity_codes

FROM award_classifications
GROUP BY contact_pi_name;
EOSQL

echo "✓ Created pi_award_portfolio"

# Step 4: PI Patents & Clinical Studies (Placeholder - would need external data)
echo ""
echo "[4/5] Creating PI impact metrics template..."

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.pi_broader_impact` AS
SELECT
  contact_pi_name,
  
  -- Publications (from grant data)
  SUM(publication_count) as total_publications,
  
  -- Patents (placeholder - would integrate with USPTO data)
  CAST(NULL AS INT64) as patent_count,
  CAST(NULL AS STRING) as patent_ids,
  
  -- Clinical trials (placeholder - would integrate with ClinicalTrials.gov)
  CAST(NULL AS INT64) as clinical_trial_count,
  CAST(NULL AS STRING) as clinical_trial_ids,
  
  -- ORCID (placeholder - would need to link external data)
  CAST(NULL AS STRING) as orcid_id,
  
  -- Research output metrics
  ROUND(AVG(publication_count), 1) as avg_pubs_per_award

FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`
WHERE contact_pi_name IS NOT NULL
  AND cluster_id IS NOT NULL
GROUP BY contact_pi_name;
EOSQL

echo "✓ Created pi_broader_impact (with placeholders for patents/trials)"

# Step 5: Comprehensive PI Cards
echo ""
echo "[5/5] Assembling comprehensive PI cards..."

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.pi_cards_complete` AS
WITH base_metrics AS (
  SELECT
    contact_pi_name,
    
    -- Current/primary affiliation (most recent)
    ARRAY_AGG(PRIMARY_ORG ORDER BY LAST_FISCAL_YEAR DESC LIMIT 1)[OFFSET(0)] as current_institution,
    
    -- Career span
    MIN(FIRST_FISCAL_YEAR) as career_start_year,
    MAX(LAST_FISCAL_YEAR) as career_last_active_year,
    
    -- Overall metrics
    COUNT(DISTINCT CORE_PROJECT_NUM) as total_awards,
    ROUND(SUM(TOTAL_LIFETIME_FUNDING)/1e6, 2) as total_funding_millions,
    
    -- Research profile
    COUNT(DISTINCT domain_id) as num_research_domains,
    COUNT(DISTINCT cluster_id) as num_research_topics,
    APPROX_TOP_COUNT(cluster_label, 5) as top_research_areas,
    APPROX_TOP_COUNT(domain_name, 3) as top_domains,
    
    -- Funding sources
    COUNT(DISTINCT ADMINISTERING_IC) as num_funding_ics,
    APPROX_TOP_COUNT(ADMINISTERING_IC, 3) as top_funding_ics,
    
    -- Collaboration
    COUNTIF(is_mpi) as mpi_awards,
    ROUND(COUNTIF(is_mpi) * 100.0 / COUNT(*), 1) as pct_collaborative

  FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`
  WHERE contact_pi_name IS NOT NULL
    AND cluster_id IS NOT NULL
  GROUP BY contact_pi_name
),
mobility_summary AS (
  SELECT
    contact_pi_name,
    COUNT(DISTINCT institution) as num_institutions,
    ARRAY_AGG(STRUCT(
      institution,
      first_year_at_institution,
      last_year_at_institution,
      num_active_years,
      total_funding_millions
    ) ORDER BY first_year_at_institution) as institutional_history
  FROM `od-cl-odss-conroyri-f75a.nih_analytics.pi_institutional_history`
  GROUP BY contact_pi_name
),
collaboration_summary AS (
  SELECT
    pi as contact_pi_name,
    SUM(num_collaborative_projects) as total_collaborative_projects,
    SUM(total_collaborative_funding_millions) as total_collaborative_funding_m
  FROM `od-cl-odss-conroyri-f75a.nih_analytics.pi_collaborations`
  GROUP BY pi
)
SELECT
  b.*,
  
  -- Institutional mobility
  COALESCE(m.num_institutions, 1) as num_institutions_worked,
  m.institutional_history,
  
  -- Award portfolio
  p.rpg_awards,
  p.rpg_funding_m,
  p.center_awards,
  p.center_funding_m,
  p.fellowship_awards,
  p.fellowship_funding_m,
  p.training_awards,
  p.training_funding_m,
  p.sbir_awards,
  p.sbir_funding_m,
  p.first_early_career_award,
  p.first_senior_award,
  p.top_activity_codes,
  
  -- Collaboration
  COALESCE(c.total_collaborative_projects, 0) as collaborative_project_count,
  COALESCE(c.total_collaborative_funding_m, 0) as collaborative_funding_m,
  
  -- Impact
  i.total_publications,
  i.avg_pubs_per_award,
  i.patent_count,
  i.clinical_trial_count,
  i.orcid_id,
  
  -- Derived metrics
  b.career_last_active_year - b.career_start_year as career_span_years,
  ROUND(b.total_funding_millions / b.total_awards, 2) as avg_funding_per_award

FROM base_metrics b
LEFT JOIN mobility_summary m ON b.contact_pi_name = m.contact_pi_name
LEFT JOIN `od-cl-odss-conroyri-f75a.nih_analytics.pi_award_portfolio` p ON b.contact_pi_name = p.contact_pi_name
LEFT JOIN collaboration_summary c ON b.contact_pi_name = c.contact_pi_name
LEFT JOIN `od-cl-odss-conroyri-f75a.nih_analytics.pi_broader_impact` i ON b.contact_pi_name = i.contact_pi_name
WHERE b.total_awards >= 3  -- Focus on PIs with sustained funding
ORDER BY b.total_funding_millions DESC
LIMIT 1000;  -- Top 1000 PIs
EOSQL

echo "✓ Created pi_cards_complete (top 1000 PIs)"

echo ""
echo "=========================================="
echo "✅ FULL PI CARDS CREATED"
echo "=========================================="
echo ""
echo "Tables created:"
echo "  - pi_institutional_history (PI × Institution × Years)"
echo "  - pi_collaborations (PI collaboration networks)"
echo "  - pi_award_portfolio (Award type breakdowns)"
echo "  - pi_broader_impact (Publications, patents*, trials*)"
echo "  - pi_cards_complete (Comprehensive PI profiles)"
echo ""
echo "* Patents and clinical trials are placeholders"
echo "  Requires integration with USPTO and ClinicalTrials.gov"
echo ""
