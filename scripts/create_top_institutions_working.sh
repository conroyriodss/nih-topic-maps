#!/bin/bash
set -e

echo "Creating top institutions summary..."

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.top_institutions_simple` AS
SELECT
  PRIMARY_ORG as institution_name,
  COUNT(DISTINCT CORE_PROJECT_NUM) as total_awards,
  ROUND(SUM(TOTAL_LIFETIME_FUNDING)/1e9, 2) as funding_billions,
  COUNT(DISTINCT domain_id) as num_domains,
  COUNT(DISTINCT cluster_id) as num_topics,
  COUNT(DISTINCT contact_pi_name) as num_contact_pis,
  SUM(publication_count) as total_publications,
  ROUND(AVG(publication_count), 1) as avg_pubs_per_award,
  COUNTIF(is_mpi) as mpi_awards,
  ROUND(COUNTIF(is_mpi) * 100.0 / COUNT(*), 1) as pct_collaborative,
  COUNT(DISTINCT ADMINISTERING_IC) as num_funding_ics,
  APPROX_TOP_COUNT(domain_name, 5) as top_research_domains,
  MIN(FIRST_FISCAL_YEAR) as first_award_year,
  MAX(LAST_FISCAL_YEAR) as last_award_year
FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`
WHERE PRIMARY_ORG IS NOT NULL
  AND cluster_id IS NOT NULL
GROUP BY PRIMARY_ORG
HAVING total_awards >= 10
ORDER BY funding_billions DESC
LIMIT 50;
EOSQL

echo "✓ Created top_institutions_simple"

bq query --use_legacy_sql=false << 'EOSQL'
SELECT 
  institution_name,
  total_awards,
  funding_billions,
  num_domains,
  num_contact_pis,
  total_publications,
  top_research_domains[OFFSET(0)].value as top_domain
FROM `od-cl-odss-conroyri-f75a.nih_analytics.top_institutions_simple`
ORDER BY funding_billions DESC
LIMIT 20;
EOSQL

echo "✅ Top Institutions Complete"
