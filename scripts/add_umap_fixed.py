#!/usr/bin/env python3
import pandas as pd
import numpy as np

# Import UMAP without triggering parametric_umap
import sys
import importlib.util

# Hack to skip parametric_umap import
spec = importlib.util.find_spec("umap.umap_")
umap_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(umap_module)
UMAP = umap_module.UMAP

print("=" * 70)
print("ADDING UMAP VISUALIZATION (FIXED)")
print("=" * 70)

# Load
print("\n[1/3] Loading clustered data...")
df = pd.read_parquet('grants_50k_SEMANTIC_clustered.parquet')
df_emb = pd.read_parquet('embeddings_50k_sample.parquet')
df = df.merge(df_emb, on='APPLICATION_ID')

embeddings = np.vstack(df['embedding'].values)
print(f"  Embeddings: {embeddings.shape}")

# UMAP
print("\n[2/3] Generating UMAP (10-15 minutes)...")
reducer = UMAP(
    n_components=2,
    n_neighbors=15,
    min_dist=0.1,
    random_state=42,
    low_memory=True,
    verbose=True
)
coords = reducer.fit_transform(embeddings)

df['umap_x'] = coords[:, 0]
df['umap_y'] = coords[:, 1]
df = df.drop('embedding', axis=1)

# Save
print("\n[3/3] Saving...")
df.to_parquet('grants_50k_SEMANTIC_with_viz.parquet', index=False)
print("  ✓ grants_50k_SEMANTIC_with_viz.parquet")

print("\n" + "=" * 70)
print("COMPLETE!")
print("=" * 70)
