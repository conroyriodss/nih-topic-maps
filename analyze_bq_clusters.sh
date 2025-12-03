#!/bin/bash

echo "========================================================================"
echo "BIGQUERY CLUSTER ANALYSIS"
echo "========================================================================"

# 1. Cluster size distribution
echo ""
echo "📊 Cluster Size Distribution:"
bq query --use_legacy_sql=false '
SELECT 
  cluster,
  COUNT(*) as grants,
  COUNT(DISTINCT IC_NAME_x) as unique_ics,
  CAST(MIN(FY_x) AS INT64) as earliest_fy,
  CAST(MAX(FY_x) AS INT64) as latest_fy
FROM `od-cl-odss-conroyri-f75a.nih_exporter.clustered_50k_semantic`
GROUP BY cluster
ORDER BY grants DESC
LIMIT 10'

# 2. Sample titles from top clusters
echo ""
echo "📝 Sample Project Titles (Top 3 Clusters):"
bq query --use_legacy_sql=false '
WITH top_clusters AS (
  SELECT cluster
  FROM `od-cl-odss-conroyri-f75a.nih_exporter.clustered_50k_semantic`
  GROUP BY cluster
  ORDER BY COUNT(*) DESC
  LIMIT 3
)
SELECT 
  cluster,
  PROJECT_TITLE_x as project_title,
  IC_NAME_x as ic_name,
  CAST(FY_x AS INT64) as fy
FROM `od-cl-odss-conroyri-f75a.nih_exporter.clustered_50k_semantic`
WHERE cluster IN (SELECT cluster FROM top_clusters)
ORDER BY cluster, RAND()
LIMIT 30'

# 3. IC homogeneity analysis
echo ""
echo "🏛️ IC Homogeneity by Cluster:"
bq query --use_legacy_sql=false '
WITH cluster_ic_counts AS (
  SELECT 
    cluster,
    IC_NAME_x as ic_name,
    COUNT(*) as ic_count,
    COUNT(*) OVER (PARTITION BY cluster) as cluster_total
  FROM `od-cl-odss-conroyri-f75a.nih_exporter.clustered_50k_semantic`
  GROUP BY cluster, IC_NAME_x
),
top_ic_per_cluster AS (
  SELECT 
    cluster,
    ic_name,
    ic_count,
    cluster_total,
    ROUND(ic_count / cluster_total, 3) as purity,
    ROW_NUMBER() OVER (PARTITION BY cluster ORDER BY ic_count DESC) as rank
  FROM cluster_ic_counts
)
SELECT 
  cluster,
  cluster_total as total_grants,
  ic_name as dominant_ic,
  ic_count as dominant_ic_count,
  purity as ic_purity
FROM top_ic_per_cluster
WHERE rank = 1
ORDER BY cluster_total DESC
LIMIT 20'

# 4. Temporal analysis
echo ""
echo "📅 Temporal Distribution:"
bq query --use_legacy_sql=false '
WITH cluster_years AS (
  SELECT 
    cluster,
    COUNT(*) as total,
    SUM(CASE WHEN FY_x >= 2020 THEN 1 ELSE 0 END) as recent_2020plus,
    SUM(CASE WHEN FY_x >= 2015 AND FY_x < 2020 THEN 1 ELSE 0 END) as mid_2015_2019,
    SUM(CASE WHEN FY_x < 2015 THEN 1 ELSE 0 END) as older_pre2015
  FROM `od-cl-odss-conroyri-f75a.nih_exporter.clustered_50k_semantic`
  GROUP BY cluster
)
SELECT 
  cluster,
  total,
  recent_2020plus,
  ROUND(recent_2020plus / total, 3) as pct_recent,
  mid_2015_2019,
  older_pre2015
FROM cluster_years
ORDER BY total DESC
LIMIT 10'

echo ""
echo "========================================================================"
echo "ANALYSIS COMPLETE"
echo "========================================================================"
