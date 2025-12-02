NIH Topic Maps - K=50 Hybrid Clustering Visualization
======================================================

FILES:
- index.html: Interactive visualization (open in browser)
- clustering_k50_with_umap.csv: Full dataset with UMAP coordinates
- cluster_labels_k50.json: Topic labels for all 50 clusters
- hybrid_lemmatized_results.csv: Clustering quality metrics

METRICS:
- K=50 topics
- Silhouette score: +0.0015 (positive clustering!)
- 12,491 grants from FY 2000-2024
- Method: Hybrid hierarchical (Ward linkage)
- Features: PubMedBERT (50%) + RCDC (15%) + IC (10%) + Terms-TF-IDF (25%)

TO USE:
1. Open index.html in a modern web browser (Chrome, Firefox, Safari)
2. Use filters to explore by IC, topic, fiscal year
3. Search for specific grants
4. Click dots to see grant details
5. Click legend items to filter by topic
6. Zoom and pan the visualization

NEXT STEPS:
- Scale to full 50k sample
- Deploy to GCS for web access
- Refine topic labels with domain expertise
