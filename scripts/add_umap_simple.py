#!/usr/bin/env python3
import pandas as pd
import numpy as np
import umap.umap_ as umap  # Direct import avoids torch conflict

print("=" * 70)
print("ADDING UMAP VISUALIZATION")
print("=" * 70)

# Load clustered data
print("\n[1/3] Loading clustered data...")
df = pd.read_parquet('grants_50k_SEMANTIC_clustered.parquet')
df_emb = pd.read_parquet('embeddings_50k_sample.parquet')
df = df.merge(df_emb, on='APPLICATION_ID')

# Extract embeddings
embeddings = np.vstack(df['embedding'].values)
print(f"  Embeddings: {embeddings.shape}")

# Generate UMAP (memory-efficient settings)
print("\n[2/3] Generating 2D UMAP coordinates...")
print("  This will take 10-15 minutes...")

reducer = umap.UMAP(
    n_components=2,
    n_neighbors=15,
    min_dist=0.1,
    random_state=42,
    low_memory=True,  # Critical for Cloud Shell!
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
print("\nNow run options 2-4:")
print("  2. Upload to BigQuery")
print("  3. Analyze clusters")
print("  4. Scale to 100k")
