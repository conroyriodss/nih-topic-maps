#!/usr/bin/env python3
"""
Regenerate UMAP coordinates specifically for PROJECT_TERMS clusters
This will create tight, well-separated clusters on the map
"""

import pandas as pd
import numpy as np
from umap import UMAP
import subprocess

print("\n" + "="*70)
print("Regenerating UMAP for PROJECT_TERMS Clusters")
print("="*70 + "\n")

# Download clustered embeddings
print("Downloading PROJECT_TERMS embeddings...")
subprocess.run([
    'gsutil', 'cp',
    'gs://od-cl-odss-conroyri-nih-embeddings/sample/embeddings_project_terms_clustered_k100.parquet',
    'data/processed/'
], check=True)

# Load embeddings with clusters
print("Loading embeddings...")
df = pd.read_parquet('data/processed/embeddings_project_terms_clustered_k100.parquet')

print(f"Loaded {len(df):,} grants")
print(f"Embedding shape: {len(df)} x 768")

# Extract embeddings as numpy array
embeddings = np.array([np.array(emb) for emb in df['embedding']])

print(f"\nEmbeddings array shape: {embeddings.shape}")

# Generate UMAP with parameters optimized for cluster visualization
print("\nGenerating UMAP coordinates...")
print("  - n_neighbors: 30 (tighter local structure)")
print("  - min_dist: 0.1 (more separation)")
print("  - metric: cosine (semantic similarity)")
print("  - random_state: 42 (reproducible)")

umap_model = UMAP(
    n_components=2,
    n_neighbors=30,
    min_dist=0.1,
    metric='cosine',
    random_state=42,
    verbose=True,
    n_epochs=500
)

umap_coords = umap_model.fit_transform(embeddings)

print(f"\nUMAP coordinates shape: {umap_coords.shape}")

# Create results dataframe
results = pd.DataFrame({
    'APPLICATION_ID': df['APPLICATION_ID'].values,
    'umap_x': umap_coords[:, 0],
    'umap_y': umap_coords[:, 1],
    'cluster': df['cluster'].values,
    'ic': df['IC_NAME'].values,
    'year': df['FISCAL_YEAR'].values,
    'title': df['PROJECT_TITLE'].values,
    'cost': df['TOTAL_COST'].values
})

# Save locally
output_file = 'data/processed/umap_project_terms_k100.parquet'
results.to_parquet(output_file)
print(f"\n✓ Saved to: {output_file}")
print(f"  Size: {len(results):,} rows")

# Upload to GCS
print("\nUploading to GCS...")
subprocess.run(['gsutil', 'cp', output_file, 'gs://od-cl-odss-conroyri-nih-embeddings/sample/'], check=True)

print("\n" + "="*70)
print("UMAP REGENERATION COMPLETE")
print("="*70)
print(f"\nNew UMAP coordinates: umap_project_terms_k100.parquet")
print(f"Optimized for: Tight cluster visualization")
print(f"Parameters: n_neighbors=30, min_dist=0.1, metric=cosine")
print(f"\nNext: Regenerate visualization with new coordinates")
