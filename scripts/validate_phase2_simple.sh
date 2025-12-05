#!/bin/bash
set -e

echo "=========================================="
echo "PHASE 2 DATA VALIDATION (SIMPLE)"
echo "=========================================="
echo ""

# Basic counts
echo "[1/3] Basic statistics..."
bq query --use_legacy_sql=false << 'EOSQL'
SELECT
  'Total Records' as metric,
  CAST(COUNT(*) AS STRING) as value
FROM `od-cl-odss-conroyri-f75a.nih_analytics.phase2_cluster_assignments`
UNION ALL
SELECT
  'Unique Projects',
  CAST(COUNT(DISTINCT CORE_PROJECT_NUM) AS STRING)
FROM `od-cl-odss-conroyri-f75a.nih_analytics.phase2_cluster_assignments`
UNION ALL
SELECT
  'Unique Clusters',
  CAST(COUNT(DISTINCT cluster_id) AS STRING)
FROM `od-cl-odss-conroyri-f75a.nih_analytics.phase2_cluster_assignments`
UNION ALL
SELECT
  'Unique Domains',
  CAST(COUNT(DISTINCT domain_id) AS STRING)
FROM `od-cl-odss-conroyri-f75a.nih_analytics.phase2_cluster_assignments`
UNION ALL
SELECT
  'Null Clusters',
  CAST(COUNTIF(cluster_id IS NULL) AS STRING)
FROM `od-cl-odss-conroyri-f75a.nih_analytics.phase2_cluster_assignments`;
EOSQL

# Cluster distribution
echo ""
echo "[2/3] Cluster distribution (top 15)..."
bq query --use_legacy_sql=false << 'EOSQL'
SELECT
  cluster_id,
  ANY_VALUE(cluster_label) as cluster_label,
  ANY_VALUE(domain_name) as domain_name,
  COUNT(*) as num_awards,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as pct
FROM `od-cl-odss-conroyri-f75a.nih_analytics.phase2_cluster_assignments`
GROUP BY cluster_id
ORDER BY num_awards DESC
LIMIT 15;
EOSQL

# Check overlap with Phase 1
echo ""
echo "[3/3] Checking overlap with existing clustered data..."
bq query --use_legacy_sql=false << 'EOSQL'
WITH phase2_projects AS (
  SELECT DISTINCT CORE_PROJECT_NUM
  FROM `od-cl-odss-conroyri-f75a.nih_analytics.phase2_cluster_assignments`
),
phase1_projects AS (
  SELECT DISTINCT CORE_PROJECT_NUM
  FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`
  WHERE cluster_id IS NOT NULL
)
SELECT
  'Phase 2 Awards' as metric,
  COUNT(*) as count
FROM phase2_projects
UNION ALL
SELECT
  'Already Clustered (Phase 1)',
  COUNT(*)
FROM phase1_projects
UNION ALL
SELECT
  'Overlap (Should be 0)',
  COUNT(*)
FROM phase2_projects p2
JOIN phase1_projects p1 ON p2.CORE_PROJECT_NUM = p1.CORE_PROJECT_NUM;
EOSQL

echo ""
echo "=========================================="
echo "✅ VALIDATION COMPLETE"
echo "=========================================="
