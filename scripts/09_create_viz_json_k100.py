#!/usr/bin/env python3
"""
Create production visualization JSON for K=100 PROJECT_TERMS clustering
Uses new UMAP coordinates optimized for cluster visualization
"""

import pandas as pd
import numpy as np
import json
from collections import Counter
from pathlib import Path

print("\n" + "="*80)
print("CREATING PRODUCTION VISUALIZATION DATA")
print("Using NEW UMAP coordinates optimized for K=100 clusters")
print("="*80 + "\n")

# Load data
print("1. Loading data files...")

# UMAP coordinates (just generated)
umap_file = 'data/processed/umap_project_terms_k100.parquet'
if not Path(umap_file).exists():
    print(f"❌ UMAP file not found: {umap_file}")
    print("   Run: python3 scripts/08_regenerate_umap_project_terms.py")
    exit(1)

df_umap = pd.read_parquet(umap_file)
print(f"   ✓ UMAP coordinates: {len(df_umap):,} points")

# Clustered embeddings (for metadata)
cluster_file = 'data/processed/embeddings_project_terms_clustered_k100.parquet'
if not Path(cluster_file).exists():
    print(f"❌ Cluster file not found: {cluster_file}")
    print("   Run: gsutil cp gs://od-cl-odss-conroyri-nih-embeddings/sample/embeddings_project_terms_clustered_k100.parquet data/processed/")
    exit(1)

df_clusters = pd.read_parquet(cluster_file)
print(f"   ✓ Clustered data: {len(df_clusters):,} grants")

# Merge
print("\n2. Merging UMAP coordinates with cluster assignments...")
df_merged = df_umap.merge(
    df_clusters[['APPLICATION_ID', 'cluster', 'PROJECT_TERMS', 'IC_NAME', 
                 'FISCAL_YEAR', 'PROJECT_TITLE', 'TOTAL_COST']],
    on='APPLICATION_ID',
    how='inner'
)
print(f"   ✓ Merged: {len(df_merged):,} grants")

if len(df_merged) < len(df_umap) * 0.95:
    print(f"   ⚠️  Warning: Lost {len(df_umap) - len(df_merged)} grants in merge")

# Generate cluster labels
print("\n3. Generating cluster labels from PROJECT_TERMS...")
cluster_info = {}

for cluster_id in range(100):
    cluster_data = df_merged[df_merged['cluster'] == cluster_id]
    
    if len(cluster_data) == 0:
        print(f"   ⚠️  Cluster {cluster_id}: EMPTY")
        continue
    
    # Extract all terms for this cluster
    all_terms = []
    for terms_str in cluster_data['PROJECT_TERMS'].head(100):  # Sample first 100
        if pd.notna(terms_str):
            terms = str(terms_str).split(';')
            all_terms.extend([t.strip().lower() for t in terms if len(t.strip()) > 3])
    
    # Count term frequencies
    term_counts = Counter(all_terms)
    top_terms = term_counts.most_common(20)
    
    # Generate readable label
    if len(top_terms) >= 3:
        label = ' / '.join([term for term, count in top_terms[:3]])
    elif len(top_terms) > 0:
        label = ' / '.join([term for term, count in top_terms])
    else:
        label = f"Topic {cluster_id}"
    
    # Calculate cluster statistics
    ic_counts = cluster_data['IC_NAME'].value_counts()
    top_ic = ic_counts.index[0] if len(ic_counts) > 0 else 'Unknown'
    
    cluster_info[cluster_id] = {
        'id': int(cluster_id),
        'label': label,
        'size': len(cluster_data),
        'top_terms': [term for term, count in top_terms[:5]],
        'top_ic': top_ic,
        'ic_count': len(ic_counts),
        'year_range': f"{int(cluster_data['FISCAL_YEAR'].min())}-{int(cluster_data['FISCAL_YEAR'].max())}",
        'total_cost': float(cluster_data['TOTAL_COST'].sum()),
        'avg_cost': float(cluster_data['TOTAL_COST'].mean()),
        'center_x': float(cluster_data['umap_x'].mean()),
        'center_y': float(cluster_data['umap_y'].mean())
    }
    
    if cluster_id % 20 == 0:
        print(f"   Processed {cluster_id}/100 clusters...")

print(f"   ✓ Generated labels for {len(cluster_info)} clusters")

# Create visualization data structure
print("\n4. Creating visualization JSON...")

viz_data = {
    'metadata': {
        'created': pd.Timestamp.now().isoformat(),
        'n_points': len(df_merged),
        'n_clusters': 100,
        'method': 'K-means on PROJECT_TERMS embeddings',
        'embedding_model': 'PubMedBERT',
        'umap_params': {
            'n_neighbors': 30,
            'min_dist': 0.1,
            'metric': 'cosine',
            'random_state': 42
        },
        'quality_metrics': {
            'silhouette_score': 0.0391,
            'calinski_harabasz': 466.06,
            'davies_bouldin': 2.95
        }
    },
    'points': [],
    'clusters': []
}

# Add all points
print("   Adding grant points...")
for idx, row in df_merged.iterrows():
    point = {
        'x': float(row['umap_x']),
        'y': float(row['umap_y']),
        'cluster': int(row['cluster']),
        'application_id': str(row['APPLICATION_ID']),
        'title': str(row['PROJECT_TITLE'])[:200] if pd.notna(row['PROJECT_TITLE']) else '',
        'ic': str(row['IC_NAME']),
        'year': int(row['FISCAL_YEAR']),
        'cost': float(row['TOTAL_COST']) if pd.notna(row['TOTAL_COST']) else 0
    }
    viz_data['points'].append(point)
    
    if (idx + 1) % 10000 == 0:
        print(f"   Added {idx + 1:,} points...")

# Add cluster metadata
print("   Adding cluster metadata...")
for cluster_id, info in sorted(cluster_info.items()):
    viz_data['clusters'].append(info)

# Save
print("\n5. Saving visualization data...")
output_file = 'data/processed/viz_data_project_terms_k100_final.json'
with open(output_file, 'w') as f:
    json.dump(viz_data, f, separators=(',', ':'))  # Compact format

file_size = Path(output_file).stat().st_size / (1024 * 1024)
print(f"   ✓ Saved to: {output_file}")
print(f"   ✓ File size: {file_size:.2f} MB")

# Upload to GCS
print("\n6. Uploading to GCS...")
import subprocess
result = subprocess.run([
    'gsutil', 'cp', output_file,
    'gs://od-cl-odss-conroyri-nih-embeddings/sample/'
], capture_output=True, text=True)

if result.returncode == 0:
    print("   ✓ Upload successful")
else:
    print(f"   ⚠️  Upload failed: {result.stderr}")
    print("   Manual upload: gsutil cp", output_file, "gs://od-cl-odss-conroyri-nih-embeddings/sample/")

# Print summary
print("\n" + "="*80)
print("VISUALIZATION DATA COMPLETE")
print("="*80)
print(f"\nPoints: {len(viz_data['points']):,}")
print(f"Clusters: {len(viz_data['clusters'])}")
print(f"File size: {file_size:.2f} MB")
print(f"\nPublic URL (after setting permissions):")
print(f"  https://storage.googleapis.com/od-cl-odss-conroyri-nih-embeddings/sample/viz_data_project_terms_k100_final.json")

print(f"\n📊 Sample cluster labels (first 10):")
for i in range(min(10, len(viz_data['clusters']))):
    cluster = viz_data['clusters'][i]
    print(f"  {cluster['id']:3d}. {cluster['label'][:60]:60s} ({cluster['size']:5d} grants)")

print(f"\n📈 Cluster size statistics:")
sizes = [c['size'] for c in viz_data['clusters']]
print(f"  Mean: {np.mean(sizes):.1f} grants")
print(f"  Median: {np.median(sizes):.1f} grants")
print(f"  Min: {np.min(sizes)} grants")
print(f"  Max: {np.max(sizes)} grants")

print(f"\n🎯 Next steps:")
print(f"  1. Create/update interactive HTML to use this data file")
print(f"  2. Test locally: python3 -m http.server 8000")
print(f"  3. Deploy HTML to GCS")
print(f"  4. Set public read permissions")
print(f"  5. Update index.html with new link")

print("\n" + "="*80)
print("Ready for deployment: Interactive visualization HTML")
print("="*80 + "\n")
