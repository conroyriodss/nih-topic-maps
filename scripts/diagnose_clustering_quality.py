#!/usr/bin/env python3
"""
OPTION B: Diagnose Clustering Quality Issues
"""
import pandas as pd
import numpy as np
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from scipy.spatial.distance import pdist
import matplotlib.pyplot as plt
import glob
import sys

print("=" * 70)
print("OPTION B: CLUSTERING QUALITY DIAGNOSTIC")
print("=" * 70)

# Find cluster files
cluster_files = glob.glob('hierarchical_*.csv') + glob.glob('*_50k*.csv')
if not cluster_files:
    print("\n✗ No cluster files found")
    sys.exit(1)

print(f"\nFound {len(cluster_files)} file(s):")
for f in cluster_files:
    print(f"  - {f}")

cluster_file = cluster_files[0]
print(f"\nAnalyzing: {cluster_file}")

df = pd.read_csv(cluster_file)
print(f"Loaded {len(df):,} grants")

# Check dimensionality
print("\n" + "=" * 70)
print("[1] DIMENSIONALITY CHECK")
print("=" * 70)

has_embeddings = 'embedding' in df.columns
has_umap = all(c in df.columns for c in ['umap_x', 'umap_y'])

print(f"Embeddings: {'✓' if has_embeddings else '✗'}")
print(f"UMAP coords: {'✓' if has_umap else '✗'}")

if has_embeddings:
    try:
        embeddings = np.vstack(df['embedding'].apply(eval).values)
        print(f"Embedding dimension: {embeddings.shape[1]}")
        X_high = embeddings
    except:
        has_embeddings = False

if has_umap:
    X_low = df[['umap_x', 'umap_y']].values
    print(f"UMAP dimension: {X_low.shape[1]}")
    if not has_embeddings:
        print("\n⚠️  CRITICAL: Clustering on 2D UMAP loses 99.7% of information!")
        print("   Recommendation: Re-cluster on full embeddings")

# Analyze clusters
print("\n" + "=" * 70)
print("[2] CLUSTER ANALYSIS")
print("=" * 70)

cluster_cols = [c for c in df.columns if 'cluster' in c.lower()]
if not cluster_cols:
    print("✗ No cluster column found")
    sys.exit(1)

cluster_col = cluster_cols[0]
labels = df[cluster_col].values
n_clusters = df[cluster_col].nunique()
sizes = df[cluster_col].value_counts()

print(f"Clusters: {n_clusters}")
print(f"Size range: {sizes.min()} - {sizes.max()} (mean: {sizes.mean():.1f})")

if (sizes < 10).sum() > 0:
    print(f"⚠️  {(sizes < 10).sum()} clusters have <10 grants")

# Calculate metrics
print("\n" + "=" * 70)
print("[3] QUALITY METRICS")
print("=" * 70)

if has_umap:
    sil_2d = silhouette_score(X_low, labels, metric='euclidean')
    ch_2d = calinski_harabasz_score(X_low, labels)
    db_2d = davies_bouldin_score(X_low, labels)
    print(f"2D UMAP space:")
    print(f"  Silhouette: {sil_2d:+.4f}")
    print(f"  Calinski-Harabasz: {ch_2d:.2f}")
    print(f"  Davies-Bouldin: {db_2d:.2f}")

if has_embeddings:
    sample_idx = np.random.choice(len(df), min(10000, len(df)), replace=False)
    sil_high = silhouette_score(X_high[sample_idx], labels[sample_idx], metric='cosine')
    ch_high = calinski_harabasz_score(X_high[sample_idx], labels[sample_idx])
    db_high = davies_bouldin_score(X_high[sample_idx], labels[sample_idx])
    print(f"\n768D embedding space:")
    print(f"  Silhouette: {sil_high:+.4f}")
    print(f"  Calinski-Harabasz: {ch_high:.2f}")
    print(f"  Davies-Bouldin: {db_high:.2f}")

# Distance analysis
print("\n" + "=" * 70)
print("[4] DISTANCE DISTRIBUTION")
print("=" * 70)

sample_idx = np.random.choice(len(df), min(5000, len(df)), replace=False)
if has_embeddings:
    dists = pdist(X_high[sample_idx], metric='cosine')
elif has_umap:
    dists = pdist(X_low[sample_idx], metric='euclidean')

print(f"Pairwise distances:")
print(f"  Min: {dists.min():.4f}")
print(f"  Mean: {dists.mean():.4f}")
print(f"  Max: {dists.max():.4f}")
print(f"  Std: {dists.std():.4f}")

cv = dists.std() / dists.mean()
print(f"  Coefficient of variation: {cv:.3f}")

if cv < 0.3:
    print("\n⚠️  LOW VARIATION: Continuous manifold (normal for grants)")
    print("   Recommendation: Hierarchical clustering with multiple levels")

# Plot
plt.figure(figsize=(10, 5))
plt.hist(dists, bins=100, alpha=0.7, edgecolor='black')
plt.xlabel('Pairwise Distance')
plt.ylabel('Frequency')
plt.title('Distance Distribution (Bimodal = good, Uniform = continuous)')
plt.axvline(dists.mean(), color='red', linestyle='--', label=f'Mean: {dists.mean():.3f}')
plt.legend()
plt.tight_layout()
plt.savefig('pairwise_distance_distribution.png', dpi=150)
print(f"\n✓ Saved: pairwise_distance_distribution.png")

# Interpretability
print("\n" + "=" * 70)
print("[5] CLUSTER INTERPRETABILITY")
print("=" * 70)

if 'IC_NAME' in df.columns:
    purities = []
    for cid in df[cluster_col].unique():
        cluster = df[df[cluster_col] == cid]
        purity = cluster['IC_NAME'].value_counts().iloc[0] / len(cluster)
        purities.append(purity)
    print(f"IC purity: {np.mean(purities):.1%}")
    print(f"(Random baseline: {1/df['IC_NAME'].nunique():.1%})")

# Summary
print("\n" + "=" * 70)
print("[6] DIAGNOSIS SUMMARY")
print("=" * 70)

issues = []
recommendations = []

if has_umap and not has_embeddings:
    issues.append("Clustering on 2D UMAP (99.7% info loss)")
    recommendations.append("Re-cluster on full 768D embeddings")

if cv < 0.3:
    issues.append("Continuous data manifold")
    recommendations.append("Use hierarchical clustering (3+ levels)")

if n_clusters > 0 and len(df) / n_clusters < 20:
    issues.append(f"Clusters too small (avg {len(df)/n_clusters:.1f})")
    recommendations.append(f"Reduce K from {n_clusters} to {n_clusters//2}")

print("\n🔍 Issues:")
for i, issue in enumerate(issues, 1):
    print(f"  {i}. {issue}")

print("\n💡 Recommendations:")
for i, rec in enumerate(recommendations, 1):
    print(f"  {i}. {rec}")

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)
