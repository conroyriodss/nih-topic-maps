#!/usr/bin/env python3
"""
Memory-Efficient Hierarchical Clustering Parameter Sweep
Optimized for Cloud Shell (limited RAM)
"""
import pandas as pd
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import json
import time

print("=" * 70)
print("HIERARCHICAL CLUSTERING PARAMETER SWEEP (MEMORY-EFFICIENT)")
print("=" * 70)

# Load embeddings
print("\n[1/4] Loading embeddings...")
start = time.time()
df = pd.read_parquet('embeddings_25k_subsample.parquet')
embeddings = np.stack(df['embedding'].values)
print(f"  Loaded {len(df):,} grants with {embeddings.shape[1]}-dim embeddings")
print(f"  Memory: {embeddings.nbytes / 1e9:.2f} GB")
print(f"  Time: {time.time() - start:.1f}s")

# MEMORY OPTIMIZATION: Use only Ward linkage (doesn't need distance matrix)
LINKAGE_METHODS = ['ward']  # Most relevant for biomedical data
N_CLUSTERS_WARD = [50, 75, 100, 125, 150]

print(f"\n[2/4] Parameter grid (memory-efficient):")
print(f"  Linkage method: Ward only (no precomputed distance matrix needed)")
print(f"  Cluster counts: {N_CLUSTERS_WARD}")

# Run parameter sweep
print("\n[3/4] Running parameter sweep...")
results = []

print(f"  Computing Ward linkage hierarchy...")
start = time.time()
Z = linkage(embeddings, method='ward')
print(f"  Linkage computed in {time.time() - start:.1f}s")

for n_clusters in N_CLUSTERS_WARD:
    print(f"\n  Testing K={n_clusters}...")
    start = time.time()
    
    labels = fcluster(Z, n_clusters, criterion='maxclust')
    
    # Compute quality metrics
    unique, counts = np.unique(labels, return_counts=True)
    
    # Silhouette (sample for speed - use 5k instead of 10k)
    sample_size = min(5000, len(embeddings))
    sample_idx = np.random.choice(len(embeddings), sample_size, replace=False)
    silhouette = silhouette_score(
        embeddings[sample_idx], 
        labels[sample_idx]
    )
    
    # Other metrics (on full data)
    calinski = calinski_harabasz_score(embeddings, labels)
    davies_bouldin = davies_bouldin_score(embeddings, labels)
    
    results.append({
        'linkage_method': 'ward',
        'n_clusters_target': n_clusters,
        'n_clusters_actual': len(unique),
        'min_cluster_size': int(counts.min()),
        'max_cluster_size': int(counts.max()),
        'mean_cluster_size': float(counts.mean()),
        'median_cluster_size': float(np.median(counts)),
        'std_cluster_size': float(counts.std()),
        'tiny_clusters_pct': float((counts < 50).sum() / len(unique) * 100),
        'silhouette_score': float(silhouette),
        'calinski_harabasz': float(calinski),
        'davies_bouldin': float(davies_bouldin),
        'computation_time': time.time() - start
    })
    
    print(f"    Silhouette: {silhouette:.4f}")
    print(f"    Calinski-Harabasz: {calinski:.0f}")
    print(f"    Davies-Bouldin: {davies_bouldin:.3f}")
    print(f"    Cluster sizes: {counts.min()}-{counts.max()} (mean: {counts.mean():.0f})")

# Convert to DataFrame
results_df = pd.DataFrame(results)

print(f"\n[4/4] Results Summary")
print("=" * 70)

# Best by each metric
print("\nTop configurations by metric:")
print(f"\nBest Silhouette: K={results_df.loc[results_df['silhouette_score'].idxmax(), 'n_clusters_actual']:.0f}, "
      f"score={results_df['silhouette_score'].max():.4f}")
print(f"Best Calinski-Harabasz: K={results_df.loc[results_df['calinski_harabasz'].idxmax(), 'n_clusters_actual']:.0f}, "
      f"score={results_df['calinski_harabasz'].max():.0f}")
print(f"Best Davies-Bouldin: K={results_df.loc[results_df['davies_bouldin'].idxmin(), 'n_clusters_actual']:.0f}, "
      f"score={results_df['davies_bouldin'].min():.3f}")

# Composite score
results_df['silhouette_norm'] = (results_df['silhouette_score'] - results_df['silhouette_score'].min()) / \
                                 (results_df['silhouette_score'].max() - results_df['silhouette_score'].min())
results_df['ch_norm'] = (results_df['calinski_harabasz'] - results_df['calinski_harabasz'].min()) / \
                        (results_df['calinski_harabasz'].max() - results_df['calinski_harabasz'].min())
results_df['db_norm'] = 1 - (results_df['davies_bouldin'] - results_df['davies_bouldin'].min()) / \
                            (results_df['davies_bouldin'].max() - results_df['davies_bouldin'].min())
results_df['composite_score'] = (results_df['silhouette_norm'] + 
                                  results_df['ch_norm'] + 
                                  results_df['db_norm']) / 3

best_idx = results_df['composite_score'].idxmax()
best = results_df.loc[best_idx]

print(f"\n🎯 RECOMMENDED CONFIGURATION (Composite Score):")
print(f"  Linkage: Ward")
print(f"  K: {best['n_clusters_actual']:.0f}")
print(f"  Silhouette: {best['silhouette_score']:.4f}")
print(f"  Calinski-Harabasz: {best['calinski_harabasz']:.0f}")
print(f"  Davies-Bouldin: {best['davies_bouldin']:.3f}")
print(f"  Composite Score: {best['composite_score']:.4f}")

# Visualization
print("\nCreating visualization...")
sns.set_style('whitegrid')
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1. Silhouette score
ax = axes[0, 0]
ax.plot(results_df['n_clusters_actual'], results_df['silhouette_score'], 
        marker='o', linewidth=2, markersize=8, color='#1f77b4')
ax.set_xlabel('Number of Clusters (K)', fontsize=11)
ax.set_ylabel('Silhouette Score', fontsize=11)
ax.set_title('Cluster Separation Quality', fontsize=13, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.axvline(best['n_clusters_actual'], color='red', linestyle='--', alpha=0.5, label='Best')
ax.legend()

# 2. Calinski-Harabasz
ax = axes[0, 1]
ax.plot(results_df['n_clusters_actual'], results_df['calinski_harabasz'],
        marker='s', linewidth=2, markersize=8, color='#ff7f0e')
ax.set_xlabel('Number of Clusters (K)', fontsize=11)
ax.set_ylabel('Calinski-Harabasz Index', fontsize=11)
ax.set_title('Variance Ratio (Higher = Better)', fontsize=13, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.axvline(best['n_clusters_actual'], color='red', linestyle='--', alpha=0.5, label='Best')
ax.legend()

# 3. Davies-Bouldin
ax = axes[1, 0]
ax.plot(results_df['n_clusters_actual'], results_df['davies_bouldin'],
        marker='^', linewidth=2, markersize=8, color='#2ca02c')
ax.set_xlabel('Number of Clusters (K)', fontsize=11)
ax.set_ylabel('Davies-Bouldin Index', fontsize=11)
ax.set_title('Cluster Similarity (Lower = Better)', fontsize=13, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.axvline(best['n_clusters_actual'], color='red', linestyle='--', alpha=0.5, label='Best')
ax.legend()

# 4. Composite score
ax = axes[1, 1]
ax.plot(results_df['n_clusters_actual'], results_df['composite_score'],
        marker='D', linewidth=2, markersize=8, color='#d62728')
ax.set_xlabel('Number of Clusters (K)', fontsize=11)
ax.set_ylabel('Composite Quality Score', fontsize=11)
ax.set_title('Overall Quality (Normalized Average)', fontsize=13, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.axvline(best['n_clusters_actual'], color='red', linestyle='--', alpha=0.5, label='Best')
ax.legend()

plt.tight_layout()
plt.savefig('hierarchical_param_sweep_results.png', dpi=200, bbox_inches='tight')
print("  Saved: hierarchical_param_sweep_results.png")

# Save results
results_df.to_csv('hierarchical_param_sweep_results.csv', index=False)
print("  Saved: hierarchical_param_sweep_results.csv")

# Save recommendations
recommendations = {
    'best_overall': {
        'linkage_method': 'ward',
        'n_clusters_actual': int(best['n_clusters_actual']),
        'silhouette_score': float(best['silhouette_score']),
        'calinski_harabasz': float(best['calinski_harabasz']),
        'davies_bouldin': float(best['davies_bouldin']),
        'composite_score': float(best['composite_score'])
    },
    'best_silhouette': results_df.nlargest(1, 'silhouette_score')[
        ['n_clusters_actual', 'silhouette_score']
    ].to_dict('records')[0],
    'best_calinski': results_df.nlargest(1, 'calinski_harabasz')[
        ['n_clusters_actual', 'calinski_harabasz']
    ].to_dict('records')[0],
    'best_davies_bouldin': results_df.nsmallest(1, 'davies_bouldin')[
        ['n_clusters_actual', 'davies_bouldin']
    ].to_dict('records')[0]
}

# Convert numpy types to native Python types for JSON
for key, value in recommendations.items():
    if isinstance(value, dict):
        for k, v in value.items():
            if isinstance(v, (np.integer, np.floating)):
                recommendations[key][k] = float(v) if isinstance(v, np.floating) else int(v)

with open('hierarchical_recommendations.json', 'w') as f:
    json.dump(recommendations, f, indent=2)
print("  Saved: hierarchical_recommendations.json")

print("\n" + "=" * 70)
print("PARAMETER SWEEP COMPLETE!")
print("=" * 70)

print(f"\nNext step: Apply best clustering")
print(f"  python3 scripts/apply_hierarchical_clustering.py")
