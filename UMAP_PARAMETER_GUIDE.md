UMAP and Clustering Best Practices for Biomedical Research

NIH Maps Approach
- Clustering: K=150 topics
- Optimization: Custom UMAP parameters for visual cluster separation
- Goal: Interactive exploration of biomedical research

UMAP Key Parameters

n_neighbors (Default: 15)
- Controls balance between LOCAL and GLOBAL structure
- Low 5-10: Focus on local clusters
- Default 15: Good balance
- High 50-200: Global structure emphasis
- Recommendation: 15-30 for biomedical

min_dist (Default: 0.1)
- Controls tightness of clusters
- 0.0: Points pack tightly
- 0.1: Balanced spacing (DEFAULT)
- 0.5-1.0: Very separated
- Our issue: Need 0.05 to pull outliers closer

metric (Default: euclidean)
- cosine: BEST for embeddings semantic similarity
- euclidean: General data
- Recommendation: cosine for embeddings

spread (Default: 1.0)
- Width of embedding space
- 0.5-1.0: Compact
- 1.5-2.0: Dispersed
- Recommendation: 0.8-1.2

Current Problem
- Outliers distributed across map
- Not clearly assigned to nearest clusters
- K=100 may be too many clusters

Solutions

Option 1: More Aggressive Outlier Pulling
- min_dist=0.01 (tighter)
- spread=0.5 (more compact)

Option 2: Separate Visualization UMAP (RECOMMENDED)
- First UMAP tight for clustering
  n_neighbors=10, min_dist=0.01
- Apply K-means K=100
- Second UMAP spread for visualization
  n_neighbors=40, min_dist=0.15
- Use clusters from tight, coordinates from visualization

Option 3: Post-process Outliers
- After clustering, reassign far points to nearest cluster

Option 4: Increase K
- K=150 like NIH Maps instead of K=100

Recommendation: Option 2
1. Tight UMAP for clustering
2. Visualization UMAP with good separation
3. Result: Tight meaningful clusters with good visual spread
