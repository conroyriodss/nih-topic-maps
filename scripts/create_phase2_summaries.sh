#!/bin/bash
set -e

echo "Creating Phase 2 portfolio summaries..."

bq query --use_legacy_sql=false << 'EOSQL'
-- Domain summary with Phase 2 data
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.portfolio_domain_summary_v2` AS
SELECT 
  domain_id,
  domain_name,
  is_research_topic,
  COUNT(*) as num_awards,
  ROUND(SUM(TOTAL_LIFETIME_FUNDING)/1e9, 2) as funding_billions,
  ROUND(AVG(publication_count), 1) as avg_pubs,
  ROUND(AVG(pi_count), 2) as avg_pi_count,
  COUNTIF(is_mpi) as mpi_awards,
  ROUND(COUNTIF(is_mpi) * 100.0 / COUNT(*), 1) as pct_mpi,
  COUNTIF(clustering_phase = 'Phase 1') as phase1_awards,
  COUNTIF(clustering_phase = 'Phase 2') as phase2_awards,
  MIN(FIRST_FISCAL_YEAR) as earliest_year,
  MAX(LAST_FISCAL_YEAR) as latest_year
FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v2_0_complete`
WHERE is_clustered = TRUE
GROUP BY domain_id, domain_name, is_research_topic
ORDER BY funding_billions DESC;

-- Cluster summary with Phase 2 data
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.portfolio_cluster_summary_v2` AS
SELECT 
  domain_id,
  domain_name,
  cluster_id,
  cluster_label,
  COUNT(*) as num_awards,
  ROUND(SUM(TOTAL_LIFETIME_FUNDING)/1e9, 2) as funding_billions,
  ROUND(AVG(publication_count), 1) as avg_pubs,
  COUNTIF(clustering_phase = 'Phase 1') as phase1_awards,
  COUNTIF(clustering_phase = 'Phase 2') as phase2_awards,
  APPROX_TOP_COUNT(ADMINISTERING_IC, 5) as top_ics,
  AVG(umap_x) as centroid_x,
  AVG(umap_y) as centroid_y
FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v2_0_complete`
WHERE is_clustered = TRUE
GROUP BY domain_id, domain_name, cluster_id, cluster_label
ORDER BY funding_billions DESC;
EOSQL

echo "✓ Created portfolio summaries"

# Export to GCS
bq extract \
  --destination_format=PARQUET \
  --compression=SNAPPY \
  od-cl-odss-conroyri-f75a:nih_analytics.grant_cards_v2_0_complete \
  'gs://nih-analytics-exports/v2/grant_cards_complete_*.parquet'

echo "✓ Exported to GCS"
