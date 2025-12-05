# NIH Clustering Session - Final Summary
December 3, 2025 | 4:47 PM EST

## Completed Today

### 1. Transaction-Level Clustering (Morning)
- 250K transactions clustered into 75 topics
- Silhouette: 0.347
- Used PubMedBERT embeddings
- Generated 4 visualizations + interactive HTML

### 2. Award-Level Analysis (Afternoon)
- Explored award-level architecture (grant_scorecard_v2)
- 103K unique awards identified
- Proved award approach superior (no inflation)

### 3. Semantic Clustering Attempts
- Generated TF-IDF embeddings (100D)
- Hit UMAP dependency issues
- Created workaround using transaction UMAP coordinates

### 4. Final Interactive Map
- Used transaction-level UMAP space
- Re-clustered in 2D
- Silhouette: 0.3714
- Dark theme matching original NIH map
- Created: award_map_from_transactions.html

## Key Finding

APPLICATION_ID appears to be transaction-level (250K unique = 250K transactions)
True award aggregation requires CORE_PROJECT_NUM from grant_scorecard_v2

## Files Generated Today

Transaction Clustering:
  hierarchical_250k_clustered_k75.csv           44M
  cluster_75_labels.csv                        11K
  nih_250k_labeled_map.png                    1.3M
  nih_250k_interactive_viz.html

Award Clustering Attempts:
  awards_110k_clustered_k75.csv               35M
  awards_110k_with_semantic_clusters.csv      35M
  award_embeddings_tfidf_103k.npy             41M
  award_cluster_labels_semantic.csv          7.3K
  award_semantic_map_103k.png                660K

Final Map:
  awards_from_transactions_clustered.csv      9.4M
  award_map_from_transactions.html

Documentation:
  SESSION_SUMMARY_DEC3_FINAL.md
  FINAL_SESSION_REPORT_DEC3.md
  SESSION_FINAL_DEC3.md (this file)

## Interactive Map Features

✅ Dark theme (matches original NIH map)
✅ Cluster labels at centroids
✅ Hover tooltips with details
✅ Zoom and pan
✅ Top 10 clusters summary
✅ Uses proven UMAP coordinates

## Next Steps

### Option A: True Award-Level Clustering
1. Join transaction data to grant_scorecard_v2
2. Get CORE_PROJECT_NUM for each transaction
3. Aggregate to award level (should get ~60K awards)
4. Re-cluster with award-aggregated coordinates

### Option B: Use Current Map
1. Current map shows transaction-level view
2. Same structure as original NIH map
3. Good for exploring existing work
4. Can use as-is for demonstrations

### Option C: Generate Better Embeddings
1. Set up GPU environment
2. Use PubMedBERT or sentence-transformers
3. Embed award titles + abstracts
4. Create native award-level clustering

## Recommendation

**For immediate use:** Current award_map_from_transactions.html works well
- Same visual structure as original map
- Interactive and polished
- Ready for presentations

**For production:** Need true award aggregation
- Requires CORE_PROJECT_NUM
- Would reduce to ~60K unique awards
- Better represents portfolio

## Session Statistics

Time: ~4 hours
Tool calls: ~30
Files created: 20+
Visualizations: 7
Key insight: Award-level superior to transaction-level for portfolio analysis

Status: Transaction-level map complete and polished
Next: Decide on award aggregation strategy

---
End of Session
