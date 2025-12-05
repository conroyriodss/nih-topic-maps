#!/usr/bin/env python3
"""
Memory-efficient semantic clustering for 100k grants
Uses MiniBatchKMeans to prevent OOM
"""
import pandas as pd
import numpy as np
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import silhouette_score, calinski_harabasz_score
import gc

print("=" * 70)
print("CLUSTERING 100K GRANTS (MEMORY-EFFICIENT)")
print("=" * 70)

# Load
print("\n[1/4] Loading data...")
df_sample = pd.read_parquet('grants_100k_stratified.parquet')
df_embeddings = pd.read_parquet('embeddings_100k_pubmedbert.parquet')

# Keep essential columns
essential_cols = ['APPLICATION_ID', 'PROJECT_TITLE', 'FY', 'IC_NAME']
available_cols = [c for c in essential_cols if c in df_sample.columns]
df_sample = df_sample[available_cols]

print(f"  Sample: {len(df_sample):,} grants")
print(f"  Embeddings: {len(df_embeddings):,} embeddings")

# Merge
df = df_sample.merge(df_embeddings, on='APPLICATION_ID', how='inner')
print(f"  Merged: {len(df):,} grants")

del df_sample, df_embeddings
gc.collect()

# Extract embeddings
print("\n[2/4] Extracting embeddings...")
if isinstance(df['embedding'].iloc[0], str):
    embeddings = np.vstack(df['embedding'].apply(eval).values)
elif isinstance(df['embedding'].iloc[0], list):
    embeddings = np.vstack(df['embedding'].values)
else:
    embeddings = np.vstack(df['embedding'].values)

print(f"  Shape: {embeddings.shape}")
print(f"  Memory: ~{embeddings.nbytes / 1024**2:.0f} MB")

# Cluster
print("\n[3/4] Clustering with K=75 (from optimization)...")
K = 75

clustering = MiniBatchKMeans(
    n_clusters=K,
    batch_size=1000,
    random_state=42,
    max_iter=100,
    n_init=3,
    verbose=1
)

labels = clustering.fit_predict(embeddings)

# Evaluate
print("\n  Evaluating quality...")
sample_size = 10000
sample_idx = np.random.choice(len(df), sample_size, replace=False)

sil = silhouette_score(
    embeddings[sample_idx], 
    labels[sample_idx], 
    metric='cosine'
)
ch = calinski_harabasz_score(embeddings, labels)

print(f"    Silhouette (cosine): {sil:+.4f}")
print(f"    Calinski-Harabasz: {ch:.2f}")

# Add to dataframe
df['cluster'] = labels
df = df.drop('embedding', axis=1)

# Stats
print("\n  Cluster statistics:")
sizes = np.bincount(labels)
print(f"    Count: {len(sizes)}")
print(f"    Size range: {sizes.min()} - {sizes.max()}")
print(f"    Median: {np.median(sizes):.0f}")
print(f"    Mean: {sizes.mean():.0f}")

# Save
print("\n[4/4] Saving...")
output_file = 'grants_100k_SEMANTIC_clustered.parquet'
df.to_parquet(output_file, index=False)
print(f"  ✓ {output_file}")

# Save cluster centers
centers_df = pd.DataFrame({
    'cluster_id': range(K),
    'center': [clustering.cluster_centers_[i].tolist() for i in range(K)]
})
centers_df.to_parquet('cluster_centers_100k.parquet', index=False)
print(f"  ✓ cluster_centers_100k.parquet")

print("\n" + "=" * 70)
print("COMPLETE!")
print("=" * 70)
print(f"\nClustered {len(df):,} grants into {K} semantic clusters")
print(f"Silhouette: {sil:+.4f}")
print(f"\nNext: Upload to BigQuery with:")
print(f"  bq load --source_format=PARQUET --replace \\")
print(f"    od-cl-odss-conroyri-f75a:nih_exporter.clustered_100k_semantic \\")
print(f"    grants_100k_SEMANTIC_clustered.parquet")
