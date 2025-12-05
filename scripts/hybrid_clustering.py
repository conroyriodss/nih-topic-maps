#!/usr/bin/env python3
"""
Hybrid Clustering: PubMedBERT + RCDC Categories
Combines semantic embeddings with NIH category data
"""
import pandas as pd
import numpy as np
from google.cloud import bigquery
from sklearn.cluster import KMeans
from sklearn.preprocessing import MultiLabelBinarizer, StandardScaler, OneHotEncoder
from sklearn.metrics import silhouette_score
import json
from collections import Counter
import time

# Configuration
PROJECT_ID = 'od-cl-odss-conroyri-f75a'
N_CLUSTERS = 100
WEIGHT_EMBEDDING = 0.70
WEIGHT_RCDC = 0.20
WEIGHT_IC = 0.10

print("=" * 60)
print("HYBRID CLUSTERING: PubMedBERT + RCDC + IC")
print("=" * 60)

# Step 1: Load embeddings
print("\n[1/6] Loading PubMedBERT embeddings...")
start = time.time()
df = pd.read_parquet('gs://od-cl-odss-conroyri-nih-embeddings/sample/embeddings_pubmedbert_50k.parquet')
embeddings = np.stack(df['embedding'].values)
print(f"  Loaded {len(df):,} grants with {embeddings.shape[1]}-dim embeddings in {time.time()-start:.1f}s")
print(f"  Columns: {df.columns.tolist()}")

# Step 2: Get RCDC categories from BigQuery using APPLICATION_ID
print("\n[2/6] Fetching RCDC categories from BigQuery...")
start = time.time()
client = bigquery.Client(project=PROJECT_ID)

# Get APPLICATION_IDs from embedding sample
app_ids = df['APPLICATION_ID'].astype(int).tolist()

# Query for categories - use APPLICATION_ID to match
query = """
SELECT 
  CAST(APPLICATION_ID AS INT64) as APPLICATION_ID,
  NIH_SPENDING_CATS,
  PROJECT_TERMS,
  CORE_PROJECT_NUM
FROM `od-cl-odss-conroyri-f75a.nih_processed.projects`
WHERE CAST(APPLICATION_ID AS INT64) IN UNNEST(@app_ids)
"""
job_config = bigquery.QueryJobConfig(
    query_parameters=[
        bigquery.ArrayQueryParameter("app_ids", "INT64", app_ids)
    ]
)
category_df = client.query(query, job_config=job_config).to_dataframe()
print(f"  Fetched {len(category_df):,} rows in {time.time()-start:.1f}s")

# Merge with embedding df
df['APPLICATION_ID'] = df['APPLICATION_ID'].astype(int)
category_df['APPLICATION_ID'] = category_df['APPLICATION_ID'].astype(int)
df = df.merge(category_df, on='APPLICATION_ID', how='left')
print(f"  Merged: {df['NIH_SPENDING_CATS'].notna().sum():,} grants have RCDC categories")

# Step 3: Process RCDC categories
print("\n[3/6] Processing RCDC categories...")
def parse_categories(cat_string):
    if pd.isna(cat_string) or cat_string == '':
        return []
    return [c.strip() for c in str(cat_string).split(';') if c.strip()]

df['rcdc_list'] = df['NIH_SPENDING_CATS'].apply(parse_categories)

# Get all unique RCDC categories
all_rcdc = set()
for cats in df['rcdc_list']:
    all_rcdc.update(cats)
print(f"  Found {len(all_rcdc)} unique RCDC categories")

# Multi-label binarize
if len(all_rcdc) > 0:
    mlb_rcdc = MultiLabelBinarizer(classes=sorted(all_rcdc))
    rcdc_encoded = mlb_rcdc.fit_transform(df['rcdc_list'])
    print(f"  RCDC matrix shape: {rcdc_encoded.shape}")
else:
    print("  WARNING: No RCDC categories found, using zeros")
    rcdc_encoded = np.zeros((len(df), 1))

# Step 4: Process IC codes
print("\n[4/6] Processing IC codes...")
df['IC_NAME'] = df['IC_NAME'].fillna('UNKNOWN')
unique_ics = df['IC_NAME'].unique()
print(f"  Found {len(unique_ics)} unique ICs")

# One-hot encode IC
ic_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
ic_encoded = ic_encoder.fit_transform(df[['IC_NAME']])
print(f"  IC matrix shape: {ic_encoded.shape}")

# Step 5: Create hybrid feature matrix
print("\n[5/6] Creating hybrid feature matrix...")
print(f"  Weights: Embedding={WEIGHT_EMBEDDING}, RCDC={WEIGHT_RCDC}, IC={WEIGHT_IC}")

# Normalize embeddings
scaler = StandardScaler()
embeddings_scaled = scaler.fit_transform(embeddings)

# Scale RCDC and IC to similar magnitude as embeddings
rcdc_scaled = rcdc_encoded * np.sqrt(embeddings.shape[1] / max(rcdc_encoded.shape[1], 1))
ic_scaled = ic_encoded * np.sqrt(embeddings.shape[1] / max(ic_encoded.shape[1], 1))

# Combine with weights
hybrid_features = np.hstack([
    WEIGHT_EMBEDDING * embeddings_scaled,
    WEIGHT_RCDC * rcdc_scaled,
    WEIGHT_IC * ic_scaled
])
print(f"  Hybrid feature matrix: {hybrid_features.shape}")

# Step 6: Cluster
print(f"\n[6/6] Clustering with K={N_CLUSTERS}...")
start = time.time()
kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
labels = kmeans.fit_predict(hybrid_features)
print(f"  Clustering completed in {time.time()-start:.1f}s")

# Evaluate
print("\n" + "=" * 60)
print("EVALUATION")
print("=" * 60)

# Silhouette score (sample for speed)
sample_size = min(10000, len(hybrid_features))
sample_idx = np.random.choice(len(hybrid_features), sample_size, replace=False)
silhouette = silhouette_score(hybrid_features[sample_idx], labels[sample_idx])
print(f"Silhouette Score: {silhouette:.4f}")

# Cluster size distribution
unique, counts = np.unique(labels, return_counts=True)
print(f"Cluster sizes: min={counts.min()}, max={counts.max()}, mean={counts.mean():.0f}")
print(f"Tiny clusters (<50): {(counts < 50).sum()}")

# IC mixing per cluster
print("\nIC Mixing Analysis:")
df['cluster'] = labels
ic_per_cluster = df.groupby('cluster')['IC_NAME'].nunique()
print(f"  Mean ICs per cluster: {ic_per_cluster.mean():.1f}")
print(f"  Max ICs per cluster: {ic_per_cluster.max()}")
print(f"  Clusters with >30 ICs: {(ic_per_cluster > 30).sum()}")

# Generate topic labels from RCDC
print("\nGenerating topic labels from RCDC categories...")
topic_labels = {}
for cluster_id in range(N_CLUSTERS):
    cluster_mask = labels == cluster_id
    cluster_rcdc = df.loc[cluster_mask, 'rcdc_list'].tolist()
    
    # Flatten and count
    all_terms = []
    for terms in cluster_rcdc:
        all_terms.extend(terms)
    
    if all_terms:
        top_terms = Counter(all_terms).most_common(3)
        label = ' | '.join([t[0] for t in top_terms])
    else:
        # Fall back to project title keywords
        label = f'Topic {cluster_id}'
    
    topic_labels[cluster_id] = label

# Show sample labels
print("\nSample topic labels:")
for i in range(min(15, N_CLUSTERS)):
    count = (labels == i).sum()
    print(f"  Cluster {i:2d} ({count:4d} grants): {topic_labels[i][:60]}")

# Save results
print("\n" + "=" * 60)
print("SAVING RESULTS")
print("=" * 60)

# Save cluster assignments
df['topic'] = labels
df['topic_label'] = df['topic'].map(topic_labels)
df[['APPLICATION_ID', 'CORE_PROJECT_NUM', 'topic', 'topic_label', 'IC_NAME', 'FISCAL_YEAR']].to_csv(
    'hybrid_cluster_assignments.csv', index=False)
print("  Saved: hybrid_cluster_assignments.csv")

# Save topic labels
with open('hybrid_topic_labels.json', 'w') as f:
    json.dump(topic_labels, f, indent=2)
print("  Saved: hybrid_topic_labels.json")

# Save evaluation metrics
metrics = {
    'n_clusters': N_CLUSTERS,
    'silhouette_score': float(silhouette),
    'min_cluster_size': int(counts.min()),
    'max_cluster_size': int(counts.max()),
    'mean_cluster_size': float(counts.mean()),
    'tiny_clusters': int((counts < 50).sum()),
    'mean_ics_per_cluster': float(ic_per_cluster.mean()),
    'max_ics_per_cluster': int(ic_per_cluster.max()),
    'rcdc_coverage': float(df['NIH_SPENDING_CATS'].notna().mean()),
    'weights': {
        'embedding': WEIGHT_EMBEDDING,
        'rcdc': WEIGHT_RCDC,
        'ic': WEIGHT_IC
    }
}
with open('hybrid_clustering_metrics.json', 'w') as f:
    json.dump(metrics, f, indent=2)
print("  Saved: hybrid_clustering_metrics.json")

print("\n" + "=" * 60)
print("HYBRID CLUSTERING COMPLETE!")
print("=" * 60)
