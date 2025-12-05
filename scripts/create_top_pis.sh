#!/bin/bash
set -e

echo "Creating top PIs summary..."

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.top_pis_simple` AS
WITH pi_metrics AS (
  SELECT
    PI_ID,
    ANY_VALUE(PI_NAME) as pi_name,
    ANY_VALUE(ORG_NAME) as primary_institution,
    COUNT(DISTINCT CORE_PROJECT_NUM) as total_awards,
    ROUND(SUM(TOTAL_LIFETIME_FUNDING)/1e6, 2) as funding_millions,
    SUM(publication_count) as total_publications,
    SUM(citation_count) as total_citations,
    COUNT(DISTINCT domain_id) as num_domains,
    COUNT(DISTINCT cluster_id) as num_topics,
    MIN(FIRST_FISCAL_YEAR) as career_start,
    MAX(LAST_FISCAL_YEAR) as career_last_active,
    COUNTIF(is_mpi) as mpi_awards,
    APPROX_TOP_COUNT(cluster_label, 3) as top_research_areas,
    APPROX_TOP_COUNT(ADMINISTERING_IC, 3) as top_funding_ics
  FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`
  WHERE PI_ID IS NOT NULL
    AND cluster_id IS NOT NULL
  GROUP BY PI_ID
  HAVING total_awards >= 3  -- Filter for active researchers
)
SELECT *,
  ROUND(total_citations / NULLIF(total_publications, 0), 1) as avg_citations_per_pub,
  career_last_active - career_start as career_span_years,
  ROUND(funding_millions / total_awards, 2) as avg_funding_per_award
FROM pi_metrics
ORDER BY funding_millions DESC
LIMIT 100;
EOSQL

echo "✓ Created top_pis_simple"

# Display results
bq query --use_legacy_sql=false << 'EOSQL'
SELECT 
  pi_name,
  primary_institution,
  total_awards,
  funding_millions,
  total_publications,
  career_span_years,
  top_research_areas[OFFSET(0)].value as top_area
FROM `od-cl-odss-conroyri-f75a.nih_analytics.top_pis_simple`
ORDER BY funding_millions DESC
LIMIT 20;
EOSQL

echo ""
echo "✅ Top PIs Complete"
