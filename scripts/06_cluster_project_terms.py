#!/usr/bin/env python3
"""
Cluster PROJECT_TERMS embeddings using K-means
Using K=100 based on Nov 26 optimization results
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
import argparse
import time
from datetime import datetime
import json
import subprocess
import os

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('--k', type=int, default=100, help='Number of clusters (default: 100 based on optimization)')
parser.add_argument('--random-state', type=int, default=42, help='Random state for reproducibility')
args = parser.parse_args()

K = args.k
RANDOM_STATE = args.random_state

print("\n" + "="*70)
print(f"K-Means Clustering - PROJECT_TERMS Embeddings")
print(f"K = {K} clusters")
print(f"Based on Nov 26 optimization: K=100 showed best balance")
print("="*70 + "\n")

start_time = time.time()

# Download embeddings from GCS
print("Downloading PROJECT_TERMS embeddings from GCS...")
os.makedirs('data/processed', exist_ok=True)
subprocess.run([
    'gsutil', 'cp',
    'gs://od-cl-odss-conroyri-nih-embeddings/sample/embeddings_project_terms_50k.parquet',
    'data/processed/'
], check=True)

# Load embeddings
print("Loading embeddings...")
df = pd.read_parquet('data/processed/embeddings_project_terms_50k.parquet')
print(f"✓ Loaded {len(df):,} grants with embeddings\n")

# Extract embedding vectors
embeddings = np.array(df['embedding'].tolist())
print(f"Embedding shape: {embeddings.shape}")

# Perform K-means clustering
print(f"\nClustering with K={K}...")
kmeans = KMeans(
    n_clusters=K,
    random_state=RANDOM_STATE,
    n_init=10,
    max_iter=300,
    verbose=1
)
labels = kmeans.fit_predict(embeddings)

# Calculate quality metrics
print("\nCalculating quality metrics...")
silhouette = silhouette_score(embeddings, labels, sample_size=10000)
davies_bouldin = davies_bouldin_score(embeddings, labels)
calinski = calinski_harabasz_score(embeddings, labels)

elapsed = time.time() - start_time

print("\n" + "="*70)
print("Clustering Results")
print("="*70)
print(f"K clusters: {K}")
print(f"Silhouette score: {silhouette:.4f} (Nov 26 full-text K=100: 0.018)")
print(f"Davies-Bouldin index: {davies_bouldin:.4f} (lower is better)")
print(f"Calinski-Harabasz score: {calinski:.2f} (Nov 26 full-text K=100: 287.7)")
print(f"Time elapsed: {elapsed/60:.1f} minutes")

# Add cluster labels to dataframe
df['cluster'] = labels

# Analyze cluster sizes
cluster_sizes = pd.Series(labels).value_counts().sort_index()
print("\n" + "="*70)
print("Cluster Size Distribution")
print("="*70)
print(f"Mean size: {cluster_sizes.mean():.1f}")
print(f"Median size: {cluster_sizes.median():.1f}")
print(f"Min size: {cluster_sizes.min()}")
print(f"Max size: {cluster_sizes.max()}")
print(f"\nSmallest clusters (size < 100):")
small_clusters = cluster_sizes[cluster_sizes < 100]
if len(small_clusters) > 0:
    print(small_clusters.to_string())
else:
    print("None")

# Analyze IC diversity per cluster
print("\n" + "="*70)
print("Cluster IC Diversity")
print("="*70)
ic_diversity = df.groupby('cluster')['IC_NAME'].nunique()
print(f"Mean ICs per cluster: {ic_diversity.mean():.1f}")
print(f"Max ICs in a cluster: {ic_diversity.max()}")
print(f"\nClusters with >25 ICs (potentially too generic):")
diverse_clusters = ic_diversity[ic_diversity > 25].sort_values(ascending=False)
if len(diverse_clusters) > 0:
    print(diverse_clusters.head(10).to_string())
else:
    print("None - Good! PROJECT_TERMS provide better focus than full text")

# Compare with Nov 26 full-text results
print("\n" + "="*70)
print("Comparison: PROJECT_TERMS vs Full Text (Nov 26)")
print("="*70)
print(f"                          PROJECT_TERMS    Full Text (Nov 26)")
print(f"Silhouette score:         {silhouette:8.4f}         0.0180")
print(f"Min cluster size:         {cluster_sizes.min():8d}            50")
print(f"Mean ICs per cluster:     {ic_diversity.mean():8.1f}          24.2")
print(f"Generic clusters (>25 IC):{len(diverse_clusters):8d}            14")

# Save results
print("\n" + "="*70)
print("Saving Results")
print("="*70)

# Save clustered data
output_file = f'data/processed/embeddings_project_terms_clustered_k{K}.parquet'
df.to_parquet(output_file, compression='snappy')
print(f"✓ Saved clustered data: {output_file}")

# Upload to GCS
subprocess.run([
    'gsutil', 'cp', output_file,
    'gs://od-cl-odss-conroyri-nih-embeddings/sample/'
], check=True)
print(f"✓ Uploaded to GCS")

# Save cluster centers
centers_file = f'data/processed/cluster_centers_project_terms_k{K}.npy'
np.save(centers_file, kmeans.cluster_centers_)
subprocess.run([
    'gsutil', 'cp', centers_file,
    'gs://od-cl-odss-conroyri-nih-embeddings/sample/'
], check=True)
print(f"✓ Saved cluster centers")

# Create summary report
summary = {
    'timestamp': datetime.now().isoformat(),
    'k': K,
    'n_samples': len(df),
    'embedding_source': 'PROJECT_TERMS',
    'comparison_to_full_text': {
        'full_text_silhouette': 0.018,
        'project_terms_silhouette': float(silhouette),
        'improvement': 'TBD after completion'
    },
    'metrics': {
        'silhouette_score': float(silhouette),
        'davies_bouldin_index': float(davies_bouldin),
        'calinski_harabasz_score': float(calinski)
    },
    'cluster_sizes': {
        'mean': float(cluster_sizes.mean()),
        'median': float(cluster_sizes.median()),
        'min': int(cluster_sizes.min()),
        'max': int(cluster_sizes.max()),
        'small_clusters': len(small_clusters)
    },
    'ic_diversity': {
        'mean_ics_per_cluster': float(ic_diversity.mean()),
        'max_ics_per_cluster': int(ic_diversity.max()),
        'generic_clusters': len(diverse_clusters)
    },
    'time_minutes': elapsed / 60
}

summary_file = f'data/processed/clustering_summary_project_terms_k{K}.json'
with open(summary_file, 'w') as f:
    json.dump(summary, f, indent=2)

subprocess.run([
    'gsutil', 'cp', summary_file,
    'gs://od-cl-odss-conroyri-nih-embeddings/sample/'
], check=True)
print(f"✓ Saved summary report")

print("\n" + "="*70)
print("CLUSTERING COMPLETE")
print("="*70)
print(f"\nNext steps:")
print(f"1. Generate UMAP visualization:")
print(f"   python3 scripts/07_create_umap_project_terms.py --k {K}")
print(f"\n2. Compare with full-text clustering:")
print(f"   python3 scripts/compare_clustering_methods.py")
