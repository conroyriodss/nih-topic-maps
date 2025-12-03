# NIH Topic Mapping - Session Summary
December 3, 2025

## Completed Work

### 1. Transaction-Level Clustering
- 250K transactions clustered into 75 topics
- Silhouette: 0.347
- Visualizations: 4 static + 1 interactive

### 2. Award-Level Architecture Analysis
- Identified grant_scorecard_v2 as proper award level
- 103K unique awards analyzed
- Proved award-level superior to transaction-level

### 3. Hierarchical Clustering System
- 3-level hierarchy: 15 domains → 60 topics → 180 subtopics
- Interactive map with level switching
- Reduced outliers through hierarchical structure

## Key Files

### Data Files
- awards_hierarchical_clustered.csv (250K records with 3-level hierarchy)
- awards_from_transactions_clustered.csv (award-level with UMAP coords)
- hierarchical_250k_clustered_k75.csv (original transaction clustering)

### Visualizations
- award_map_hierarchical.html (interactive with level switching)
- award_map_from_transactions.html (single-level interactive)
- nih_250k_labeled_map.png (transaction-level static)

### Documentation
- SESSION_FINAL_DEC3.md (session notes)
- FINAL_SESSION_REPORT_DEC3.md (detailed report)

## Architecture Decision

Award-level clustering is superior for portfolio analysis:
- No inflation from multi-year funding
- Better represents research programs
- Enables PI/institution analysis
- Cleaner for strategic planning

Transaction-level still useful for:
- Annual budget reports
- Fiscal year spending analysis
- Payment tracking

## Next Steps

1. True award aggregation using CORE_PROJECT_NUM
2. Generate better embeddings (PubMedBERT on GPU)
3. Scale to full 560K awards in grant_scorecard_v2
4. Compare to RCDC categories
5. Deploy interactive dashboard

## Technical Stack

- Embeddings: TF-IDF + SVD (100D) or PubMedBERT (768D)
- Dimensionality Reduction: UMAP (n_neighbors=50, min_dist=0.0)
- Clustering: K-means hierarchical (15→60→180)
- Visualization: Plotly interactive maps
- Platform: Google Cloud BigQuery + Cloud Shell

## Contact

Richard Conroy
conroyri@nih.gov
