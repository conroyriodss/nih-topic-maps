#!/usr/bin/env python3
"""
Generate final visualization data with coordinates + clusters + years
"""
import pandas as pd
import json
import time

print("=" * 60)
print("GENERATING FINAL HYBRID VISUALIZATION")
print("=" * 60)

# Step 1: Load the original viz data (has x, y, topic)
print("\n[1/3] Loading original visualization data...")
with open('hybrid_viz_data.json') as f:
    viz_data_old = json.load(f)
print(f"  Loaded {len(viz_data_old)} records from viz_data.json")
print(f"  Sample: {viz_data_old[0]}")

# Step 2: Load embedding data for year info
print("\n[2/3] Loading embedding data for years...")
emb_df = pd.read_parquet('gs://od-cl-odss-conroyri-nih-embeddings/sample/embeddings_pubmedbert_50k.parquet')
print(f"  Loaded {len(emb_df)} embeddings")

# Create lookup map from APPLICATION_ID to year
year_map = {}
for idx, row in emb_df.iterrows():
    year_map[int(row['APPLICATION_ID'])] = int(row['FISCAL_YEAR']) if pd.notna(row['FISCAL_YEAR']) else 0

print(f"  Created year map with {len(year_map)} entries")

# Step 3: Merge year data into viz_data
print("\n[3/3] Merging year data into visualization...")
for record in viz_data_old:
    app_id = record['id']
    record['year'] = year_map.get(app_id, 0)

# Check year distribution
from collections import Counter
years = [d['year'] for d in viz_data_old]
year_counts = Counter(years)
print(f"\n  Year distribution in final data:")
for year in sorted(year_counts.keys()):
    if year > 0:
        print(f"    {year}: {year_counts[year]}")

# Save
print("\n  Saving hybrid_viz_data.json...")
with open('hybrid_viz_data.json', 'w') as f:
    json.dump(viz_data_old, f)
print(f"  ✓ Saved {len(viz_data_old)} records")

# Upload
print("\n  Uploading to GCS...")
import subprocess
result = subprocess.run(['gsutil', 'cp', 'hybrid_viz_data.json', 
                'gs://od-cl-odss-conroyri-nih-embeddings/sample/hybrid_viz_data.json'],
                capture_output=True)
if result.returncode == 0:
    print("  ✓ Uploaded to GCS")
else:
    print(f"  Error uploading: {result.stderr}")

print("\n" + "=" * 60)
print("✓ FINAL VISUALIZATION DATA READY!")
print("=" * 60)
print("\nSample record:")
print(json.dumps(viz_data_old[0], indent=2))
