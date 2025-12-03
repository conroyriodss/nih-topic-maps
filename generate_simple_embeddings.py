#!/usr/bin/env python3
"""
Generate simple TF-IDF embeddings for awards (faster, no dependencies)
Then apply UMAP and re-cluster
"""
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import silhouette_score
import umap

print("="*70)
print("GENERATING TF-IDF EMBEDDINGS FOR AWARDS")
print("="*70)

# Load awards
print("\n[1/5] Loading award data...")
df = pd.read_csv('awards_110k_clustered_k75.csv')
print(f"Loaded {len(df):,} awards")

# Handle missing titles
df['project_title'] = df['project_title'].fillna('Unknown Project')

# Generate TF-IDF features
print("\n[2/5] Generating TF-IDF embeddings...")
print("   This creates semantic features from project titles")

vectorizer = TfidfVectorizer(
    max_features=5000,
    ngram_range=(1, 2),
    stop_words='english',
    min_df=2,
    max_df=0.8
)

tfidf_matrix = vectorizer.fit_transform(df['project_title'])
print(f"   TF-IDF matrix: {tfidf_matrix.shape}")

# Reduce dimensionality with SVD
print("\n[3/5] Reducing dimensions with SVD...")
svd = TruncatedSVD(n_components=100, random_state=42)
embeddings = svd.fit_transform(tfidf_matrix)
print(f"   Embeddings: {embeddings.shape}")
print(f"   Variance explained: {svd.explained_variance_ratio_.sum():.2%}")

# Save embeddings
np.save('award_embeddings_tfidf_103k.npy', embeddings)
print("   ✅ Saved: award_embeddings_tfidf_103k.npy")

# Generate UMAP for visualization
print("\n[4/5] Generating UMAP coordinates...")
print("   This may take 5-10 minutes...")

umap_model = umap.UMAP(
    n_components=2,
    n_neighbors=15,
    min_dist=0.1,
    metric='cosine',
    random_state=42,
    verbose=True
)

umap_coords = umap_model.fit_transform(embeddings)
df['umap_x'] = umap_coords[:, 0]
df['umap_y'] = umap_coords[:, 1]

print(f"   UMAP X range: [{df['umap_x'].min():.2f}, {df['umap_x'].max():.2f}]")
print(f"   UMAP Y range: [{df['umap_y'].min():.2f}, {df['umap_y'].max():.2f}]")

# Re-cluster using semantic embeddings
print("\n[5/5] Clustering using semantic embeddings...")

kmeans = MiniBatchKMeans(
    n_clusters=75,
    batch_size=1000,
    random_state=42,
    n_init=10,
    verbose=1
)

df['cluster_semantic_k75'] = kmeans.fit_predict(embeddings)

# Evaluate
sample_size = min(10000, len(df))
silhouette = silhouette_score(embeddings, df['cluster_semantic_k75'], sample_size=sample_size)

print(f"\n✅ Semantic Clustering Results:")
print(f"   Silhouette score: {silhouette:.4f}")
print(f"   Clusters: {df['cluster_semantic_k75'].nunique()}")

# Compare clusterings
from sklearn.metrics import adjusted_rand_score
ari = adjusted_rand_score(df['cluster_k75'], df['cluster_semantic_k75'])
print(f"\n   Comparison to IC/activity clusters:")
print(f"   Adjusted Rand Index: {ari:.4f}")
print(f"   (0 = completely different, 1 = identical)")

# Save
df.to_csv('awards_110k_with_semantic_clusters.csv', index=False)
print("\n✅ Saved: awards_110k_with_semantic_clusters.csv")

# Quick cluster analysis
print("\n" + "="*70)
print("SEMANTIC CLUSTER PREVIEW")
print("="*70)

cluster_summary = df.groupby('cluster_semantic_k75').agg({
    'core_project_num': 'count',
    'total_lifetime_funding': 'sum',
    'ic_name': lambda x: x.mode()[0] if len(x) > 0 else 'Unknown'
}).rename(columns={'core_project_num': 'n_awards'})

print("\nTop 10 clusters by size:")
top10 = cluster_summary.nlargest(10, 'n_awards')
for idx, row in top10.iterrows():
    print(f"  C{idx:2d}: {row['n_awards']:>5,} awards | {row['ic_name'][:45]}")

print("\n" + "="*70)
print("COMPLETE - Ready for visualization!")
print("="*70)
