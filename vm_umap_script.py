#!/usr/bin/env python3
"""
Run UMAP on 50k clustered grants
"""
import pandas as pd
import numpy as np
from google.cloud import storage
import umap.umap_ as umap
import time

PROJECT_ID = 'od-cl-odss-conroyri-f75a'
BUCKET = 'od-cl-odss-conroyri-nih-embeddings'

print("=" * 80)
print("ADDING UMAP COORDINATES TO 50K GRANTS")
print("=" * 80)

# Download from GCS
print("\n[1/4] Downloading data from GCS...")
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET)

blob = bucket.blob('hierarchical_50k_clustered.csv')
blob.download_to_filename('hierarchical_50k_clustered.csv')

blob = bucket.blob('embeddings_50k_sample.parquet')
blob.download_to_filename('embeddings_50k_sample.parquet')

# Load data
print("\n[2/4] Loading data...")
df = pd.read_csv('hierarchical_50k_clustered.csv')
emb_df = pd.read_parquet('embeddings_50k_sample.parquet')
emb_df['APPLICATION_ID'] = emb_df['APPLICATION_ID'].astype('int64')

df = df.merge(emb_df[['APPLICATION_ID', 'embedding']], on='APPLICATION_ID', how='left')
embeddings = np.stack(df['embedding'].values)
print(f"  {len(df):,} grants with {embeddings.shape[1]}-dim embeddings")

# Apply UMAP
print("\n[3/4] Running UMAP...")
print("  This will take 10-15 minutes...")

start = time.time()

reducer = umap.UMAP(
    n_neighbors=15,
    n_components=2,
    min_dist=0.1,
    metric='cosine',
    random_state=42,
    verbose=True,
    low_memory=False,
    n_jobs=-1
)

coords = reducer.fit_transform(embeddings)

elapsed = time.time() - start
print(f"\n  UMAP complete in {elapsed/60:.1f} minutes")
print(f"  X range: [{coords[:, 0].min():.2f}, {coords[:, 0].max():.2f}]")
print(f"  Y range: [{coords[:, 1].min():.2f}, {coords[:, 1].max():.2f}]")

# Save
print("\n[4/4] Saving and uploading...")
df['umap_x'] = coords[:, 0]
df['umap_y'] = coords[:, 1]

output = df[['APPLICATION_ID', 'PROJECT_TITLE', 'IC_NAME', 'FY', 'TOTAL_COST',
             'domain', 'domain_label', 'topic', 'subtopic', 'umap_x', 'umap_y']].copy()

output.to_csv('hierarchical_50k_with_umap.csv', index=False)

blob = bucket.blob('hierarchical_50k_with_umap.csv')
blob.upload_from_filename('hierarchical_50k_with_umap.csv')

print("\n" + "=" * 80)
print("UMAP COMPLETE!")
print("=" * 80)
print(f"\n✅ Uploaded to gs://{BUCKET}/hierarchical_50k_with_umap.csv")
print("\nNext: Download in Cloud Shell and create visualization")
print("=" * 80)
