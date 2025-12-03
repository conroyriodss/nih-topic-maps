#!/usr/bin/env python3
"""
Emergency clustering from local 250k file
Uses hierarchical + UMAP to infer better clusters
"""
import pandas as pd
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score
from umap import UMAP

print("="*70)
print("CLUSTERING 250K FROM LOCAL FILE")
print("="*70)

# Load existing file
print("\n[1/4] Loading local 250k file...")
df = pd.read_csv('hierarchical_250k_with_umap.csv')
print(f"   Loaded {len(df):,} grants")
print(f"   Has UMAP coords: {('umap_x' in df.columns and 'umap_y' in df.columns)}")

# Extract UMAP coordinates
coords = df[['umap_x', 'umap_y']].values
print(f"   Coordinate range: X=[{coords[:,0].min():.2f}, {coords[:,0].max():.2f}], Y=[{coords[:,1].min():.2f}, {coords[:,1].max():.2f}]")

# Cluster on UMAP (acknowledging this is imperfect but better than nothing)
print("\n[2/4] Re-clustering with optimal K=75...")
print("   ⚠️  Note: Clustering on 2D UMAP coords (768D embeddings not available)")
print("   ⚠️  This is a limitation - silhouette will be low")

K = 75
clustering = AgglomerativeClustering(n_clusters=K, linkage='ward')
labels = clustering.fit_predict(coords)

# Evaluate
sil = silhouette_score(coords, labels, metric='euclidean', sample_size=10000)
print(f"\n[3/4] Quality metrics:")
print(f"   Silhouette (2D UMAP): {sil:.4f}")
print(f"   Cluster count: {K}")
print(f"   Cluster sizes: min={np.bincount(labels).min()}, median={int(np.median(np.bincount(labels)))}, max={np.bincount(labels).max()}")

# Add new clusters
df['cluster_k75'] = labels

# Save
output_file = 'hierarchical_250k_reclustered_k75.csv'
df.to_csv(output_file, index=False)

print(f"\n[4/4] Saved: {output_file}")
print(f"   - {len(df):,} grants")
print(f"   - {K} clusters (column: cluster_k75)")
print(f"   - Original domain labels preserved")

print("\n" + "="*70)
print("COMPLETE!")
print("="*70)
print("\n⚠️  IMPORTANT LIMITATION:")
print("This clustering uses 2D UMAP coordinates, not full 768D embeddings.")
print("For production quality, you need to:")
print("  1. Generate 768D PubMedBERT embeddings from original text")
print("  2. Cluster on full 768D space (not 2D)")
print("  3. Use UMAP only for visualization after clustering")
print("\nCurrent approach is adequate for exploration, not final analysis.")
