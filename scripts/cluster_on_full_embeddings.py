#!/usr/bin/env python3
import pandas as pd
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score, calinski_harabasz_score

print("Clustering on Full 768D Embeddings (NOT UMAP)")

# Load embeddings - UPDATE THIS PATH
embedding_file = "embeddings_50k_pubmedbert.parquet"  # or your actual file
df = pd.read_parquet(embedding_file)

print(f"Loaded {len(df):,} grants with embeddings")

# Extract embeddings
if isinstance(df['embedding'].iloc[0], str):
    embeddings = np.vstack(df['embedding'].apply(eval).values)
else:
    embeddings = np.vstack(df['embedding'].values)

print(f"Embedding shape: {embeddings.shape}")

# Cluster on FULL embeddings
K = 50
print(f"\nClustering with K={K} on full {embeddings.shape[1]}D space...")

clustering = AgglomerativeClustering(
    n_clusters=K,
    linkage='ward',
    metric='euclidean'
)
labels = clustering.fit_predict(embeddings)

# Evaluate
sil = silhouette_score(embeddings, labels, metric='cosine', sample_size=10000)
ch = calinski_harabasz_score(embeddings, labels)

print(f"\nResults:")
print(f"  Silhouette (cosine): {sil:+.4f}")
print(f"  Calinski-Harabasz: {ch:.2f}")
print(f"  Cluster sizes: {np.bincount(labels).min()} - {np.bincount(labels).max()}")

# Save
df['cluster'] = labels
df.to_parquet('hierarchical_50k_FULLEMBEDDINGS_clustered.parquet', index=False)
print(f"\n✓ Saved: hierarchical_50k_FULLEMBEDDINGS_clustered.parquet")
