#!/usr/bin/env python3
"""
Apply clustering and prepare data for UMAP visualization
Uses hybrid hierarchical clustering with K=100
"""
import pandas as pd
import numpy as np
from google.cloud import bigquery
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.preprocessing import StandardScaler, MultiLabelBinarizer, OneHotEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
import umap
import json
import time

PROJECT_ID = 'od-cl-odss-conroyri-f75a'

# Use parameters from previous run
WEIGHT_EMBEDDING = 0.50
WEIGHT_RCDC = 0.15
WEIGHT_IC = 0.10
WEIGHT_TERMS = 0.25
K = 100  # Middle ground between 50-150

STOP_TERMS = {
    'project', 'research', 'study', 'grant', 'core', 'program', 'center',
    'development', 'training', 'support', 'service', 'year', 'years',
    'aim', 'specific', 'aims', 'proposed', 'proposal', 'application',
    'data', 'analysis', 'method', 'approach', 'technique', 'tool',
    'system', 'model', 'process', 'investigation', 'evaluation',
    'health', 'disease', 'patient', 'clinical', 'treatment', 'therapy',
    'human', 'tissue', 'cell', 'cells', 'protein', 'proteins', 'gene'
}

print("=" * 70)
print("APPLY CLUSTERING & PREPARE VISUALIZATION")
print("=" * 70)

# Load embeddings
print("\n[1/6] Loading embeddings...")
df = pd.read_parquet('embeddings_25k_subsample.parquet')
embeddings = np.stack(df['embedding'].values)
df['APPLICATION_ID'] = df['APPLICATION_ID'].astype('int64')
print(f"  {len(df):,} grants loaded")

# Fetch metadata
print("\n[2/6] Fetching metadata...")
client = bigquery.Client(project=PROJECT_ID)
app_ids = df['APPLICATION_ID'].tolist()

query = """
SELECT 
  CAST(APPLICATION_ID AS INT64) as APPLICATION_ID,
  NIH_SPENDING_CATS,
  PROJECT_TERMS,
  IC_NAME,
  PROJECT_TITLE,
  ABSTRACT_TEXT,
  FY,
  TOTAL_COST
FROM `od-cl-odss-conroyri-f75a.nih_exporter.projects`
WHERE CAST(APPLICATION_ID AS INT64) IN UNNEST(@app_ids)
"""
job_config = bigquery.QueryJobConfig(
    query_parameters=[bigquery.ArrayQueryParameter("app_ids", "INT64", app_ids)]
)
metadata_df = client.query(query, job_config=job_config).to_dataframe()
metadata_df['APPLICATION_ID'] = metadata_df['APPLICATION_ID'].astype('int64')

# Merge
cols_to_drop = [c for c in metadata_df.columns if c in df.columns and c != 'APPLICATION_ID']
if cols_to_drop:
    df = df.drop(columns=cols_to_drop)
df = df.merge(metadata_df, on='APPLICATION_ID', how='left')
print(f"  Merged with titles, abstracts, funding")

# Create hybrid features (same as before)
print("\n[3/6] Creating hybrid features...")

# RCDC
def parse_categories(cat_string):
    if pd.isna(cat_string) or cat_string == '':
        return []
    return [c.strip() for c in str(cat_string).split(';') if c.strip()]

df['rcdc_list'] = df['NIH_SPENDING_CATS'].apply(parse_categories)
all_rcdc = set()
for cats in df['rcdc_list']:
    all_rcdc.update(cats)

if len(all_rcdc) > 0:
    mlb_rcdc = MultiLabelBinarizer(classes=sorted(all_rcdc))
    rcdc_encoded = mlb_rcdc.fit_transform(df['rcdc_list'])
else:
    rcdc_encoded = np.zeros((len(df), 1))

# IC
df['IC_NAME'] = df['IC_NAME'].fillna('UNKNOWN')
ic_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
ic_encoded = ic_encoder.fit_transform(df[['IC_NAME']])

# Terms
def clean_terms(terms_string):
    if pd.isna(terms_string) or terms_string == '':
        return ''
    terms = [t.strip().lower() for t in str(terms_string).split(';') if t.strip()]
    terms = [t for t in terms if t not in STOP_TERMS and len(t) > 3]
    return ' '.join(terms)

df['terms_cleaned'] = df['PROJECT_TERMS'].apply(clean_terms)

tfidf = TfidfVectorizer(max_features=500, min_df=5, max_df=0.5, ngram_range=(1, 2))
try:
    terms_tfidf = tfidf.fit_transform(df['terms_cleaned']).toarray()
except:
    terms_tfidf = np.zeros((len(df), 1))

# Scale and combine
scaler = StandardScaler()
embeddings_scaled = scaler.fit_transform(embeddings)
rcdc_scaled = rcdc_encoded * np.sqrt(embeddings.shape[1] / max(rcdc_encoded.shape[1], 1))
ic_scaled = ic_encoded * np.sqrt(embeddings.shape[1] / max(ic_encoded.shape[1], 1))
terms_scaled = terms_tfidf * np.sqrt(embeddings.shape[1] / max(terms_tfidf.shape[1], 1))

hybrid_features = np.hstack([
    WEIGHT_EMBEDDING * embeddings_scaled,
    WEIGHT_RCDC * rcdc_scaled,
    WEIGHT_IC * ic_scaled,
    WEIGHT_TERMS * terms_scaled
])

print(f"  Hybrid features: {hybrid_features.shape}")

# Apply hierarchical clustering
print(f"\n[4/6] Clustering with K={K}...")
start = time.time()
Z = linkage(hybrid_features, method='ward')
df['cluster'] = fcluster(Z, K, criterion='maxclust')
print(f"  Clustering complete in {time.time()-start:.1f}s")

# Cluster statistics
cluster_counts = df['cluster'].value_counts().sort_index()
print(f"  Cluster sizes: {cluster_counts.min()}-{cluster_counts.max()} (mean: {cluster_counts.mean():.0f})")
print(f"  Tiny clusters (<50): {(cluster_counts < 50).sum()}")

# Generate topic labels for each cluster
print(f"\n[5/6] Generating topic labels...")

def generate_cluster_label(cluster_df):
    """Generate descriptive label from cluster contents"""
    # Most common RCDC categories
    rcdc_counts = {}
    for rcdc_list in cluster_df['rcdc_list']:
        for cat in rcdc_list:
            rcdc_counts[cat] = rcdc_counts.get(cat, 0) + 1
    
    # Most common IC
    ic_mode = cluster_df['IC_NAME'].mode()
    ic_name = ic_mode.iloc[0] if len(ic_mode) > 0 else 'Mixed'
    
    # Top RCDC category
    if rcdc_counts:
        top_rcdc = max(rcdc_counts.items(), key=lambda x: x[1])[0]
        # Simplify label
        if len(top_rcdc) > 30:
            top_rcdc = top_rcdc[:27] + '...'
    else:
        top_rcdc = 'General'
    
    return f"{ic_name}: {top_rcdc}"

cluster_labels = {}
for cluster_id in sorted(df['cluster'].unique()):
    cluster_df = df[df['cluster'] == cluster_id]
    label = generate_cluster_label(cluster_df)
    cluster_labels[int(cluster_id)] = label
    if cluster_id <= 10:  # Show first 10
        print(f"  Cluster {cluster_id:3d}: {label} (n={len(cluster_df)})")

df['topic_label'] = df['cluster'].map(cluster_labels)

# UMAP projection for visualization
print(f"\n[6/6] Computing UMAP projection...")
start = time.time()
reducer = umap.UMAP(
    n_neighbors=50,
    min_dist=0.1,
    metric='euclidean',
    n_components=2,
    random_state=42,
    n_jobs=1
)
umap_coords = reducer.fit_transform(hybrid_features)
df['umap_x'] = umap_coords[:, 0]
df['umap_y'] = umap_coords[:, 1]
print(f"  UMAP complete in {time.time()-start:.1f}s")

# Prepare visualization dataset
print(f"\n[7/7] Preparing visualization data...")
viz_df = df[[
    'APPLICATION_ID', 'PROJECT_TITLE', 'IC_NAME', 'FY', 
    'TOTAL_COST', 'cluster', 'topic_label',
    'umap_x', 'umap_y'
]].copy()

# Truncate titles for display
viz_df['title_short'] = viz_df['PROJECT_TITLE'].fillna('').str[:100]

# Save outputs
viz_df.to_csv('clustering_with_umap.csv', index=False)
print(f"  Saved: clustering_with_umap.csv")

with open('cluster_labels.json', 'w') as f:
    json.dump(cluster_labels, f, indent=2)
print(f"  Saved: cluster_labels.json")

# Summary stats
print("\n" + "=" * 70)
print("CLUSTERING SUMMARY")
print("=" * 70)
print(f"Total grants: {len(df):,}")
print(f"Number of clusters: {K}")
print(f"Cluster size range: {cluster_counts.min()}-{cluster_counts.max()}")
print(f"Mean cluster size: {cluster_counts.mean():.0f}")
print(f"UMAP coordinate ranges:")
print(f"  X: [{viz_df['umap_x'].min():.2f}, {viz_df['umap_x'].max():.2f}]")
print(f"  Y: [{viz_df['umap_y'].min():.2f}, {viz_df['umap_y'].max():.2f}]")
print("\n" + "=" * 70)
print("Ready for visualization!")
print("=" * 70)
