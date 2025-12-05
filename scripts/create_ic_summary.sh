#!/bin/bash
set -e

echo "Creating IC summary cards..."

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.ic_summary_simple` AS
SELECT
  ADMINISTERING_IC,
  organizational_category,
  COUNT(*) as total_awards,
  ROUND(SUM(TOTAL_LIFETIME_FUNDING)/1e9, 2) as funding_billions,
  COUNT(DISTINCT domain_id) as num_domains,
  COUNT(DISTINCT cluster_id) as num_topics,
  COUNT(DISTINCT PI_ID) as num_pis,
  COUNT(DISTINCT ORG_NAME) as num_institutions,
  SUM(publication_count) as total_publications,
  ROUND(AVG(publication_count), 1) as avg_pubs_per_award,
  COUNTIF(is_mpi) as mpi_awards,
  ROUND(COUNTIF(is_mpi) * 100.0 / COUNT(*), 1) as pct_mpi,
  MIN(FIRST_FISCAL_YEAR) as earliest_year,
  MAX(LAST_FISCAL_YEAR) as latest_year
FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`
WHERE cluster_id IS NOT NULL
GROUP BY ADMINISTERING_IC, organizational_category
ORDER BY funding_billions DESC;
EOSQL

echo "✓ Created ic_summary_simple"

# Display results
bq query --use_legacy_sql=false << 'EOSQL'
SELECT 
  ADMINISTERING_IC,
  total_awards,
  funding_billions,
  num_domains,
  num_topics,
  num_pis
FROM `od-cl-odss-conroyri-f75a.nih_analytics.ic_summary_simple`
ORDER BY funding_billions DESC
LIMIT 20;
EOSQL

echo ""
echo "✅ IC Summary Complete"
