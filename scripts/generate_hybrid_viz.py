#!/usr/bin/env python3
"""
Generate visualization data with hybrid clusters and RCDC labels
"""
import pandas as pd
import numpy as np
import umap
import json
import time

print("=" * 60)
print("GENERATING HYBRID VISUALIZATION DATA")
print("=" * 60)

# Load embeddings and cluster assignments
print("\n[1/4] Loading data...")
start = time.time()
emb_df = pd.read_parquet('gs://od-cl-odss-conroyri-nih-embeddings/sample/embeddings_pubmedbert_50k.parquet')
cluster_df = pd.read_csv('hybrid_cluster_assignments.csv')

print(f"  Embedding columns: {emb_df.columns.tolist()}")
print(f"  Cluster columns: {cluster_df.columns.tolist()}")

# Merge
emb_df['APPLICATION_ID'] = emb_df['APPLICATION_ID'].astype(int)
cluster_df['APPLICATION_ID'] = cluster_df['APPLICATION_ID'].astype(int)
df = emb_df.merge(cluster_df, on='APPLICATION_ID', how='left', suffixes=('_emb', '_clust'))

print(f"  Loaded {len(df):,} grants in {time.time()-start:.1f}s")
print(f"  Merged columns: {df.columns.tolist()}")

# Load topic labels
with open('hybrid_topic_labels.json') as f:
    topic_labels = json.load(f)

# [2/4] Run UMAP with better parameters
print("\n[2/4] Running UMAP (n_neighbors=30, min_dist=0.0)...")
start = time.time()
embeddings = np.stack(df['embedding'].values)

reducer = umap.UMAP(
    n_neighbors=30,
    min_dist=0.0,
    metric='cosine',
    random_state=42,
    verbose=True
)
coords = reducer.fit_transform(embeddings)
print(f"  UMAP completed in {time.time()-start:.1f}s")

df['x'] = coords[:, 0]
df['y'] = coords[:, 1]

# [3/4] Build viz data
print("\n[3/4] Building visualization JSON...")
viz_data = []
for idx, row in df.iterrows():
    topic_id = int(row['topic']) if pd.notna(row['topic']) else 0
    
    # Get IC name - could be from either column
    ic_name = row.get('IC_NAME_emb')
    if pd.isna(ic_name):
        ic_name = row.get('IC_NAME_clust')
    ic_name = str(ic_name) if pd.notna(ic_name) else 'Unknown'
    
    # Get fiscal year - from embedding df
    fiscal_year = row.get('FISCAL_YEAR')
    fiscal_year = int(fiscal_year) if pd.notna(fiscal_year) else 0
    
    # Get total cost - from embedding df
    total_cost = row.get('TOTAL_COST')
    total_cost = float(total_cost) if pd.notna(total_cost) else 0
    
    viz_data.append({
        'id': int(row['APPLICATION_ID']),
        'x': float(row['x']),
        'y': float(row['y']),
        'title': str(row['PROJECT_TITLE'])[:100],
        'ic': ic_name,
        'year': fiscal_year,
        'funding': total_cost,
        'topic': topic_id,
        'topic_label': topic_labels.get(str(topic_id), f'Topic {topic_id}')
    })

# [4/4] Save
print("\n[4/4] Saving files...")
with open('hybrid_viz_data.json', 'w') as f:
    json.dump(viz_data, f)
print(f"  Saved: hybrid_viz_data.json ({len(viz_data):,} grants)")

# Also save to GCS
print("  Uploading to GCS...")
import subprocess
result = subprocess.run(['gsutil', 'cp', 'hybrid_viz_data.json', 
                'gs://od-cl-odss-conroyri-nih-embeddings/sample/hybrid_viz_data.json'],
                capture_output=True, text=True)
if result.returncode == 0:
    print("  ✓ Uploaded to GCS")
else:
    print(f"  Note: GCS upload skipped ({result.returncode})")

# Summary stats
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Total grants: {len(viz_data):,}")
print(f"Topics: {len(topic_labels)}")
print(f"X range: [{df['x'].min():.2f}, {df['x'].max():.2f}]")
print(f"Y range: [{df['y'].min():.2f}, {df['y'].max():.2f}]")
print(f"\nReady for visualization!")
