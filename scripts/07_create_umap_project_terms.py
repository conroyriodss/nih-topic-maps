#!/usr/bin/env python3
"""
Generate UMAP visualization for PROJECT_TERMS clustering
Uses existing UMAP coordinates but with new PROJECT_TERMS clusters
"""

import pandas as pd
import numpy as np
import json
import subprocess
from collections import Counter

print("\n" + "="*70)
print("UMAP Visualization for PROJECT_TERMS Clustering")
print("="*70 + "\n")

# Download required files
print("Downloading files from GCS...")
subprocess.run([
    'gsutil', 'cp',
    'gs://od-cl-odss-conroyri-nih-embeddings/sample/embeddings_project_terms_clustered_k100.parquet',
    'data/processed/'
], check=True)

subprocess.run([
    'gsutil', 'cp',
    'gs://od-cl-odss-conroyri-nih-embeddings/sample/umap_coordinates_50k.parquet',
    'data/processed/'
], check=True)

print("Loading data...")
df_clusters = pd.read_parquet('data/processed/embeddings_project_terms_clustered_k100.parquet')
df_umap = pd.read_parquet('data/processed/umap_coordinates_50k.parquet')

print(f"Clustered data: {len(df_clusters):,} grants")
print(f"UMAP coordinates: {len(df_umap):,} points")

# Merge on APPLICATION_ID
print("\nMerging clusters with UMAP coordinates...")
df_merged = df_umap.merge(
    df_clusters[['APPLICATION_ID', 'cluster', 'PROJECT_TERMS', 'IC_NAME', 'FISCAL_YEAR', 'PROJECT_TITLE', 'TOTAL_COST']],
    on='APPLICATION_ID',
    how='inner'
)

print(f"Merged: {len(df_merged):,} grants with coordinates and clusters")

# Generate cluster labels from PROJECT_TERMS
print("\nGenerating cluster labels from PROJECT_TERMS...")
cluster_labels = {}
cluster_stats = {}

for cluster_id in range(100):
    cluster_data = df_merged[df_merged['cluster'] == cluster_id]
    
    if len(cluster_data) == 0:
        continue
    
    # Extract top terms from PROJECT_TERMS
    all_terms = []
    for terms_str in cluster_data['PROJECT_TERMS'].head(50):
        if pd.notna(terms_str):
            terms = str(terms_str).split(';')
            all_terms.extend([t.strip().lower() for t in terms if len(t.strip()) > 3])
    
    # Count term frequencies
    term_counts = Counter(all_terms)
    top_terms = [term for term, count in term_counts.most_common(5)]
    
    # Create label from top terms
    label = ' / '.join(top_terms[:3]) if top_terms else f"Cluster {cluster_id}"
    
    # Calculate stats
    cluster_labels[cluster_id] = label
    cluster_stats[cluster_id] = {
        'size': len(cluster_data),
        'top_ic': cluster_data['IC_NAME'].mode()[0] if len(cluster_data) > 0 else 'Unknown',
        'avg_cost': float(cluster_data['TOTAL_COST'].mean()),
        'year_range': f"{cluster_data['FISCAL_YEAR'].min()}-{cluster_data['FISCAL_YEAR'].max()}"
    }

print(f"Generated labels for {len(cluster_labels)} clusters")

# Create visualization data
print("\nCreating visualization data...")
viz_data = {
    'points': [],
    'clusters': [],
    'metadata': {
        'n_points': len(df_merged),
        'n_clusters': 100,
        'clustering_method': 'K-means on PROJECT_TERMS embeddings',
        'embedding_model': 'PubMedBERT',
        'k': 100
    }
}

# Add points - USE umap_x and umap_y
for idx, row in df_merged.iterrows():
    viz_data['points'].append({
        'x': float(row['umap_x']),
        'y': float(row['umap_y']),
        'cluster': int(row['cluster']),
        'application_id': str(row['APPLICATION_ID']),
        'title': str(row['PROJECT_TITLE'])[:200],
        'ic': str(row['IC_NAME']),
        'year': int(row['FISCAL_YEAR']),
        'cost': float(row['TOTAL_COST']) if pd.notna(row['TOTAL_COST']) else 0
    })

# Add cluster info
for cluster_id, label in cluster_labels.items():
    stats = cluster_stats[cluster_id]
    cluster_points = df_merged[df_merged['cluster'] == cluster_id]
    
    viz_data['clusters'].append({
        'id': int(cluster_id),
        'label': label,
        'size': stats['size'],
        'top_ic': stats['top_ic'],
        'avg_cost': stats['avg_cost'],
        'year_range': stats['year_range'],
        'center_x': float(cluster_points['umap_x'].mean()),
        'center_y': float(cluster_points['umap_y'].mean())
    })

# Save visualization data
print("\nSaving visualization data...")
output_file = 'data/processed/viz_data_project_terms_k100.json'
with open(output_file, 'w') as f:
    json.dump(viz_data, f)

print(f"Saved to: {output_file}")
print(f"File size: {len(json.dumps(viz_data)) / 1024 / 1024:.1f} MB")

# Upload to GCS
print("\nUploading to GCS...")
subprocess.run([
    'gsutil', 'cp', output_file,
    'gs://od-cl-odss-conroyri-nih-embeddings/sample/'
], check=True)

print("\n" + "="*70)
print("VISUALIZATION DATA COMPLETE")
print("="*70)
print(f"\nPoints: {len(viz_data['points']):,}")
print(f"Clusters: {len(viz_data['clusters'])}")
print(f"\nSample cluster labels:")
for i in range(min(10, len(viz_data['clusters']))):
    cluster = viz_data['clusters'][i]
    print(f"  {cluster['id']}: {cluster['label']} ({cluster['size']} grants)")

print(f"\nNext step: Create interactive HTML visualization")
