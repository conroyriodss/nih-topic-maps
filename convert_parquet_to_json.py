#!/usr/bin/env python3
"""
Convert Parquet data to JSON for web visualization
"""

import pandas as pd
import json
import subprocess

print("Loading data from GCS...")

# Download files
subprocess.run(['gsutil', 'cp', 
    'gs://od-cl-odss-conroyri-nih-embeddings/sample/umap_coordinates_50k.parquet',
    'gs://od-cl-odss-conroyri-nih-embeddings/sample/topics_final_75.parquet',
    'data/processed/'], check=True)

# Load parquet files
print("Reading Parquet files...")
umap_df = pd.read_parquet('data/processed/umap_coordinates_50k.parquet')
topics_df = pd.read_parquet('data/processed/topics_final_75.parquet')

# Merge
df = umap_df.merge(topics_df[['APPLICATION_ID', 'PROJECT_TITLE', 'FISCAL_YEAR', 'IC_NAME', 'TOTAL_COST']], 
                   on='APPLICATION_ID', how='left')

print(f"Loaded {len(df):,} grants")

# Create JSON structure
data_json = []
for _, row in df.iterrows():
    data_json.append({
        'id': row['APPLICATION_ID'],
        'x': float(row['umap_x']),
        'y': float(row['umap_y']),
        'ic': row['IC_NAME'],
        'year': int(row['FISCAL_YEAR']),
        'topic': int(row['topic']),
        'topic_label': row['topic_label'],
        'title': row['PROJECT_TITLE'][:100],  # Truncate for size
        'funding': float(row['TOTAL_COST'])
    })

print(f"Converting to JSON...")
output_file = 'data/processed/viz_data.json'
with open(output_file, 'w') as f:
    json.dump(data_json, f)

print(f"✓ Saved {len(data_json):,} records to {output_file}")

# Upload to GCS
print("Uploading to GCS...")
subprocess.run(['gsutil', 'cp', output_file,
    'gs://od-cl-odss-conroyri-nih-embeddings/sample/'], check=True)

# Get file size
import os
size_mb = os.path.getsize(output_file) / 1024 / 1024
print(f"✓ File size: {size_mb:.1f} MB")
print(f"✓ Available at: https://storage.googleapis.com/od-cl-odss-conroyri-nih-embeddings/sample/viz_data.json")
