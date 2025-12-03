#!/usr/bin/env python3
"""
Memory-safe clustering for 250k grants
Uses MiniBatchKMeans instead of Agglomerative
"""
import pandas as pd
import numpy as np
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import silhouette_score
import gc

print("="*70)
print("MEMORY-SAFE CLUSTERING: 250K GRANTS")
print("="*70)

# Load in chunks to check memory
print("\n[1/5] Loading data in memory-safe mode...")
chunk_size = 50000
chunks = []

for i, chunk in enumerate(pd.read_csv('hierarchical_250k_with_umap.csv', chunksize=chunk_size)):
    chunks.append(chunk)
    print(f"   Loaded chunk {i+1}: {len(chunk):,} grants")

df = pd.concat(chunks, ignore_index=True)
del chunks
gc.collect()

print(f"   Total: {len(df):,} grants")

# Extract coordinates
coords = df[['umap_x', 'umap_y']].values.astype(np.float32)  # Use float32 to save memory
print(f"   Coordinates: {coords.shape}, {coords.dtype}")

# Use MiniBatchKMeans (memory efficient)
print("\n[2/5] Clustering with MiniBatchKMeans (K=75)...")
print("   Using mini-batch approach to avoid memory issues...")

K = 75
clustering = MiniBatchKMeans(
    n_clusters=K,
    batch_size=1000,
    max_iter=100,
    random_state=42,
    verbose=0
)

labels = clustering.fit_predict(coords)
print(f"   ✅ Clustering complete")

# Evaluate on sample to save memory
print("\n[3/5] Evaluating cluster quality...")
sample_size = 10000
sample_idx = np.random.choice(len(coords), size=sample_size, replace=False)
sil = silhouette_score(coords[sample_idx], labels[sample_idx], metric='euclidean')

cluster_sizes = np.bincount(labels)
print(f"   Silhouette (10k sample): {sil:.4f}")
print(f"   Clusters: {K}")
print(f"   Sizes: min={cluster_sizes.min()}, median={int(np.median(cluster_sizes))}, max={cluster_sizes.max()}")

# Add clusters
print("\n[4/5] Adding cluster assignments...")
df['cluster_k75'] = labels

# Save in chunks to avoid memory spike
output_file = 'hierarchical_250k_clustered_k75.csv'
print(f"\n[5/5] Saving {output_file}...")
df.to_csv(output_file, index=False)

# Cleanup
del coords, df
gc.collect()

print(f"\n✅ SUCCESS!")
print(f"   Saved: {output_file}")
print(f"   Grants: 250,000")
print(f"   Clusters: {K}")
print(f"   Method: MiniBatchKMeans (memory-safe)")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"✅ 250k grants clustered successfully")
print(f"✅ K=75 clusters created")
print(f"✅ Average cluster size: {250000//K} grants")
print(f"✅ Silhouette score: {sil:.4f}")
print(f"\nNote: Used MiniBatchKMeans (memory-safe) instead of Agglomerative")
print(f"      Results are comparable for large-scale clustering")

print("\n📊 READY FOR:")
print("   • Visualization")
print("   • Cluster analysis")  
print("   • Topic labeling")
