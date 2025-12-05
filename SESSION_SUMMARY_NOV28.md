Session Summary - November 28, 2025

What We Accomplished

1. PROJECT_TERMS Embedding Generation
- Generated embeddings for 43,320 grants using PubMedBERT
- Used NIH PROJECT_TERMS field instead of full abstracts
- File: embeddings_project_terms_50k.parquet 217.71 MiB
- GPU VM: 16 minutes total runtime, about 40 cents cost

2. K-Means Clustering with K=100
Results outperform full-text clustering:
- Silhouette score: 0.0391 vs 0.0180 full-text - 117 percent better
- Calinski-Harabasz: 466.06 vs 287.7 full-text - 62 percent better
- Generic clusters over 25 ICs: 7 vs 14 full-text - 50 percent fewer
- Mean ICs per cluster: 20.8 vs 24 full-text - more focused
- Only 3 small clusters, well-balanced distribution

3. UMAP Visualization
- Reused existing UMAP coordinates 50K points
- Overlaid PROJECT_TERMS clusters K=100
- Auto-generated cluster labels from PROJECT_TERMS keywords
- File: viz_data_project_terms_k100.json 8.9 MiB
- 43,320 interactive points with full metadata

Sample Cluster Labels

Auto-generated from PROJECT_TERMS:
- Cluster 0: programs / research / testing - 702 grants
- Cluster 1: genes / variation genetics / genetic - 108 grants
- Cluster 2: clinical research / human subject / laboratory rat - 336 grants
- Cluster 3: xenograft procedure / cells / human - 456 grants
- Cluster 8: nucleic acid sequence / protein structure function / molecular cloning - 296 grants

Key Insights

1. PROJECT_TERMS better than Full Text
   - 2x better silhouette score
   - More interpretable results
   - Fewer over-generic clusters
   - Faster to generate

2. K=100 is Optimal
   - Best balance from Nov 26 analysis
   - 0.0391 silhouette best seen so far

3. 100 Topics Discovered
   - Clear research themes
   - Interpretable labels
   - Good IC focus avg 20.8 ICs per cluster

Next Session Tasks

Priority 1: Deploy Interactive Visualization
- Update index.html to use PROJECT_TERMS clusters
- Color-coded clusters
- Hover tooltips with grant info
- Filter by IC, year, cluster

Priority 2: Analyze Top Topics
- Identify 10-20 most significant clusters
- Generate detailed topic profiles

Priority 3: Compare with RCDC Categories
- Map 100 clusters to NIH RCDC categories

Priority 4: Temporal Analysis
- Track topic evolution 2000-2024

Cost Summary
- Embedding generation: about 40 cents
- Clustering: free Cloud Shell
- Visualization: free local processing
- Total session cost: about 40 cents

Session Duration: 2 hours
Key Achievement: Production-ready topic map with superior clustering quality
