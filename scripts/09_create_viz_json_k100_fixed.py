#!/usr/bin/env python3
"""
Create production visualization JSON for K=100 PROJECT_TERMS clustering
Uses UMAP file which already contains all metadata
"""

import pandas as pd
import numpy as np
import json
from collections import Counter
from pathlib import Path

print("\n" + "="*80)
print("CREATING PRODUCTION VISUALIZATION DATA")
print("Using UMAP file with all metadata included")
print("="*80 + "\n")

# Load UMAP data (already has cluster, ic, year, title, cost)
print("1. Loading UMAP data...") 
umap_file = 'data/processed/umap_project_terms_k100.parquet'
df = pd.read_parquet(umap_file)
print(f"   ✓ Loaded: {len(df):,} points")
print(f"   ✓ Columns: {list(df.columns)}")

# Load clustered embeddings for PROJECT_TERMS
print("\n2. Loading PROJECT_TERMS for label generation...")
cluster_file = 'data/processed/embeddings_project_terms_clustered_k100.parquet'
df_terms = pd.read_parquet(cluster_file)
df = df.merge(df_terms[['APPLICATION_ID', 'PROJECT_TERMS']], on='APPLICATION_ID', how='left')
print(f"   ✓ Added PROJECT_TERMS to {len(df):,} grants")

# Generate cluster labels
print("\n3. Generating cluster labels from PROJECT_TERMS...")
cluster_info = {}

for cluster_id in range(100):
    cluster_data = df[df['cluster'] == cluster_id]
    
    if len(cluster_data) == 0:
        continue
    
    # Extract terms
    all_terms = []
    for terms_str in cluster_data['PROJECT_TERMS'].head(100):
        if pd.notna(terms_str):
            terms = str(terms_str).split(';')
            all_terms.extend([t.strip().lower() for t in terms if len(t.strip()) > 3])
    
    term_counts = Counter(all_terms)
    top_terms = term_counts.most_common(20)
    
    label = ' / '.join([term for term, count in top_terms[:3]]) if len(top_terms) >= 3 else f"Topic {cluster_id}"
    
    cluster_info[cluster_id] = {
        'id': int(cluster_id),
        'label': label,
        'size': len(cluster_data),
        'top_terms': [term for term, count in top_terms[:5]],
        'top_ic': str(cluster_data['ic'].value_counts().index[0]),
        'ic_count': cluster_data['ic'].nunique(),
        'year_range': f"{int(cluster_data['year'].min())}-{int(cluster_data['year'].max())}",
        'total_cost': float(cluster_data['cost'].sum()),
        'avg_cost': float(cluster_data['cost'].mean()),
        'center_x': float(cluster_data['umap_x'].mean()),
        'center_y': float(cluster_data['umap_y'].mean())
    }
    
    if cluster_id % 20 == 0:
        print(f"   Processed {cluster_id}/100...")

print(f"   ✓ Generated {len(cluster_info)} cluster labels")

# Create viz JSON
print("\n4. Creating visualization JSON...")

viz_data = {
    'metadata': {
        'created': pd.Timestamp.now().isoformat(),
        'n_points': len(df),
        'n_clusters': 100,
        'method': 'K-means on PROJECT_TERMS embeddings',
        'embedding_model': 'PubMedBERT',
        'umap_params': {'n_neighbors': 30, 'min_dist': 0.1, 'metric': 'cosine', 'random_state': 42},
        'quality_metrics': {'silhouette_score': 0.0391, 'calinski_harabasz': 466.06, 'davies_bouldin': 2.95}
    },
    'points': [],
    'clusters': list(cluster_info.values())
}

print("   Adding points...")
for idx, row in df.iterrows():
    viz_data['points'].append({
        'x': float(row['umap_x']),
        'y': float(row['umap_y']),
        'cluster': int(row['cluster']),
        'application_id': str(row['APPLICATION_ID']),
        'title': str(row['title'])[:200] if pd.notna(row['title']) else '',
        'ic': str(row['ic']),
        'year': int(row['year']),
        'cost': float(row['cost']) if pd.notna(row['cost']) else 0
    })
    if (idx + 1) % 10000 == 0:
        print(f"   Added {idx + 1:,} points...")

# Save
print("\n5. Saving...")
output_file = 'data/processed/viz_data_project_terms_k100_final.json'
with open(output_file, 'w') as f:
    json.dump(viz_data, f, separators=(',', ':'))

file_size = Path(output_file).stat().st_size / (1024 * 1024)
print(f"   ✓ Saved: {output_file} ({file_size:.2f} MB)")

# Upload
print("\n6. Uploading to GCS...")
import subprocess
result = subprocess.run(['gsutil', 'cp', output_file, 'gs://od-cl-odss-conroyri-nih-embeddings/sample/'], 
                       capture_output=True, text=True)
print("   ✓ Upload successful" if result.returncode == 0 else f"   ⚠️  {result.stderr}")

print("\n" + "="*80)
print(f"✅ COMPLETE! {len(viz_data['points']):,} points, {len(viz_data['clusters'])} clusters, {file_size:.2f} MB")
print("="*80 + "\n")
