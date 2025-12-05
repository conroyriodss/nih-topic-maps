#!/usr/bin/env python3
"""
UMAP Parameter Sweep for Visualization Optimization
Explore n_neighbors, min_dist, and metric parameters
"""
import pandas as pd
import numpy as np
import umap
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import silhouette_score
import json
import time
from itertools import product

print("=" * 70)
print("UMAP PARAMETER SWEEP")
print("=" * 70)

# Load embeddings and cluster labels
print("\n[1/4] Loading data...")
df = pd.read_parquet('embeddings_100k_pubmedbert.parquet')
embeddings = np.stack(df['embedding'].values)

# Load cluster labels from best hierarchical clustering
try:
    cluster_df = pd.read_csv('hierarchical_best_clustering.csv')
    df = df.merge(cluster_df[['APPLICATION_ID', 'cluster']], on='APPLICATION_ID')
    labels = df['cluster'].values
    print(f"  Loaded {len(df):,} grants with cluster assignments")
except FileNotFoundError:
    print("  WARNING: No cluster labels found, using dummy labels")
    labels = np.zeros(len(df))

print(f"  Embeddings shape: {embeddings.shape}")

# Parameter grid
N_NEIGHBORS = [5, 15, 30, 50, 100, 200]
MIN_DIST = [0.0, 0.1, 0.25, 0.5, 0.8]
METRICS = ['euclidean', 'cosine']

print(f"\n[2/4] Parameter grid:")
print(f"  n_neighbors: {N_NEIGHBORS}")
print(f"  min_dist: {MIN_DIST}")
print(f"  metric: {METRICS}")
print(f"  Total combinations: {len(N_NEIGHBORS) * len(MIN_DIST) * len(METRICS)}")

# Step 3: Run parameter sweep
print("\n[3/4] Running parameter sweep...")
results = []
embeddings_2d = {}  # Store for visualization

total = len(N_NEIGHBORS) * len(MIN_DIST) * len(METRICS)
current = 0

for n_neighbors, min_dist, metric in product(N_NEIGHBORS, MIN_DIST, METRICS):
    current += 1
    print(f"\n  [{current}/{total}] n_neighbors={n_neighbors}, min_dist={min_dist}, metric={metric}")
    
    start = time.time()
    
    try:
        # Run UMAP
        reducer = umap.UMAP(
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            metric=metric,
            n_components=2,
            random_state=42,
            n_jobs=-1
        )
        embedding_2d = reducer.fit_transform(embeddings)
        
        # Compute quality metrics
        
        # 1. Global structure preservation (using cluster silhouette)
        if len(np.unique(labels)) > 1:
            silhouette_2d = silhouette_score(embedding_2d, labels)
        else:
            silhouette_2d = 0.0
        
        # 2. Local structure preservation (trustworthiness)
        from sklearn.manifold import trustworthiness
        trust = trustworthiness(embeddings, embedding_2d, n_neighbors=min(50, len(embeddings)-1))
        
        # 3. Spread metrics (how well spread out is the embedding)
        x_range = embedding_2d[:, 0].max() - embedding_2d[:, 0].min()
        y_range = embedding_2d[:, 1].max() - embedding_2d[:, 1].min()
        aspect_ratio = x_range / y_range if y_range > 0 else 1.0
        
        # 4. Cluster cohesion (variance within clusters)
        if len(np.unique(labels)) > 1:
            within_cluster_variance = 0
            for cluster_id in np.unique(labels):
                mask = labels == cluster_id
                if mask.sum() > 1:
                    cluster_points = embedding_2d[mask]
                    within_cluster_variance += np.var(cluster_points)
            within_cluster_variance /= len(np.unique(labels))
        else:
            within_cluster_variance = 0.0
        
        comp_time = time.time() - start
        
        results.append({
            'n_neighbors': n_neighbors,
            'min_dist': min_dist,
            'metric': metric,
            'silhouette_2d': float(silhouette_2d),
            'trustworthiness': float(trust),
            'x_range': float(x_range),
            'y_range': float(y_range),
            'aspect_ratio': float(aspect_ratio),
            'within_cluster_var': float(within_cluster_variance),
            'computation_time': comp_time
        })
        
        # Store select embeddings for visualization
        key = f"n{n_neighbors}_d{min_dist}_{metric}"
        if n_neighbors in [15, 50] and min_dist in [0.0, 0.5]:
            embeddings_2d[key] = embedding_2d
        
        print(f"    silhouette={silhouette_2d:.3f}, trust={trust:.3f}, time={comp_time:.1f}s")
        
    except Exception as e:
        print(f"    ERROR: {e}")
        continue

# Convert to DataFrame
results_df = pd.DataFrame(results)

print(f"\n[4/4] Completed {len(results)} parameter combinations")

# Analyze results
print("\n" + "=" * 70)
print("RESULTS SUMMARY")
print("=" * 70)

# Best by different criteria
print("\nTop 5 by Silhouette Score (cluster separation):")
for idx, row in results_df.nlargest(5, 'silhouette_2d').iterrows():
    print(f"  n={row['n_neighbors']:3d} dist={row['min_dist']:.2f} {row['metric']:9s} "
          f"silhouette={row['silhouette_2d']:.3f} trust={row['trustworthiness']:.3f}")

print("\nTop 5 by Trustworthiness (local structure):")
for idx, row in results_df.nlargest(5, 'trustworthiness').iterrows():
    print(f"  n={row['n_neighbors']:3d} dist={row['min_dist']:.2f} {row['metric']:9s} "
          f"silhouette={row['silhouette_2d']:.3f} trust={row['trustworthiness']:.3f}")

# Balanced recommendation
results_df['balanced_score'] = (
    results_df['silhouette_2d'] / results_df['silhouette_2d'].max() +
    results_df['trustworthiness'] / results_df['trustworthiness'].max()
) / 2

print("\nTop 5 by Balanced Score (silhouette + trustworthiness):")
for idx, row in results_df.nlargest(5, 'balanced_score').iterrows():
    print(f"  n={row['n_neighbors']:3d} dist={row['min_dist']:.2f} {row['metric']:9s} "
          f"silhouette={row['silhouette_2d']:.3f} trust={row['trustworthiness']:.3f} "
          f"balanced={row['balanced_score']:.3f}")

# Visualize results
print("\nCreating visualizations...")

sns.set_style('whitegrid')
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# 1. Silhouette by parameters
ax = axes[0, 0]
for metric in METRICS:
    for min_dist in [0.0, 0.25, 0.5]:
        data = results_df[(results_df['metric'] == metric) & 
                          (results_df['min_dist'] == min_dist)]
        ax.plot(data['n_neighbors'], data['silhouette_2d'],
                marker='o', label=f"{metric[:3]} d={min_dist}", linewidth=2)
ax.set_xlabel('n_neighbors', fontsize=12)
ax.set_ylabel('Silhouette Score', fontsize=12)
ax.set_title('Cluster Separation vs. n_neighbors', fontsize=14, fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# 2. Trustworthiness by parameters
ax = axes[0, 1]
for metric in METRICS:
    for min_dist in [0.0, 0.25, 0.5]:
        data = results_df[(results_df['metric'] == metric) & 
                          (results_df['min_dist'] == min_dist)]
        ax.plot(data['n_neighbors'], data['trustworthiness'],
                marker='s', label=f"{metric[:3]} d={min_dist}", linewidth=2)
ax.set_xlabel('n_neighbors', fontsize=12)
ax.set_ylabel('Trustworthiness', fontsize=12)
ax.set_title('Local Structure Preservation', fontsize=14, fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# 3. Balanced score heatmap (euclidean)
ax = axes[1, 0]
euc_data = results_df[results_df['metric'] == 'euclidean']
pivot = euc_data.pivot(index='min_dist', columns='n_neighbors', values='balanced_score')
sns.heatmap(pivot, annot=True, fmt='.3f', cmap='RdYlGn', ax=ax, cbar_kws={'label': 'Score'})
ax.set_title('Balanced Score (Euclidean)', fontsize=14, fontweight='bold')
ax.set_xlabel('n_neighbors', fontsize=12)
ax.set_ylabel('min_dist', fontsize=12)

# 4. Balanced score heatmap (cosine)
ax = axes[1, 1]
cos_data = results_df[results_df['metric'] == 'cosine']
pivot = cos_data.pivot(index='min_dist', columns='n_neighbors', values='balanced_score')
sns.heatmap(pivot, annot=True, fmt='.3f', cmap='RdYlGn', ax=ax, cbar_kws={'label': 'Score'})
ax.set_title('Balanced Score (Cosine)', fontsize=14, fontweight='bold')
ax.set_xlabel('n_neighbors', fontsize=12)
ax.set_ylabel('min_dist', fontsize=12)

plt.tight_layout()
plt.savefig('umap_param_sweep_results.png', dpi=300, bbox_inches='tight')
print("  Saved: umap_param_sweep_results.png")

# Visualize select embeddings
if len(embeddings_2d) > 0:
    fig, axes = plt.subplots(2, 4, figsize=(24, 12))
    axes = axes.flatten()
    
    for idx, (key, emb_2d) in enumerate(embeddings_2d.items()):
        if idx >= len(axes):
            break
        ax = axes[idx]
        scatter = ax.scatter(emb_2d[:, 0], emb_2d[:, 1], 
                             c=labels, cmap='tab20', s=1, alpha=0.6)
        ax.set_title(key.replace('_', ' '), fontsize=11, fontweight='bold')
        ax.axis('off')
    
    plt.tight_layout()
    plt.savefig('umap_embedding_comparison.png', dpi=300, bbox_inches='tight')
    print("  Saved: umap_embedding_comparison.png")

# Save results
results_df.to_csv('umap_param_sweep_results.csv', index=False)
print("  Saved: umap_param_sweep_results.csv")

# Save recommendations
best_balanced = results_df.nlargest(1, 'balanced_score').iloc[0]
recommendations = {
    'best_balanced': {
        'n_neighbors': int(best_balanced['n_neighbors']),
        'min_dist': float(best_balanced['min_dist']),
        'metric': best_balanced['metric'],
        'silhouette': float(best_balanced['silhouette_2d']),
        'trustworthiness': float(best_balanced['trustworthiness']),
        'balanced_score': float(best_balanced['balanced_score'])
    },
    'best_silhouette': results_df.nlargest(1, 'silhouette_2d')[[
        'n_neighbors', 'min_dist', 'metric', 'silhouette_2d'
    ]].to_dict('records')[0],
    'best_trust': results_df.nlargest(1, 'trustworthiness')[[
        'n_neighbors', 'min_dist', 'metric', 'trustworthiness'
    ]].to_dict('records')[0]
}

with open('umap_recommendations.json', 'w') as f:
    json.dump(recommendations, f, indent=2)
print("  Saved: umap_recommendations.json")

print("\n" + "=" * 70)
print("UMAP PARAMETER SWEEP COMPLETE!")
print("=" * 70)

print("\n🎯 RECOMMENDED UMAP CONFIGURATION:")
best = recommendations['best_balanced']
print(f"  n_neighbors: {best['n_neighbors']}")
print(f"  min_dist: {best['min_dist']}")
print(f"  metric: {best['metric']}")
print(f"  Silhouette: {best['silhouette']:.4f}")
print(f"  Trustworthiness: {best['trustworthiness']:.4f}")
print(f"  Balanced Score: {best['balanced_score']:.4f}")
