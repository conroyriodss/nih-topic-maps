#!/usr/bin/env python3
"""
Simple clustering from existing 250k UMAP coordinates
No UMAP import needed - coordinates already exist
"""
import pandas as pd
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score

print("="*70)
print("CLUSTERING 250K FROM EXISTING UMAP COORDINATES")
print("="*70)

# Load existing file with UMAP coords
print("\n[1/4] Loading hierarchical_250k_with_umap.csv...")
df = pd.read_csv('hierarchical_250k_with_umap.csv')
print(f"   Loaded {len(df):,} grants")
print(f"   Columns: {df.columns.tolist()}")

# Extract existing UMAP coordinates
if 'umap_x' not in df.columns or 'umap_y' not in df.columns:
    print("ERROR: UMAP coordinates not found in file!")
    exit(1)

coords = df[['umap_x', 'umap_y']].values
print(f"   Coordinate range: X=[{coords[:,0].min():.2f}, {coords[:,0].max():.2f}]")
print(f"                      Y=[{coords[:,1].min():.2f}, {coords[:,1].max():.2f}]")

# Cluster with optimal K=75 from your 50k experiments
print("\n[2/4] Clustering with K=75 (Ward linkage)...")
K = 75
clustering = AgglomerativeClustering(n_clusters=K, linkage='ward')
labels = clustering.fit_predict(coords)

# Evaluate
print("\n[3/4] Evaluating cluster quality...")
sil = silhouette_score(coords, labels, metric='euclidean', sample_size=10000)
cluster_sizes = np.bincount(labels)

print(f"   Silhouette (2D UMAP): {sil:.4f}")
print(f"   Cluster count: {K}")
print(f"   Cluster sizes:")
print(f"     Min: {cluster_sizes.min()}")
print(f"     Median: {int(np.median(cluster_sizes))}")
print(f"     Mean: {cluster_sizes.mean():.1f}")
print(f"     Max: {cluster_sizes.max()}")
print(f"   Tiny clusters (<100): {(cluster_sizes < 100).sum()}")

# Add new cluster assignments
df['cluster_k75'] = labels

# Save
output_file = 'hierarchical_250k_clustered_k75.csv'
print(f"\n[4/4] Saving {output_file}...")
df.to_csv(output_file, index=False)

print(f"\n✅ SUCCESS!")
print(f"   File: {output_file}")
print(f"   Grants: {len(df):,}")
print(f"   Clusters: {K}")

print("\n" + "="*70)
print("ANALYSIS SUMMARY")
print("="*70)
print(f"✅ {len(df):,} grants clustered into {K} clusters")
print(f"✅ Average cluster size: {cluster_sizes.mean():.0f} grants")
print(f"✅ Consistent with your 50k methodology (K=75, Ward)")
print(f"\n⚠️  KNOWN LIMITATION:")
print(f"   Clustering used 2D UMAP coordinates (not full 768D embeddings)")
print(f"   Silhouette score {sil:.4f} is expected for 2D space")
print(f"   For production: need to cluster on 768D embeddings first")
print(f"\n📊 NEXT STEPS:")
print(f"   1. Visualize: python3 create-viz-250k-complete.py")
print(f"   2. Analyze clusters: python3 scripts/analyze_cluster_quality.py")
print(f"   3. For production: Generate 768D embeddings and re-cluster")

print("\n" + "="*70)
