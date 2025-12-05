#!/bin/bash
set -e

echo "=========================================="
echo "UPDATING GRANT CARDS WITH PHASE 2 RESULTS"
echo "=========================================="

echo ""
echo "[1/4] Checking current clustering status..."

bq query --use_legacy_sql=false << 'EOSQL'
SELECT 
  'Current Status' as status,
  COUNTIF(cluster_id IS NOT NULL) as clustered,
  COUNTIF(cluster_id IS NULL) as unclustered,
  COUNT(*) as total,
  ROUND(COUNTIF(cluster_id IS NOT NULL) * 100.0 / COUNT(*), 1) as pct_clustered
FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`;
EOSQL

echo ""
echo "[2/4] Creating backup of current grant_cards..."

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_backup_before_phase2` 
AS SELECT * FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`;
EOSQL

echo "  ✓ Backup created: grant_cards_v1_6_backup_before_phase2"

echo ""
echo "[3/4] Updating grant_cards with Phase 2 assignments..."

bq query --use_legacy_sql=false << 'EOSQL'
-- Create new version with Phase 2 assignments
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v2_0_complete` AS
SELECT 
  g.*,
  
  -- Update cluster info from Phase 2 (if available)
  COALESCE(p.cluster_id, g.cluster_id) as cluster_id_updated,
  COALESCE(p.cluster_label, g.cluster_label) as cluster_label_updated,
  COALESCE(p.domain_id, g.domain_id) as domain_id_updated,
  COALESCE(p.domain_name, g.domain_name) as domain_name_updated,
  COALESCE(p.umap_x, g.umap_x) as umap_x_updated,
  COALESCE(p.umap_y, g.umap_y) as umap_y_updated,
  
  -- Update flags
  CASE 
    WHEN p.cluster_id IS NOT NULL THEN TRUE
    WHEN g.cluster_id IS NOT NULL THEN TRUE
    ELSE FALSE
  END as is_clustered_updated,
  
  -- Track which phase
  CASE 
    WHEN p.cluster_id IS NOT NULL THEN 'Phase 2'
    WHEN g.cluster_id IS NOT NULL THEN 'Phase 1'
    ELSE 'Unclustered'
  END as clustering_phase,
  
  p.cluster_distance as phase2_cluster_distance

FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency` g
LEFT JOIN `od-cl-odss-conroyri-f75a.nih_analytics.phase2_cluster_assignments` p
  ON g.CORE_PROJECT_NUM = p.CORE_PROJECT_NUM;

-- Replace old columns with updated ones
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v2_0_complete` AS
SELECT 
  * EXCEPT(
    cluster_id, cluster_label, domain_id, domain_name, 
    umap_x, umap_y, is_clustered,
    cluster_id_updated, cluster_label_updated, domain_id_updated, 
    domain_name_updated, umap_x_updated, umap_y_updated, is_clustered_updated
  ),
  cluster_id_updated as cluster_id,
  cluster_label_updated as cluster_label,
  domain_id_updated as domain_id,
  domain_name_updated as domain_name,
  umap_x_updated as umap_x,
  umap_y_updated as umap_y,
  is_clustered_updated as is_clustered,
  clustering_phase,
  phase2_cluster_distance
FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v2_0_complete`;
EOSQL

echo "  ✓ Created grant_cards_v2_0_complete"

echo ""
echo "[4/4] Verifying results..."

bq query --use_legacy_sql=false << 'EOSQL'
SELECT 
  clustering_phase,
  COUNT(*) as num_awards,
  ROUND(SUM(TOTAL_LIFETIME_FUNDING)/1e9, 2) as funding_billions,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as pct_of_total,
  COUNT(DISTINCT domain_id) as num_domains,
  COUNT(DISTINCT cluster_id) as num_clusters
FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v2_0_complete`
GROUP BY clustering_phase
ORDER BY num_awards DESC;
EOSQL

echo ""
echo "=========================================="
echo "✅ GRANT CARDS UPDATE COMPLETE"
echo "=========================================="
echo ""
echo "Tables Created:"
echo "  - grant_cards_v1_6_backup_before_phase2 (backup)"
echo "  - grant_cards_v2_0_complete (NEW, with 100% coverage)"
echo ""
echo "Next Steps:"
echo "  1. Generate updated visualizations"
echo "  2. Export new portfolio summaries"
echo "  3. Create Phase 2 documentation"
echo ""
