#!/usr/bin/env python3
import pandas as pd
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch
from sklearn.neighbors import NearestNeighbors
from google.cloud import bigquery
from tqdm import tqdm
import gc
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = "od-cl-odss-conroyri-f75a"
DATASET = "nih_analytics"
BATCH_SIZE = 128
MODEL_NAME = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
logger.info(f"Device: {device}")

print("="*80)
print("PHASE 2: ML-BASED CLUSTERING EXPANSION")
print("="*80)

# Initialize BigQuery client
client = bigquery.Client(project=PROJECT_ID)

# READ DIRECTLY FROM BIGQUERY (no GCS needed)
logger.info("[1/6] Loading unclustered awards from BigQuery...")
query_unclustered = f"""
SELECT *
FROM `{PROJECT_ID}.{DATASET}.phase2_unclustered_for_ml`
"""
df_new = client.query(query_unclustered).to_dataframe()
logger.info(f"Loaded {len(df_new):,} awards (${df_new['TOTAL_LIFETIME_FUNDING'].sum()/1e9:.1f}B)")

logger.info("Loading cluster centroids from BigQuery...")
query_centroids = f"""
SELECT 
  cluster_id, 
  cluster_label, 
  domain_id, 
  domain_name,
  AVG(umap_x) as centroid_x, 
  AVG(umap_y) as centroid_y
FROM `{PROJECT_ID}.{DATASET}.grant_cards_v1_6_with_agency`
WHERE cluster_id IS NOT NULL
GROUP BY cluster_id, cluster_label, domain_id, domain_name
ORDER BY cluster_id
"""
centroids_df = client.query(query_centroids).to_dataframe()
logger.info(f"Loaded {len(centroids_df)} centroids")

logger.info("[2/6] Loading PubMedBERT model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
model = model.to(device)
model.eval()
logger.info("Model loaded successfully")

def embed_texts(texts, batch_size=BATCH_SIZE):
    """Generate embeddings with progress tracking"""
    embeddings = []
    with tqdm(total=len(texts), desc="Generating embeddings") as pbar:
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            encoded = tokenizer(batch, padding=True, truncation=True, max_length=512, return_tensors='pt')
            encoded = {k: v.to(device) for k, v in encoded.items()}
            
            with torch.no_grad():
                outputs = model(**encoded)
                batch_emb = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            
            embeddings.append(batch_emb)
            pbar.update(len(batch))
            
            del encoded, outputs, batch_emb
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
    
    return np.vstack(embeddings)

logger.info("Generating embeddings for unclustered awards...")
texts = df_new['combined_text'].fillna('').tolist()
embeddings = embed_texts(texts)
logger.info(f"Generated embeddings: {embeddings.shape}")

np.save('/tmp/phase2_embeddings.npy', embeddings)
logger.info("Saved embeddings to /tmp/phase2_embeddings.npy")

del model, tokenizer
if torch.cuda.is_available():
    torch.cuda.empty_cache()
gc.collect()

logger.info("[3/6] Loading reference clustered awards from BigQuery...")
query_reference = f"""
SELECT *
FROM `{PROJECT_ID}.{DATASET}.phase2_reference_sample`
"""
df_ref = client.query(query_reference).to_dataframe()
logger.info(f"Loaded {len(df_ref):,} reference awards")

logger.info("[4/6] Approximating UMAP coordinates using KNN...")
ref_texts = (df_ref['type1_title'].fillna('') + ' ' + df_ref['type1_project_terms'].fillna('')).tolist()

logger.info("Generating embeddings for reference sample...")
model = AutoModel.from_pretrained(MODEL_NAME)
model = model.to(device)
model.eval()
ref_embeddings = embed_texts(ref_texts)
logger.info(f"Reference embeddings: {ref_embeddings.shape}")

del model
if torch.cuda.is_available():
    torch.cuda.empty_cache()
gc.collect()

logger.info("Building KNN index for UMAP approximation...")
knn = NearestNeighbors(n_neighbors=10, metric='cosine', n_jobs=-1)
knn.fit(ref_embeddings)

logger.info("Finding nearest neighbors...")
distances, indices = knn.kneighbors(embeddings)

ref_coords = df_ref[['umap_x', 'umap_y']].values
logger.info("Computing average UMAP coordinates from neighbors...")
umap_coords = np.array([ref_coords[idx].mean(axis=0) for idx in tqdm(indices, desc="UMAP coords")])

df_new['umap_x'] = umap_coords[:, 0]
df_new['umap_y'] = umap_coords[:, 1]
logger.info(f"Assigned UMAP coordinates: {umap_coords.shape}")

logger.info("[5/6] Assigning clusters using centroid nearest neighbors...")
centroids = centroids_df[['centroid_x', 'centroid_y']].values
centroid_ids = centroids_df['cluster_id'].values
logger.info(f"Using {len(centroids)} cluster centroids")

knn_cluster = NearestNeighbors(n_neighbors=1, metric='euclidean')
knn_cluster.fit(centroids)

cluster_dist, cluster_idx = knn_cluster.kneighbors(df_new[['umap_x', 'umap_y']].values)
df_new['cluster_id'] = centroid_ids[cluster_idx.flatten()]
df_new['cluster_distance'] = cluster_dist.flatten()

df_new = df_new.merge(
    centroids_df[['cluster_id', 'cluster_label', 'domain_id', 'domain_name']], 
    on='cluster_id', 
    how='left'
)

logger.info("\nCluster assignment summary (top 10):")
for cid, count in df_new['cluster_id'].value_counts().head(10).items():
    label = df_new[df_new['cluster_id']==cid]['cluster_label'].iloc[0]
    logger.info(f"  Cluster {cid} ({label}): {count:,} awards")

logger.info("[6/6] Saving results to BigQuery...")
output = df_new[[
    'CORE_PROJECT_NUM', 'cluster_id', 'cluster_label', 
    'domain_id', 'domain_name', 'umap_x', 'umap_y', 'cluster_distance'
]]

table_id = f"{PROJECT_ID}.{DATASET}.phase2_cluster_assignments"
job_config = bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE)

logger.info(f"Uploading to {table_id}...")
job = client.load_table_from_dataframe(output, table_id, job_config=job_config)
job.result()

logger.info(f"✓ Saved {len(output):,} cluster assignments to BigQuery")

print("\n" + "="*80)
print("✅ PHASE 2 CLUSTERING COMPLETE")
print("="*80)
print(f"\nProcessed: {len(df_new):,} awards")
print(f"Total funding: ${df_new['TOTAL_LIFETIME_FUNDING'].sum()/1e9:.1f}B")
print(f"Assigned to: {df_new['cluster_id'].nunique()} clusters")
print(f"Domains: {df_new['domain_id'].nunique()}")
print(f"\nResults saved to: {table_id}")
print("="*80)
