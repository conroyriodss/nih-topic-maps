#!/usr/bin/env python3
"""
Generate embeddings for 103K awards using sentence-transformers
This will enable semantic clustering based on project content
"""
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from tqdm import tqdm

print("="*70)
print("GENERATING EMBEDDINGS FOR AWARD-LEVEL CLUSTERING")
print("="*70)

# Check for GPU
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"\nDevice: {device}")
if device == 'cuda':
    print(f"GPU: {torch.cuda.get_device_name(0)}")

# Load awards
print("\n[1/6] Loading award data...")
df = pd.read_csv('awards_110k_clustered_k75.csv')
print(f"Loaded {len(df):,} awards")

# Check for missing titles
missing = df['project_title'].isna().sum()
if missing > 0:
    print(f"⚠️  Missing titles: {missing:,} ({100*missing/len(df):.1f}%)")
    print("   Filling with 'Unknown Project'")
    df['project_title'] = df['project_title'].fillna('Unknown Project')

# Load model
print("\n[2/6] Loading embedding model...")
print("   Using: all-MiniLM-L6-v2 (384 dimensions, fast)")
model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
print(f"   Model loaded on {device}")

# Generate embeddings in batches
print("\n[3/6] Generating embeddings...")
batch_size = 256 if device == 'cuda' else 64
all_embeddings = []

titles = df['project_title'].tolist()

for i in tqdm(range(0, len(titles), batch_size), desc="Embedding batches"):
    batch = titles[i:i+batch_size]
    embeddings = model.encode(batch, show_progress_bar=False, convert_to_numpy=True)
    all_embeddings.append(embeddings)

embeddings_array = np.vstack(all_embeddings)
print(f"   Shape: {embeddings_array.shape}")
print(f"   Memory: {embeddings_array.nbytes / 1e6:.1f} MB")

# Save embeddings
print("\n[4/6] Saving embeddings...")
np.save('award_embeddings_103k.npy', embeddings_array)
print("   ✅ Saved: award_embeddings_103k.npy")

# Generate UMAP coordinates for visualization
print("\n[5/6] Generating UMAP coordinates...")
from umap import UMAP

print("   Fitting UMAP (this may take 5-10 minutes)...")
umap_model = UMAP(
    n_components=2,
    n_neighbors=15,
    min_dist=0.1,
    metric='cosine',
    random_state=42,
    verbose=True
)

umap_coords = umap_model.fit_transform(embeddings_array)
df['umap_x'] = umap_coords[:, 0]
df['umap_y'] = umap_coords[:, 1]

print(f"   UMAP range X: [{df['umap_x'].min():.2f}, {df['umap_x'].max():.2f}]")
print(f"   UMAP range Y: [{df['umap_y'].min():.2f}, {df['umap_y'].max():.2f}]")

# Re-cluster using embeddings
print("\n[6/6] Re-clustering using semantic embeddings...")
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import silhouette_score

kmeans = MiniBatchKMeans(
    n_clusters=75,
    batch_size=1000,
    random_state=42,
    n_init=10,
    verbose=1
)

df['cluster_semantic_k75'] = kmeans.fit_predict(embeddings_array)

# Evaluate
sample_size = min(10000, len(df))
silhouette = silhouette_score(embeddings_array, df['cluster_semantic_k75'], sample_size=sample_size)
print(f"\n   Semantic Clustering Silhouette: {silhouette:.4f}")

# Compare to old clustering
print("\n   Comparing clusterings:")
print(f"   Old (IC/activity based): {df['cluster_k75'].nunique()} clusters")
print(f"   New (semantic): {df['cluster_semantic_k75'].nunique()} clusters")

# Save updated dataset
df.to_csv('awards_110k_with_semantic_clusters.csv', index=False)
print("\n✅ Saved: awards_110k_with_semantic_clusters.csv")

print("\n" + "="*70)
print("EMBEDDING GENERATION COMPLETE")
print("="*70)
print("\nGenerated files:")
print("  • award_embeddings_103k.npy - 384D embeddings")
print("  • awards_110k_with_semantic_clusters.csv - Dataset with UMAP + clusters")
print("\nReady for visualization!")
print("="*70)
