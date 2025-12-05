#!/usr/bin/env python3
"""
Add UMAP coordinates - avoiding torch dependencies
"""
import pandas as pd
import numpy as np
import sys

# Import only basic UMAP, not parametric version
import umap.umap_ as umap

print("=" * 80)
print("ADDING UMAP COORDINATES TO 50K DATASET")
print("=" * 80)

# Load clustered data
print("\n[1/4] Loading clustered data...")
df = pd.read_csv('hierarchical_50k_clustered.csv')
print(f"  {len(df):,} clustered grants")

# Load embeddings
print("\n[2/4] Loading embeddings...")
emb_df = pd.read_parquet('embeddings_50k_sample.parquet')
emb_df['APPLICATION_ID'] = emb_df['APPLICATION_ID'].astype('int64')

# Merge
df = df.merge(emb_df[['APPLICATION_ID', 'embedding']], on='APPLICATION_ID', how='left')
embeddings = np.stack(df['embedding'].values)
print(f"  Embeddings: {embeddings.shape}")

# Apply UMAP
print("\n[3/4] Computing UMAP projection...")
print("  This takes ~10 minutes for 50k grants...")

reducer = umap.UMAP(
    n_neighbors=15,
    n_components=2,
    min_dist=0.1,
    metric='cosine',
    random_state=42,
    verbose=True,
    low_memory=False
)

coords = reducer.fit_transform(embeddings)

df['umap_x'] = coords[:, 0]
df['umap_y'] = coords[:, 1]

print(f"\n  UMAP complete")
print(f"  X range: [{coords[:, 0].min():.2f}, {coords[:, 0].max():.2f}]")
print(f"  Y range: [{coords[:, 1].min():.2f}, {coords[:, 1].max():.2f}]")

# Save
print("\n[4/4] Saving...")
output = df[['APPLICATION_ID', 'PROJECT_TITLE', 'IC_NAME', 'FY', 'TOTAL_COST',
             'domain', 'domain_label', 'topic', 'subtopic', 'umap_x', 'umap_y']].copy()

output.to_csv('hierarchical_50k_with_umap.csv', index=False)
print(f"  ✅ Saved: hierarchical_50k_with_umap.csv")

# Show sample
print("\nSample data:")
print(output[['APPLICATION_ID', 'domain_label', 'umap_x', 'umap_y']].head())

print("\n" + "=" * 80)
print("UMAP COMPLETE - READY FOR VISUALIZATION")
print("=" * 80)
print(f"\nDataset: {len(df):,} grants")
print(f"  Domains: {df['domain'].nunique()}")
print(f"  Topics: {df['topic'].nunique()}")
print(f"  Subtopics: {df['subtopic'].nunique()}")
print(f"  Coordinates: 2D UMAP")
print("\nNext: Create interactive visualization")
print("=" * 80)
