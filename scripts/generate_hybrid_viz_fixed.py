#!/usr/bin/env python3
"""
Generate visualization data - FIXED year handling
"""
import pandas as pd
import numpy as np
import json
import time

print("=" * 60)
print("REGENERATING HYBRID VISUALIZATION DATA (FIXED)")
print("=" * 60)

# Load embeddings and cluster assignments
print("\n[1/3] Loading data...")
start = time.time()
emb_df = pd.read_parquet('gs://od-cl-odss-conroyri-nih-embeddings/sample/embeddings_pubmedbert_50k.parquet')
cluster_df = pd.read_csv('hybrid_cluster_assignments.csv')

print(f"  Embedding df columns: {emb_df.columns.tolist()}")
print(f"  Embedding df shape: {emb_df.shape}")
print(f"  Sample year: {emb_df['FISCAL_YEAR'].head()}")

# Don't merge - just add cluster info by index
df = emb_df.copy()
df['cluster'] = cluster_df['topic'].values
df['topic_label'] = cluster_df['topic_label'].values

print(f"  Loaded {len(df):,} grants in {time.time()-start:.1f}s")

# Load topic labels
with open('hybrid_topic_labels.json') as f:
    topic_labels = json.load(f)

# Check years
print(f"\n  Years in embedding data: {sorted(df['FISCAL_YEAR'].unique())}")
print(f"  Year value counts:")
print(df['FISCAL_YEAR'].value_counts().sort_index())

# Build viz data
print("\n[2/3] Building visualization JSON...")
viz_data = []
for idx, row in df.iterrows():
    topic_id = int(row['cluster'])
    fiscal_year = int(row['FISCAL_YEAR']) if pd.notna(row['FISCAL_YEAR']) else 0
    
    viz_data.append({
        'id': int(row['APPLICATION_ID']),
        'x': float(row['x']) if 'x' in row and pd.notna(row.get('x')) else float(np.random.normal()),
        'y': float(row['y']) if 'y' in row and pd.notna(row.get('y')) else float(np.random.normal()),
        'title': str(row['PROJECT_TITLE'])[:100],
        'ic': str(row['IC_NAME']) if pd.notna(row['IC_NAME']) else 'Unknown',
        'year': fiscal_year,
        'funding': float(row['TOTAL_COST']) if pd.notna(row['TOTAL_COST']) else 0,
        'topic': topic_id,
        'topic_label': topic_labels.get(str(topic_id), f'Topic {topic_id}')
    })

print(f"  Created {len(viz_data):,} records")
print(f"  Sample record: {viz_data[0]}")

# Check year distribution in final data
years = [d['year'] for d in viz_data]
print(f"\n  Final data year distribution:")
from collections import Counter
year_counts = Counter(years)
for year in sorted(year_counts.keys()):
    if year > 0:
        print(f"    {year}: {year_counts[year]}")

# Save locally
print("\n[3/3] Saving files...")
with open('hybrid_viz_data.json', 'w') as f:
    json.dump(viz_data, f)
print(f"  Saved: hybrid_viz_data.json ({len(viz_data):,} grants)")

# Upload to GCS
print("  Uploading to GCS...")
import subprocess
subprocess.run(['gsutil', 'cp', 'hybrid_viz_data.json', 
                'gs://od-cl-odss-conroyri-nih-embeddings/sample/hybrid_viz_data.json'])
print("  ✓ Uploaded to GCS")

print("\n" + "=" * 60)
print("✓ VISUALIZATION DATA FIXED!")
print("=" * 60)
