#!/usr/bin/env python3
"""
Extract embeddings from viz data and run HDBSCAN
"""
import json
import numpy as np
import pandas as pd
import hdbscan
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import umap
from collections import Counter

print("Loading visualization data...")
with open('viz_data_project_terms_k100_final.json', 'r') as f:
    viz_data = json.load(f)

print(f"Loaded {len(viz_data['points'])} grants")
print(f"Loaded {len(viz_data['clusters'])} K-means clusters")

# Extract data
points = viz_data['points']
df = pd.DataFrame(points)

# Create embeddings from UMAP coordinates (we'll re-run UMAP properly)
# For now, use the x,y as a 2D embedding
coords_2d = np.array([[p['x'], p['y']] for p in points])

print("\nNote: Using existing 2D UMAP coordinates for clustering")
print("For best results, should use original high-dimensional embeddings")

# Standardize
scaler = StandardScaler()
coords_scaled = scaler.fit_transform(coords_2d)

# HDBSCAN clustering
print("\nRunning HDBSCAN on 2D UMAP space...")
clusterer = hdbscan.HDBSCAN(
    min_cluster_size=100,
    min_samples=20,
    cluster_selection_epsilon=0.5,
    metric='euclidean',
    cluster_selection_method='eom',
    prediction_data=True
)

labels = clusterer.fit_predict(coords_scaled)

# Results
n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
n_noise = sum(labels == -1)
cluster_sizes = Counter(labels)

print(f"\n{'='*60}")
print("HDBSCAN RESULTS (on 2D UMAP space)")
print(f"{'='*60}")
print(f"Clusters found: {n_clusters}")
print(f"Noise points: {n_noise:,} ({100*n_noise/len(labels):.1f}%)")
print(f"Clustered points: {len(labels)-n_noise:,}")

if n_noise < len(labels):
    mask = labels != -1
    silhouette = silhouette_score(coords_scaled[mask], labels[mask])
    print(f"Silhouette score: {silhouette:.4f}")
else:
    silhouette = 0.0

print(f"\n{'='*60}")
print("COMPARISON: K-MEANS vs HDBSCAN")
print(f"{'='*60}")
print("\n| Metric | K-means | HDBSCAN |")
print("|--------|---------|---------|")
print(f"| Clusters | 100 | {n_clusters} |")
print(f"| Outliers | 0 | {n_noise:,} |")
print(f"| Silhouette | 0.039 | {silhouette:.4f} |")
print(f"| Boundary type | Hard | Density-based |")

# Cluster sizes
sizes = [s for l, s in cluster_sizes.items() if l != -1]
if sizes:
    print(f"\nCluster size distribution:")
    print(f"  Min: {min(sizes)}, Max: {max(sizes)}")
    print(f"  Mean: {np.mean(sizes):.0f}, Median: {np.median(sizes):.0f}")

# Save results
df['cluster_hdbscan'] = labels
df.to_csv('grants_with_hdbscan.csv', index=False)

# Create new viz data with HDBSCAN clusters
viz_data_hdbscan = {
    'points': [
        {
            'application_id': p['application_id'],
            'x': p['x'],
            'y': p['y'],
            'cluster': int(labels[i]),
            'cluster_kmeans': p['cluster'],
            'ic': p['ic'],
            'year': p['year'],
            'cost': p['cost'],
            'title': p.get('title', '')
        }
        for i, p in enumerate(points)
    ],
    'clusters': []
}

# Generate HDBSCAN cluster summaries
for cluster_id in range(n_clusters):
    mask = labels == cluster_id
    cluster_points = [p for i, p in enumerate(points) if mask[i]]
    
    viz_data_hdbscan['clusters'].append({
        'id': int(cluster_id),
        'size': int(mask.sum()),
        'label': f"HDBSCAN Cluster {cluster_id}",
    })

with open('viz_data_hdbscan.json', 'w') as f:
    json.dump(viz_data_hdbscan, f)

print(f"\n{'='*60}")
print("FILES CREATED")
print(f"{'='*60}")
print("✓ grants_with_hdbscan.csv")
print("✓ viz_data_hdbscan.json")

print("\n⚠️  IMPORTANT LIMITATION:")
print("This analysis used 2D UMAP coordinates, not original embeddings.")
print("For best results, need original high-dimensional embeddings.")
print("\nHowever, this shows the concept: HDBSCAN finds natural")
print("density-based clusters instead of forcing hard boundaries.")

