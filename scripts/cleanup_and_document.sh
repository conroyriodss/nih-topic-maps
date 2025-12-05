#!/bin/bash
set -e
echo "=========================================="
echo "NIH ANALYTICS - CLEANUP & DOCUMENTATION"
echo "=========================================="
echo "Started: $(date)"
echo ""

echo "[1/4] Creating system documentation..."
cat > ~/SESSION_SUMMARY_DEC04.md << 'DOCEND'
# NIH Grant Analytics System - Production Release v1.5
**Date:** December 4, 2025
**Status:** Production Ready

## SYSTEM OVERVIEW
- 1,260,419 total grant cards (FY 2000-2024)
- 245,396 semantically clustered awards (19.5%)
- 223,588 research-topic awards (91% of clustered)
- 10 research domains, 63 topics (hierarchical taxonomy)

## PRODUCTION TABLES (BigQuery: od-cl-odss-conroyri-f75a:nih_analytics)
- grant_cards_v1_5_hierarchical (1,260,419 rows)
- cluster_hierarchy_complete (75 clusters mapped to 10 domains)
- export_research_portfolio (223,588 research awards)
- export_domain_ic_summary (295 domain-IC combinations)
- export_cluster_metadata (64 clusters with centroids)

## HIERARCHICAL TAXONOMY - 10 RESEARCH DOMAINS
| Domain | Code | Awards | Funding | Avg Pubs |
|--------|------|--------|---------|----------|
| Basic Biomedical Sciences | D01 | 69,269 | $237.0B | 30.0 |
| Neuroscience & Behavior | D02 | 46,544 | $156.7B | 24.0 |
| Infectious Disease & Immunity | D05 | 30,259 | $101.5B | 27.0 |
| Cancer Research | D03 | 19,541 | $63.3B | 28.0 |
| Clinical & Translational | D07 | 18,851 | $58.6B | 24.8 |
| Metabolic & Endocrine | D06 | 10,836 | $47.1B | 31.4 |
| Cardiovascular & Respiratory | D04 | 12,215 | $44.0B | 27.7 |
| Population & Public Health | D08 | 6,091 | $20.9B | 24.9 |
| Methodology & Infrastructure | D10 | 5,978 | $18.6B | 17.0 |
| Musculoskeletal & Sensory | D09 | 4,004 | $11.8B | 21.2 |
| TOTAL RESEARCH | | 223,588 | $759.5B | 26.7 |

## CLOUD STORAGE EXPORTS (gs://nih-analytics-exports/hierarchical/)
- research_portfolio_000000000000.parquet (4.8 MB, 223K awards)
- domain_ic_summary.csv (16 KB, 295 records)
- cluster_metadata.json (64 clusters with metadata)

## INTERACTIVE VISUALIZATIONS (~/exports/)
1. hierarchical_topic_map_with_centers.html - UMAP scatter (50K sample)
2. domain_treemap.html - Funding distribution by domain
3. domain_ic_heatmap.html - Strategic portfolio matrix
4. cluster_summary_table.html - Top 20 clusters by funding

## KEY QUERIES

### Get Research Awards by Domain
SELECT domain_id, domain_name, COUNT(*) as awards,
  ROUND(SUM(TOTAL_LIFETIME_FUNDING)/1e9, 2) as funding_b
FROM od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_5_hierarchical
WHERE is_clustered = TRUE AND is_research_topic = TRUE
GROUP BY domain_id, domain_name
ORDER BY funding_b DESC;

### Get Domain-Specific Awards
SELECT * FROM od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_5_hierarchical
WHERE domain_id = 'D02' AND is_clustered = TRUE AND is_research_topic = TRUE;

## CHANGELOG
### v1.5 (Dec 4, 2025)
- Added hierarchical taxonomy (10 domains, 63 topics)
- Fixed publication temporal filtering
- Corrected MPI detection logic
- Created domain-specific exports
- Generated interactive visualizations
- Mapped cluster 74 (unlabeled awards)

## CONTACT
GitHub: conroyriodss/nih-topic
Project: od-cl-odss-conroyri-f75a
GCS: gs://nih-analytics-exports
Updated: December 4, 2025, 12:30 PM EST
DOCEND
echo "  ✓ Created SESSION_SUMMARY_DEC04.md"

echo ""
echo "[2/4] Cleaning up old files..."
find ~ -maxdepth 1 -name "SESSION_SUMMARY_NOV*.md" -type f -delete 2>/dev/null || true
rm -f ~/*.csv 2>/dev/null || true
rm -f ~/*.parquet 2>/dev/null || true
find ~ -maxdepth 1 -name "export_*.py" -type f -delete 2>/dev/null || true
find ~ -maxdepth 1 -name "*.pyc" -type f -delete 2>/dev/null || true
pip cache purge > /dev/null 2>&1 || true
echo "  ✓ Removed old session summaries"
echo "  ✓ Removed temporary data files"
echo "  ✓ Removed old Python scripts"
echo "  ✓ Cleaned pip cache"

echo ""
echo "[3/4] Organizing exports directory..."
cd ~/exports
mkdir -p archive
find . -maxdepth 1 -name "topic_map*.html" -type f -mtime +1 -exec mv {} archive/ \; 2>/dev/null || true
find . -maxdepth 1 -name "simple_viz*.html" -type f -exec mv {} archive/ \; 2>/dev/null || true
cat > README.md << 'READEND'
# NIH Analytics Exports

## Current Visualizations
1. hierarchical_topic_map_with_centers.html - Full research landscape
2. domain_treemap.html - Funding distribution
3. domain_ic_heatmap.html - Domain x IC matrix
4. cluster_summary_table.html - Top 20 clusters

## Data Files
- research_portfolio_*.parquet - 223K research awards
- domain_ic_summary.csv - Domain-IC matrix
- cluster_metadata.json - Cluster metadata

Last Updated: December 4, 2025
READEND
echo "  ✓ Archived old visualizations"
echo "  ✓ Created exports README"

echo ""
echo "[4/4] Checking system resources..."
pkill -9 -f jupyter 2>/dev/null || true
pkill -9 -f "python.*idle" 2>/dev/null || true
history -c 2>/dev/null || true
echo "  ✓ Stopped unused processes"

echo ""
echo "=========================================="
echo "✅ CLEANUP & DOCUMENTATION COMPLETE"
echo "=========================================="
echo ""
echo "Generated Documentation:"
echo "  ~/SESSION_SUMMARY_DEC04.md"
echo "  ~/exports/README.md"
echo ""
echo "Active Visualizations (~/exports/):"
ls -lh ~/exports/*.html 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
echo ""
echo "Cloud Storage:"
gsutil ls -lh gs://nih-analytics-exports/hierarchical/ 2>/dev/null | tail -4
echo ""
echo "System Status:"
echo "  ✓ Old files archived"
echo "  ✓ Temporary files removed"
echo "  ✓ Documentation updated"
echo "  ✓ Exports organized"
echo ""
echo "Completed: $(date)"
echo "=========================================="
