#!/usr/bin/env python3
"""
HDBSCAN clustering for NIH grants - creates continuous topic flow
Addresses isolated clusters and hard boundaries from K-means
"""

import numpy as np
import pandas as pd
import hdbscan
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import umap
import json
from collections import Counter
import sys

print("Loading embeddings and data...")
embeddings = np.load('embeddings_project_terms.npy')
df = pd.read_csv('grant_data_with_project_terms.csv')

print(f"Loaded {len(embeddings)} embeddings, shape: {embeddings.shape}")
print(f"Loaded {len(df)} grant records")

# Standardize embeddings
print("\nStandardizing embeddings...")
scaler = StandardScaler()
embeddings_scaled = scaler.fit_transform(embeddings)

# HDBSCAN clustering with parameters optimized for continuous flow
print("\nRunning HDBSCAN clustering...")
print("Parameters:")
print("  - min_cluster_size=100 (avg ~430 grants/cluster)")
print("  - min_samples=20 (stricter core points)")
print("  - cluster_selection_epsilon=0.5 (allows cluster merging)")
print("  - metric=euclidean")
print("  - cluster_selection_method=eom (excess of mass)")

clusterer = hdbscan.HDBSCAN(
    min_cluster_size=100,
    min_samples=20,
    cluster_selection_epsilon=0.5,
    metric='euclidean',
    cluster_selection_method='eom',
    prediction_data=True
)

cluster_labels = clusterer.fit_predict(embeddings_scaled)

# Analyze clustering results
n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
n_noise = sum(cluster_labels == -1)
cluster_sizes = Counter(cluster_labels)

print(f"\n{'='*60}")
print("CLUSTERING RESULTS")
print(f"{'='*60}")
print(f"Clusters found: {n_clusters}")
print(f"Noise points: {n_noise:,} ({100*n_noise/len(cluster_labels):.1f}%)")
print(f"Clustered points: {len(cluster_labels) - n_noise:,} ({100*(len(cluster_labels)-n_noise)/len(cluster_labels):.1f}%)")

# Calculate silhouette score (excluding noise)
if n_noise < len(cluster_labels):
    mask = cluster_labels != -1
    silhouette = silhouette_score(embeddings_scaled[mask], cluster_labels[mask])
    print(f"Silhouette score: {silhouette:.4f}")
else:
    print("Cannot calculate silhouette: all points are noise")
    silhouette = 0.0

# Cluster size distribution
print(f"\nCluster size distribution:")
sizes = [size for label, size in cluster_sizes.items() if label != -1]
if sizes:
    print(f"  Min: {min(sizes)}")
    print(f"  Max: {max(sizes)}")
    print(f"  Mean: {np.mean(sizes):.1f}")
    print(f"  Median: {np.median(sizes):.1f}")

# Top 10 largest clusters
print(f"\nTop 10 largest clusters:")
for label, size in sorted(cluster_sizes.items(), key=lambda x: x[1], reverse=True)[:10]:
    if label != -1:
        print(f"  Cluster {label}: {size:,} grants")

# Get soft cluster memberships
print("\nComputing soft cluster memberships...")
soft_memberships = hdbscan.all_points_membership_vectors(clusterer)
print(f"Soft membership matrix shape: {soft_memberships.shape}")

# Analyze soft assignments
multi_cluster_grants = 0
for i, memberships in enumerate(soft_memberships):
    # Count how many clusters this grant has >10% membership in
    strong_memberships = sum(memberships > 0.1)
    if strong_memberships > 1:
        multi_cluster_grants += 1

print(f"Grants with multiple cluster memberships (>10%): {multi_cluster_grants:,} ({100*multi_cluster_grants/len(soft_memberships):.1f}%)")

# UMAP projection for visualization
print("\nComputing UMAP projection...")
reducer = umap.UMAP(
    n_neighbors=15,
    min_dist=0.1,
    metric='euclidean',
    random_state=42,
    verbose=True
)
coords = reducer.fit_transform(embeddings_scaled)

# Add results to dataframe
df['cluster_hdbscan'] = cluster_labels
df['umap_x'] = coords[:, 0]
df['umap_y'] = coords[:, 1]

# Add top cluster membership for each grant
df['cluster_prob'] = [memberships[label] if label != -1 else 0.0 
                       for memberships, label in zip(soft_memberships, cluster_labels)]

# Save results
print("\nSaving results...")
df.to_csv('grant_data_hdbscan.csv', index=False)
np.save('cluster_labels_hdbscan.npy', cluster_labels)
np.save('soft_memberships_hdbscan.npy', soft_memberships)
np.save('umap_coords_hdbscan.npy', coords)

# Generate cluster summaries
print("\nGenerating cluster summaries...")
cluster_summaries = []
for cluster_id in range(n_clusters):
    mask = cluster_labels == cluster_id
    cluster_grants = df[mask]
    
    # Get top terms for this cluster
    top_terms = []
    for terms_str in cluster_grants['PROJECT_TERMS'].head(20):
        if pd.notna(terms_str):
            top_terms.extend(terms_str.split(';'))
    
    term_counts = Counter(top_terms)
    top_5_terms = [term for term, _ in term_counts.most_common(5)]
    
    summary = {
        'id': int(cluster_id),
        'size': int(mask.sum()),
        'label': '; '.join(top_5_terms),
        'top_ic': cluster_grants['IC_NAME'].mode()[0] if len(cluster_grants) > 0 else 'Unknown',
        'avg_cost': float(cluster_grants['TOTAL_COST'].mean()),
        'year_range': f"{cluster_grants['FY'].min()}-{cluster_grants['FY'].max()}"
    }
    cluster_summaries.append(summary)

# Save cluster summaries
with open('cluster_summaries_hdbscan.json', 'w') as f:
    json.dump(cluster_summaries, f, indent=2)

print(f"\n{'='*60}")
print("COMPARISON WITH K-MEANS (K=100)")
print(f"{'='*60}")

# Load K-means results for comparison
try:
    df_kmeans = pd.read_csv('grant_data_with_clusters.csv')
    
    print("\n| Metric | K-means (K=100) | HDBSCAN |")
    print("|--------|-----------------|---------|")
    print(f"| Number of clusters | 100 | {n_clusters} |")
    print(f"| Avg cluster size | {len(df_kmeans)/100:.0f} | {(len(df)-n_noise)/n_clusters:.0f} |")
    print(f"| Outliers/Noise | 0 (forced) | {n_noise:,} ({100*n_noise/len(df):.1f}%) |")
    print(f"| Silhouette score | 0.039 | {silhouette:.4f} |")
    print(f"| Soft clustering | No | Yes |")
    print(f"| Grants in multiple clusters | 0 | {multi_cluster_grants:,} |")
    
except FileNotFoundError:
    print("K-means results not found for comparison")

print(f"\n{'='*60}")
print("FILES CREATED")
print(f"{'='*60}")
print("✓ grant_data_hdbscan.csv - Full dataset with HDBSCAN labels")
print("✓ cluster_labels_hdbscan.npy - Cluster assignments")
print("✓ soft_memberships_hdbscan.npy - Soft cluster probabilities")
print("✓ umap_coords_hdbscan.npy - UMAP coordinates")
print("✓ cluster_summaries_hdbscan.json - Cluster metadata")

print("\n💡 NEXT STEPS:")
print("1. Compare visualizations: K-means vs HDBSCAN")
print("2. Examine grants with multiple cluster memberships")
print("3. Analyze noise points (grants not fitting any cluster)")
print("4. Consider tuning min_cluster_size (50-200) for different granularity")

print("\nDone!")
