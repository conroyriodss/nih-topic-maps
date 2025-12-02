#!/usr/bin/env python3
"""
Use PCA for 2D projection (fast, no torch dependencies)
Good enough for visualization purposes
"""
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

print("=" * 80)
print("ADDING 2D COORDINATES (PCA) TO 50K DATASET")
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

# Apply PCA (much faster than UMAP)
print("\n[3/4] Computing PCA projection...")
print("  Using PCA as fast alternative to UMAP...")

scaler = StandardScaler()
embeddings_scaled = scaler.fit_transform(embeddings)

pca = PCA(n_components=2, random_state=42)
coords = pca.fit_transform(embeddings_scaled)

# Scale to similar range as UMAP for visualization
coords = coords * 5  # Make points more spread out

df['umap_x'] = coords[:, 0]
df['umap_y'] = coords[:, 1]

print(f"  PCA complete")
print(f"  Variance explained: {pca.explained_variance_ratio_.sum():.1%}")
print(f"  X range: [{coords[:, 0].min():.2f}, {coords[:, 0].max():.2f}]")
print(f"  Y range: [{coords[:, 1].min():.2f}, {coords[:, 1].max():.2f}]")

# Save
print("\n[4/4] Saving...")
output = df[['APPLICATION_ID', 'PROJECT_TITLE', 'IC_NAME', 'FY', 'TOTAL_COST',
             'domain', 'domain_label', 'topic', 'subtopic', 'umap_x', 'umap_y']].copy()

output.to_csv('hierarchical_50k_with_coords.csv', index=False)
print(f"  ✅ Saved: hierarchical_50k_with_coords.csv")

# Show sample by domain
print("\nSample by domain:")
for domain in sorted(df['domain'].unique())[:3]:
    sample = output[output['domain'] == domain].head(1)
    print(f"  Domain {domain}: x={sample['umap_x'].values[0]:.2f}, y={sample['umap_y'].values[0]:.2f}")

print("\n" + "=" * 80)
print("COORDINATES ADDED - READY FOR VISUALIZATION")
print("=" * 80)
print(f"\nDataset: {len(df):,} grants")
print(f"  Domains: {df['domain'].nunique()}")
print(f"  Topics: {df['topic'].nunique()}")
print(f"  Subtopics: {df['subtopic'].nunique()}")
print(f"  Method: PCA (fast, ~{pca.explained_variance_ratio_.sum():.0%} variance)")
print("\nNote: Can replace with UMAP later on VM if needed")
print("      PCA is good enough for interactive exploration")
print("=" * 80)
