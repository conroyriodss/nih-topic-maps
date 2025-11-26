#!/usr/bin/env python3
"""
Find optimal number of clusters for NIH grants
"""
import pandas as pd
import numpy as np
from sklearn.metrics import silhouette_score, calinski_harabasz_score
from sklearn.cluster import KMeans
import json

# Load embeddings
print("Loading embeddings...")
df = pd.read_parquet('gs://od-cl-odss-conroyri-nih-embeddings/sample/embeddings_pubmedbert_50k.parquet')
embeddings = np.stack(df['embedding'].values)

print(f"Embeddings shape: {embeddings.shape}")

# Test different K values
k_values = [50, 74, 100, 125, 150, 175, 200]
results = []

for k in k_values:
    print(f"\nTesting K={k}...")
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embeddings)
    
    silhouette = silhouette_score(embeddings, labels, sample_size=10000)
    calinski = calinski_harabasz_score(embeddings, labels)
    
    # Calculate cluster size distribution
    unique, counts = np.unique(labels, return_counts=True)
    min_size = counts.min()
    max_size = counts.max()
    mean_size = counts.mean()
    
    results.append({
        'k': k,
        'silhouette': silhouette,
        'calinski_harabasz': calinski,
        'min_cluster_size': int(min_size),
        'max_cluster_size': int(max_size),
        'mean_cluster_size': float(mean_size)
    })
    
    print(f"  Silhouette: {silhouette:.3f}")
    print(f"  Calinski-Harabasz: {calinski:.1f}")
    print(f"  Cluster sizes: {min_size}-{max_size} (mean={mean_size:.0f})")

# Save results
with open('clustering_evaluation.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n=== Results Summary ===")
for r in results:
    print(f"K={r['k']:3d}: Silhouette={r['silhouette']:.3f}, "
          f"CH={r['calinski_harabasz']:8.1f}, "
          f"Sizes={r['min_cluster_size']}-{r['max_cluster_size']}")

# Recommend best K
best_k = max(results, key=lambda x: x['silhouette'])
print(f"\nRecommended K={best_k['k']} (highest silhouette score)")
