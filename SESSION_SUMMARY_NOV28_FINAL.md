# Session Summary - November 28, 2025

## Major Accomplishments

### 1. GPU Embedding Generation (Complete)
- PubMedBERT embeddings on PROJECT_TERMS
- 43,320 grants processed on Tesla T4 GPU
- Cost: ~$0.40
- Output: embeddings_project_terms_clustered_k100.parquet

### 2. UMAP Parameter Exploration
Generated 4 UMAP variants:
- tight_clustering: n_neighbors=10, min_dist=0.01
- balanced: n_neighbors=15, min_dist=0.1
- loose_visualization: n_neighbors=40, min_dist=0.15
- very_tight: n_neighbors=8, min_dist=0.01, spread=0.5

### 3. Generic Terms Problem Identified
50 generic terms appear in 16-47% of grants:
- testing (46.8%), goals (44.9%), data (43.1%)
- development (42.6%), research (41.8%)
- These pollute clustering by grouping on grant-speak not science

### 4. Three Clustering Methods Tested

Method 1: Original PubMedBERT K=100
- Silhouette: 0.0391
- Largest cluster: 1,249 (2.9%)
- Issue: Generic catch-all clusters

Method 2: TF-IDF Filtered K=100
- Removed 50 generic terms
- TF-IDF weighting for rare terms
- Largest cluster: 1,296 (3.0%)
- Better labels but similar distribution

Method 3: IC Hierarchical (300 topics)
- First level: 26 ICs
- Second level: 5-20 topics per IC
- Total: 300 IC-specific topics
- Natural NIH organizational structure

### 5. MeSH Scientific Terms Whitelist (In Progress)
- Created 746-term whitelist from MeSH categories
- Categories: Anatomy, Organisms, Diseases, Chemicals, Techniques, Processes
- Filters PROJECT_TERMS to keep only scientific vocabulary
- Running: viz_mesh_filtered.json

## Key Files Created

### Scripts
- scripts/09_compare_umap_params.py
- scripts/10_ic_hierarchical_clustering.py

### Data
- data/mesh/scientific_terms_whitelist.json (746 terms)
- data/processed/viz_umap_*.json (4 UMAP variants)
- data/processed/viz_tfidf_filtered.json
- data/processed/viz_ic_hierarchical.json
- data/processed/viz_mesh_filtered.json (in progress)

### Documentation
- TERM_FILTERING_STRATEGY.md
- UMAP_PARAMETER_GUIDE.md
- QUICK_COMMANDS.md
- SESSION_SUMMARY_NOV28_FINAL.md

### Visualizations
- compare_umap_simple.html (4 UMAP params)
- compare_all_methods.html (3 clustering methods)

## Key Insights

### PROJECT_TERMS Quality
- Pre-2008: Manually assigned by CRISP indexers (higher quality)
- Post-2008: Auto-mined from abstracts (includes generic terms)
- Solution: Filter with MeSH whitelist

### Recommended Approach for Production
1. Use MeSH whitelist to filter PROJECT_TERMS
2. Apply TF-IDF weighting
3. Consider IC-hierarchical for navigation
4. K=150-200 for finer granularity

### Scaling Recommendations
| Approach | Speed | Quality | Best For |
|----------|-------|---------|----------|
| Sample 100K + BERT | Fast | High | Iteration |
| IC Hierarchical | Medium | High | NIH navigation |
| TF-IDF only | Fastest | Medium | Quick analysis |
| BERTopic | Slow | Highest | Production |

## GCS Files

Bucket: gs://od-cl-odss-conroyri-nih-embeddings/sample/

Embeddings:
- embeddings_project_terms_clustered_k100.parquet (217 MB)

Visualizations:
- viz_data_project_terms_k100.json
- viz_umap_tight_clustering.json
- viz_umap_balanced.json
- viz_umap_loose_visualization.json
- viz_umap_very_tight.json
- viz_tfidf_filtered.json
- viz_ic_hierarchical.json
- viz_mesh_filtered.json (pending)

HTML:
- compare_umap_simple.html
- compare_all_methods.html
- project_terms_interactive.html

## Next Steps

1. Review MeSH-filtered results when complete
2. Choose best clustering method
3. Create production visualization
4. Scale to larger sample (100K-200K)
5. Consider BERTopic for final version

## Commands for Next Session

Check MeSH results:
ls -lh data/processed/viz_mesh_filtered.json

View comparisons:
https://storage.googleapis.com/od-cl-odss-conroyri-nih-embeddings/sample/compare_all_methods.html

Git status:
git status && git log --oneline -5
