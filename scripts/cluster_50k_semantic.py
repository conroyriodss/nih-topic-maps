import pandas as pd
import numpy as np
from sklearn.cluster import AgglomerativeClustering

# Load
df_sample = pd.read_parquet('sample_50k_stratified.parquet')
df_embeddings = pd.read_parquet('embeddings_50k_sample.parquet')
df = df_sample.merge(df_embeddings, on='APPLICATION_ID', how='inner')

# Extract embeddings
embeddings = np.vstack(df['embedding'].values)

# Cluster on FULL embeddings (not UMAP!)
print(f"Clustering {len(df):,} grants with K=75...")
clustering = AgglomerativeClustering(n_clusters=75, linkage='ward')
labels = clustering.fit_predict(embeddings)

df['cluster'] = labels

# Save
df.to_parquet('grants_50k_SEMANTIC_clustered.parquet', index=False)
print("✓ Saved grants_50k_SEMANTIC_clustered.parquet")

# Stats
print(f"\nCluster sizes: {np.bincount(labels).min()} - {np.bincount(labels).max()}")
print(f"Median size: {np.median(np.bincount(labels)):.0f}")
