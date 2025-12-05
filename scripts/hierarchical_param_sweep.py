#!/usr/bin/env python3
"""
Hierarchical Clustering Parameter Sweep
Explore linkage methods, distance thresholds, and visualization parameters
"""
import pandas as pd
import numpy as np
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from scipy.spatial.distance import pdist
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
import matplotlib.pyplot as plt
import seaborn as sns
import json
import time
from itertools import product

print("=" * 70)
print("HIERARCHICAL CLUSTERING PARAMETER SWEEP")
print("=" * 70)

# Load embeddings
print("\n[1/5] Loading embeddings...")
start = time.time()
df = pd.read_parquet('embeddings_100k_pubmedbert.parquet')
embeddings = np.stack(df['embedding'].values)
print(f"  Loaded {len(df):,} grants with {embeddings.shape[1]}-dim embeddings")
print(f"  Time: {time.time() - start:.1f}s")

# Parameter grid
LINKAGE_METHODS = ['ward', 'complete', 'average', 'single']
DISTANCE_THRESHOLDS = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]  # For non-Ward
N_CLUSTERS_WARD = [50, 75, 100, 125, 150, 200]  # For Ward (cut at specific K)

print(f"\n[2/5] Parameter grid:")
print(f"  Linkage methods: {LINKAGE_METHODS}")
print(f"  Distance thresholds (complete/average/single): {DISTANCE_THRESHOLDS}")
print(f"  Cluster counts (Ward): {N_CLUSTERS_WARD}")

# Step 3: Run parameter sweep
print("\n[3/5] Running parameter sweep...")
results = []

# Pre-compute distance matrix for non-Ward methods
print("  Computing pairwise distances...")
dist_matrix = pdist(embeddings, metric='euclidean')
print(f"  Distance matrix computed")

for method in LINKAGE_METHODS:
    print(f"\n  Testing {method} linkage...")
    start = time.time()
    
    if method == 'ward':
        # Ward requires raw data, not precomputed distances
        Z = linkage(embeddings, method='ward')
        
        # Test multiple cluster counts
        for n_clusters in N_CLUSTERS_WARD:
            labels = fcluster(Z, n_clusters, criterion='maxclust')
            
            # Compute quality metrics
            unique, counts = np.unique(labels, return_counts=True)
            
            # Silhouette (sample for speed)
            sample_size = min(10000, len(embeddings))
            sample_idx = np.random.choice(len(embeddings), sample_size, replace=False)
            silhouette = silhouette_score(
                embeddings[sample_idx], 
                labels[sample_idx]
            )
            
            # Other metrics
            calinski = calinski_harabasz_score(embeddings, labels)
            davies_bouldin = davies_bouldin_score(embeddings, labels)
            
            results.append({
                'linkage_method': method,
                'distance_threshold': None,
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
            print(f"    K={n_clusters}: {len(unique)} clusters, silhouette={silhouette:.3f}")
    
    else:
        # Other methods use precomputed distances
        Z = linkage(dist_matrix, method=method)
        
        # Test multiple distance thresholds
        for threshold in DISTANCE_THRESHOLDS:
            labels = fcluster(Z, threshold, criterion='distance')
            
            unique, counts = np.unique(labels, return_counts=True)
            
            # Only proceed if we get reasonable number of clusters
            if len(unique) < 10 or len(unique) > 500:
                print(f"    t={threshold}: {len(unique)} clusters (skipped - out of range)")
                continue
            
            # Compute quality metrics
            sample_size = min(10000, len(embeddings))
            sample_idx = np.random.choice(len(embeddings), sample_size, replace=False)
            silhouette = silhouette_score(
                embeddings[sample_idx],
                labels[sample_idx]
            )
            
            calinski = calinski_harabasz_score(embeddings, labels)
            davies_bouldin = davies_bouldin_score(embeddings, labels)
            
            results.append({
                'linkage_method': method,
                'distance_threshold': threshold,
                'n_clusters_target': None,
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
            print(f"    t={threshold}: {len(unique)} clusters, silhouette={silhouette:.3f}")

# Convert to DataFrame
results_df = pd.DataFrame(results)

print(f"\n[4/5] Completed {len(results)} parameter combinations")

# Step 4: Analyze results
print("\n" + "=" * 70)
print("RESULTS SUMMARY")
print("=" * 70)

# Best by silhouette score
best_silhouette = results_df.nlargest(5, 'silhouette_score')
print("\nTop 5 by Silhouette Score:")
for idx, row in best_silhouette.iterrows():
    print(f"  {row['linkage_method']:8s} "
          f"K={row['n_clusters_actual']:3d} "
          f"silhouette={row['silhouette_score']:.4f} "
          f"CH={row['calinski_harabasz']:.0f} "
          f"DB={row['davies_bouldin']:.3f}")

# Best by Calinski-Harabasz
best_ch = results_df.nlargest(5, 'calinski_harabasz')
print("\nTop 5 by Calinski-Harabasz Index:")
for idx, row in best_ch.iterrows():
    print(f"  {row['linkage_method']:8s} "
          f"K={row['n_clusters_actual']:3d} "
          f"silhouette={row['silhouette_score']:.4f} "
          f"CH={row['calinski_harabasz']:.0f} "
          f"DB={row['davies_bouldin']:.3f}")

# Best by Davies-Bouldin (lower is better)
best_db = results_df.nsmallest(5, 'davies_bouldin')
print("\nTop 5 by Davies-Bouldin Index (lower is better):")
for idx, row in best_db.iterrows():
    print(f"  {row['linkage_method']:8s} "
          f"K={row['n_clusters_actual']:3d} "
          f"silhouette={row['silhouette_score']:.4f} "
          f"CH={row['calinski_harabasz']:.0f} "
          f"DB={row['davies_bouldin']:.3f}")

# Cluster size distribution analysis
print("\nCluster Size Distribution by Method:")
for method in LINKAGE_METHODS:
    method_results = results_df[results_df['linkage_method'] == method]
    if len(method_results) == 0:
        continue
    avg_tiny_pct = method_results['tiny_clusters_pct'].mean()
    avg_std = method_results['std_cluster_size'].mean()
    print(f"  {method:8s}: {avg_tiny_pct:.1f}% tiny clusters, "
          f"std={avg_std:.0f}")

# Step 5: Visualize results
print("\n[5/5] Creating visualizations...")

# Set style
sns.set_style('whitegrid')
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# 1. Silhouette score by method and K
ax = axes[0, 0]
for method in LINKAGE_METHODS:
    method_data = results_df[results_df['linkage_method'] == method]
    ax.plot(method_data['n_clusters_actual'], 
            method_data['silhouette_score'],
            marker='o', label=method, linewidth=2)
ax.set_xlabel('Number of Clusters', fontsize=12)
ax.set_ylabel('Silhouette Score', fontsize=12)
ax.set_title('Clustering Quality vs. Number of Clusters', fontsize=14, fontweight='bold')
ax.legend(title='Linkage Method')
ax.grid(True, alpha=0.3)

# 2. Cluster size variability
ax = axes[0, 1]
for method in LINKAGE_METHODS:
    method_data = results_df[results_df['linkage_method'] == method]
    ax.plot(method_data['n_clusters_actual'],
            method_data['std_cluster_size'],
            marker='s', label=method, linewidth=2)
ax.set_xlabel('Number of Clusters', fontsize=12)
ax.set_ylabel('Std Dev of Cluster Sizes', fontsize=12)
ax.set_title('Cluster Size Variability', fontsize=14, fontweight='bold')
ax.legend(title='Linkage Method')
ax.grid(True, alpha=0.3)

# 3. Tiny clusters percentage
ax = axes[1, 0]
for method in LINKAGE_METHODS:
    method_data = results_df[results_df['linkage_method'] == method]
    ax.plot(method_data['n_clusters_actual'],
            method_data['tiny_clusters_pct'],
            marker='^', label=method, linewidth=2)
ax.set_xlabel('Number of Clusters', fontsize=12)
ax.set_ylabel('Tiny Clusters (%)', fontsize=12)
ax.set_title('Percentage of Tiny Clusters (<50 grants)', fontsize=14, fontweight='bold')
ax.legend(title='Linkage Method')
ax.grid(True, alpha=0.3)

# 4. Multi-metric comparison (normalized)
ax = axes[1, 1]
# Normalize metrics to 0-1 scale for comparison
results_norm = results_df.copy()
results_norm['silhouette_norm'] = (results_norm['silhouette_score'] - results_norm['silhouette_score'].min()) / \
                                    (results_norm['silhouette_score'].max() - results_norm['silhouette_score'].min())
results_norm['ch_norm'] = (results_norm['calinski_harabasz'] - results_norm['calinski_harabasz'].min()) / \
                           (results_norm['calinski_harabasz'].max() - results_norm['calinski_harabasz'].min())
results_norm['db_norm'] = 1 - (results_norm['davies_bouldin'] - results_norm['davies_bouldin'].min()) / \
                               (results_norm['davies_bouldin'].max() - results_norm['davies_bouldin'].min())

# Composite score
results_norm['composite_score'] = (results_norm['silhouette_norm'] + 
                                    results_norm['ch_norm'] + 
                                    results_norm['db_norm']) / 3

for method in LINKAGE_METHODS:
    method_data = results_norm[results_norm['linkage_method'] == method]
    ax.plot(method_data['n_clusters_actual'],
            method_data['composite_score'],
            marker='D', label=method, linewidth=2, markersize=8)
ax.set_xlabel('Number of Clusters', fontsize=12)
ax.set_ylabel('Composite Quality Score (0-1)', fontsize=12)
ax.set_title('Overall Clustering Quality (Normalized)', fontsize=14, fontweight='bold')
ax.legend(title='Linkage Method')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('hierarchical_param_sweep_results.png', dpi=300, bbox_inches='tight')
print("  Saved: hierarchical_param_sweep_results.png")

# Save detailed results
results_df.to_csv('hierarchical_param_sweep_results.csv', index=False)
print("  Saved: hierarchical_param_sweep_results.csv")

# Save top recommendations
recommendations = {
    'best_overall': results_norm.nlargest(1, 'composite_score')[[
        'linkage_method', 'n_clusters_actual', 'silhouette_score', 
        'calinski_harabasz', 'davies_bouldin'
    ]].to_dict('records')[0],
    'best_silhouette': results_df.nlargest(1, 'silhouette_score')[[
        'linkage_method', 'n_clusters_actual', 'silhouette_score'
    ]].to_dict('records')[0],
    'best_calinski': results_df.nlargest(1, 'calinski_harabasz')[[
        'linkage_method', 'n_clusters_actual', 'calinski_harabasz'
    ]].to_dict('records')[0],
    'best_davies_bouldin': results_df.nsmallest(1, 'davies_bouldin')[[
        'linkage_method', 'n_clusters_actual', 'davies_bouldin'
    ]].to_dict('records')[0]
}

with open('hierarchical_recommendations.json', 'w') as f:
    json.dump(recommendations, f, indent=2)
print("  Saved: hierarchical_recommendations.json")

print("\n" + "=" * 70)
print("PARAMETER SWEEP COMPLETE!")
print("=" * 70)

print("\n🎯 RECOMMENDED CONFIGURATION:")
best = recommendations['best_overall']
print(f"  Linkage: {best['linkage_method']}")
print(f"  Clusters: {best['n_clusters_actual']}")
print(f"  Silhouette: {best['silhouette_score']:.4f}")
print(f"  Calinski-Harabasz: {best['calinski_harabasz']:.0f}")
print(f"  Davies-Bouldin: {best['davies_bouldin']:.3f}")
