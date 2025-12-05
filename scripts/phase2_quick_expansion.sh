#!/bin/bash
set -e

echo "=========================================="
echo "PHASE 2: QUICK CLUSTER EXPANSION"
echo "Using IC-based heuristic assignment"
echo "=========================================="
echo ""

# Step 1: Create unclustered dataset
echo "[1/4] Identifying unclustered awards..."

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.phase2_unclustered_awards` AS
SELECT 
  CORE_PROJECT_NUM,
  ADMINISTERING_IC,
  organizational_category,
  type1_title,
  TOTAL_LIFETIME_FUNDING,
  publication_count,
  FIRST_FISCAL_YEAR,
  LAST_FISCAL_YEAR
FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`
WHERE cluster_id IS NULL;
EOSQL

echo "  ✓ Identified unclustered awards"

bq query --use_legacy_sql=false << 'EOSQL'
SELECT 
  COUNT(*) as unclustered_awards,
  ROUND(SUM(TOTAL_LIFETIME_FUNDING)/1e9, 2) as funding_billions
FROM `od-cl-odss-conroyri-f75a.nih_analytics.phase2_unclustered_awards`;
EOSQL

# Step 2: Assign clusters based on IC patterns
echo ""
echo "[2/4] Assigning clusters using IC-based heuristics..."

bq query --use_legacy_sql=false << 'EOSQL'
-- Assign to most common cluster for each IC
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.phase2_cluster_assignments` AS
WITH ic_cluster_stats AS (
  -- For each IC, find the most common cluster
  SELECT 
    ADMINISTERING_IC,
    cluster_id,
    cluster_label,
    domain_id,
    domain_name,
    COUNT(*) as cluster_count,
    ROUND(AVG(umap_x), 4) as avg_umap_x,
    ROUND(AVG(umap_y), 4) as avg_umap_y,
    ROW_NUMBER() OVER (PARTITION BY ADMINISTERING_IC ORDER BY COUNT(*) DESC) as rank
  FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`
  WHERE cluster_id IS NOT NULL
  GROUP BY ADMINISTERING_IC, cluster_id, cluster_label, domain_id, domain_name
)
SELECT 
  u.CORE_PROJECT_NUM,
  COALESCE(ic.cluster_id, 74) as cluster_id,  -- Default to cluster 74 if no match
  COALESCE(ic.cluster_label, 'Unmapped') as cluster_label,
  COALESCE(ic.domain_id, 'D99_UNMAPPED') as domain_id,
  COALESCE(ic.domain_name, 'Unmapped') as domain_name,
  COALESCE(ic.avg_umap_x, 0.0) as umap_x,
  COALESCE(ic.avg_umap_y, 0.0) as umap_y,
  ic.cluster_count as ic_cluster_size,
  'IC-based heuristic' as assignment_method
FROM `od-cl-odss-conroyri-f75a.nih_analytics.phase2_unclustered_awards` u
LEFT JOIN ic_cluster_stats ic
  ON u.ADMINISTERING_IC = ic.ADMINISTERING_IC
  AND ic.rank = 1;  -- Most common cluster for this IC
EOSQL

echo "  ✓ Created cluster assignments"

# Step 3: Verify assignments
echo ""
echo "[3/4] Verifying assignments..."

bq query --use_legacy_sql=false << 'EOSQL'
SELECT 
  'Phase 2 Assignments' as metric,
  COUNT(*) as total,
  COUNT(DISTINCT cluster_id) as clusters,
  COUNT(DISTINCT domain_id) as domains,
  COUNTIF(cluster_id = 74) as unmapped_count
FROM `od-cl-odss-conroyri-f75a.nih_analytics.phase2_cluster_assignments`;
EOSQL

echo ""
echo "Cluster distribution:"
bq query --use_legacy_sql=false << 'EOSQL'
SELECT 
  domain_name,
  COUNT(*) as num_awards,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as pct
FROM `od-cl-odss-conroyri-f75a.nih_analytics.phase2_cluster_assignments`
GROUP BY domain_name
ORDER BY num_awards DESC
LIMIT 10;
EOSQL

# Step 4: Create v2.0 grant cards
echo ""
echo "[4/4] Creating grant_cards v2.0 with full coverage..."

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v2_0_complete` AS
SELECT 
  g.*,
  
  -- Override cluster fields with Phase 2 assignments where needed
  COALESCE(g.cluster_id, p.cluster_id) as cluster_id_final,
  COALESCE(g.cluster_label, p.cluster_label) as cluster_label_final,
  COALESCE(g.domain_id, p.domain_id) as domain_id_final,
  COALESCE(g.domain_name, p.domain_name) as domain_name_final,
  COALESCE(g.umap_x, p.umap_x) as umap_x_final,
  COALESCE(g.umap_y, p.umap_y) as umap_y_final,
  
  -- Track which phase
  CASE 
    WHEN g.cluster_id IS NOT NULL THEN 'Phase 1 (ML)'
    WHEN p.cluster_id IS NOT NULL THEN 'Phase 2 (IC-heuristic)'
    ELSE 'Unclustered'
  END as clustering_phase,
  
  p.assignment_method as phase2_method

FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency` g
LEFT JOIN `od-cl-odss-conroyri-f75a.nih_analytics.phase2_cluster_assignments` p
  ON g.CORE_PROJECT_NUM = p.CORE_PROJECT_NUM;

-- Clean up column names
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v2_0_complete` AS
SELECT 
  * EXCEPT(
    cluster_id, cluster_label, domain_id, domain_name, umap_x, umap_y, is_clustered,
    cluster_id_final, cluster_label_final, domain_id_final, 
    domain_name_final, umap_x_final, umap_y_final
  ),
  cluster_id_final as cluster_id,
  cluster_label_final as cluster_label,
  domain_id_final as domain_id,
  domain_name_final as domain_name,
  umap_x_final as umap_x,
  umap_y_final as umap_y,
  CASE WHEN cluster_id_final IS NOT NULL THEN TRUE ELSE FALSE END as is_clustered,
  clustering_phase,
  phase2_method
FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v2_0_complete`;
EOSQL

echo "  ✓ Created grant_cards_v2_0_complete"

# Final summary
echo ""
echo "=========================================="
echo "FINAL SUMMARY"
echo "=========================================="

bq query --use_legacy_sql=false << 'EOSQL'
SELECT 
  clustering_phase,
  COUNT(*) as num_awards,
  ROUND(SUM(TOTAL_LIFETIME_FUNDING)/1e9, 2) as funding_billions,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as pct_total,
  COUNT(DISTINCT ADMINISTERING_IC) as num_ics,
  COUNT(DISTINCT domain_id) as num_domains,
  COUNT(DISTINCT cluster_id) as num_clusters
FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v2_0_complete`
GROUP BY clustering_phase
ORDER BY num_awards DESC;
EOSQL

echo ""
echo "=========================================="
echo "✅ PHASE 2 EXPANSION COMPLETE"
echo "=========================================="
echo ""
echo "Tables Created:"
echo "  - phase2_unclustered_awards (input)"
echo "  - phase2_cluster_assignments (assignments)"
echo "  - grant_cards_v2_0_complete (FINAL)"
echo ""
echo "Coverage: 100% of portfolio"
echo "Method: IC-based heuristic for Phase 2 awards"
echo ""
echo "Next Steps:"
echo "  1. Review domain distribution"
echo "  2. Generate updated visualizations"
echo "  3. Export v2.0 datasets"
echo ""
