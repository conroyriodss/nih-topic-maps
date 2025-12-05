# NIH Topic Maps - Session Summary
## December 1, 2025

### COMPLETED TODAY

1. Hierarchical Clustering (5 x 13 x 24)
   - Created 3-level hierarchy: 5 domains, 13 topics, 24 subtopics
   - 43,320 grants (FY 2000-2024) clustered
   - Saved: viz_data_3level_hierarchy.json

2. Tighter UMAP Layout
   - Re-ran UMAP with tighter parameters (n_neighbors=5, min_dist=0.05)
   - Reduced layout span by 18%
   - Saved: viz_data_3level_hierarchy_tight.json, domain_regions.json

3. Interactive Visualization
   - Canvas-based visualization with D3.js
   - Domain/Topic/Subtopic views, filters, tooltips
   - Working locally at http://localhost:8000
   - Saved: viz_3level_hierarchy.html

4. Uploaded to GCS
   - viz_data_3level_hierarchy_tight.json
   - domain_regions.json

### PICK UP TOMORROW

Phase 1: Expand Historical Data (1990-1999)

BigQuery has ~554,000 grants from 1990-1999

Next Steps:
1. Extract 1990-1999 grants from BigQuery
2. Sample 25-30k grants
3. Generate embeddings
4. Combine with existing 43k -> ~70k total
5. Re-cluster and re-run UMAP
6. Update visualization

Goal: More filled-in spider web appearance

### START TOMORROW

cd ~/nih-topic-maps
python3 -m http.server 8000 &

bq query --use_legacy_sql=false --format=json --max_rows=600000 'SELECT APPLICATION_ID, PROJECT_TITLE, PROJECT_TERMS, FY, IC_NAME, TOTAL_COST FROM od-cl-odss-conroyri-f75a.nih_exporter.projects WHERE FY BETWEEN 1990 AND 1999 AND PROJECT_TITLE IS NOT NULL' > grants_1990_1999_full.json
