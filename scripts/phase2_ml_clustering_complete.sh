#!/bin/bash
set -e

PROJECT_ID="od-cl-odss-conroyri-f75a"
BUCKET="nih-analytics-exports"
DATASET="nih_analytics"
VM_NAME="clustering-phase2-ml"
ZONE="us-central1-a"
MACHINE_TYPE="n1-highmem-8"
GPU_TYPE="nvidia-tesla-t4"

echo "=========================================="
echo "PHASE 2: ML-BASED CLUSTERING EXPANSION"
echo "=========================================="
echo "Project: $PROJECT_ID"
echo "VM: $VM_NAME ($MACHINE_TYPE + $GPU_TYPE)"
echo "Estimated time: 3-5 hours"
echo "Estimated cost: $15-20"
echo ""

#############################################
# PART 1: PREPARE DATA IN BIGQUERY
#############################################

echo "[1/8] Preparing data in BigQuery..."

bq query --use_legacy_sql=false << 'EOSQL'
-- Extract unclustered awards for embedding
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.phase2_unclustered_for_ml` AS
SELECT 
  CORE_PROJECT_NUM,
  ADMINISTERING_IC,
  organizational_category,
  type1_title,
  type1_project_terms,
  type1_nih_categories,
  
  -- Combined text (same as Phase 1)
  CONCAT(
    COALESCE(type1_title, ''),
    ' ',
    COALESCE(type1_project_terms, ''),
    ' ',
    COALESCE(type1_nih_categories, '')
  ) as combined_text,
  
  TOTAL_LIFETIME_FUNDING,
  publication_count,
  FIRST_FISCAL_YEAR,
  LAST_FISCAL_YEAR,
  ACTIVITY,
  is_mpi,
  pi_count
  
FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`
WHERE cluster_id IS NULL
  AND type1_title IS NOT NULL
ORDER BY TOTAL_LIFETIME_FUNDING DESC;
EOSQL

# Get count
UNCLUSTERED_COUNT=$(bq query --use_legacy_sql=false --format=csv \
  "SELECT COUNT(*) as cnt FROM \`$PROJECT_ID.$DATASET.phase2_unclustered_for_ml\`" | tail -n 1)
echo "  ✓ Prepared $UNCLUSTERED_COUNT unclustered awards"

#############################################
# PART 2: EXPORT TO GCS
#############################################

echo ""
echo "[2/8] Exporting to Cloud Storage..."

# Create phase2 directory
gsutil -m rm -r gs://$BUCKET/phase2/ 2>/dev/null || true
gsutil mkdir gs://$BUCKET/phase2/

# Export unclustered data
bq extract \
  --destination_format=PARQUET \
  --compression=SNAPPY \
  $PROJECT_ID:$DATASET.phase2_unclustered_for_ml \
  "gs://$BUCKET/phase2/unclustered_*.parquet"

echo "  ✓ Exported to gs://$BUCKET/phase2/"

# Export reference data (clustered awards for centroids)
bq query --use_legacy_sql=false --format=csv \
  "SELECT cluster_id, cluster_label, domain_id, domain_name,
          AVG(umap_x) as centroid_x, AVG(umap_y) as centroid_y
   FROM \`$PROJECT_ID.$DATASET.grant_cards_v1_6_with_agency\`
   WHERE cluster_id IS NOT NULL
   GROUP BY cluster_id, cluster_label, domain_id, domain_name
   ORDER BY cluster_id" > /tmp/cluster_centroids.csv

gsutil cp /tmp/cluster_centroids.csv gs://$BUCKET/phase2/

# Export sample of clustered awards for KNN reference
bq extract \
  --destination_format=PARQUET \
  --compression=SNAPPY \
  $PROJECT_ID:$DATASET.grant_cards_v1_6_with_agency \
  "gs://$BUCKET/phase2/reference_clustered_*.parquet"

echo "  ✓ Exported reference data"

#############################################
# PART 3: CREATE GPU VM
#############################################

echo ""
echo "[3/8] Creating GPU VM..."

# Delete VM if exists
gcloud compute instances delete $VM_NAME --zone=$ZONE --quiet 2>/dev/null || true

# Create new VM
gcloud compute instances create $VM_NAME \
  --project=$PROJECT_ID \
  --zone=$ZONE \
  --machine-type=$MACHINE_TYPE \
  --accelerator=type=$GPU_TYPE,count=1 \
  --maintenance-policy=TERMINATE \
  --boot-disk-size=200GB \
  --boot-disk-type=pd-balanced \
  --image-family=pytorch-latest-gpu \
  --image-project=deeplearning-platform-release \
  --scopes=cloud-platform \
  --metadata=install-nvidia-driver=True

echo "  ✓ Created VM: $VM_NAME"
echo "  Waiting 90s for VM to boot..."
sleep 90

#############################################
# PART 4: INSTALL DEPENDENCIES
#############################################

echo ""
echo "[4/8] Installing dependencies on VM..."

gcloud compute ssh $VM_NAME --zone=$ZONE --command='
set -e
echo "Installing Python packages..."
pip install -q --upgrade pip
pip install -q transformers==4.35.0
pip install -q torch==2.1.0
pip install -q sentence-transformers==2.2.2
pip install -q umap-learn==0.5.5
pip install -q pandas==2.1.3
pip install -q pyarrow==14.0.1
pip install -q gcsfs==2023.12.0
pip install -q google-cloud-bigquery==3.14.0
pip install -q scikit-learn==1.3.2
pip install -q tqdm

echo "✓ Dependencies installed"

# Verify GPU
python3 << "PYEND"
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"CUDA version: {torch.version.cuda}")
PYEND
'

echo "  ✓ VM environment ready"

#############################################
# PART 5: CREATE CLUSTERING SCRIPT
#############################################

echo ""
echo "[5/8] Creating clustering script..."

cat > /tmp/phase2_cluster.py << 'PYSCRIPT'
#!/usr/bin/env python3
"""
Phase 2: ML-Based Clustering Expansion
Clusters 1M unclustered awards using PubMedBERT embeddings
"""

import pandas as pd
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch
from sklearn.neighbors import NearestNeighbors
from google.cloud import bigquery
from tqdm import tqdm
import gc
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = "od-cl-odss-conroyri-f75a"
BUCKET = "nih-analytics-exports"
DATASET = "nih_analytics"
BATCH_SIZE = 128
MODEL_NAME = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
logger.info(f"Using device: {device}")
if torch.cuda.is_available():
    logger.info(f"GPU: {torch.cuda.get_device_name(0)}")

print("="*80)
print("PHASE 2: ML-BASED CLUSTERING EXPANSION")
print("="*80)

#############################################
# STEP 1: LOAD DATA
#############################################

logger.info("[1/6] Loading unclustered awards...")
df_new = pd.read_parquet(f'gs://{BUCKET}/phase2/unclustered_*.parquet')
logger.info(f"Loaded {len(df_new):,} unclustered awards")
logger.info(f"Total funding: ${df_new['TOTAL_LIFETIME_FUNDING'].sum()/1e9:.1f}B")

# Load cluster centroids
logger.info("Loading cluster centroids...")
centroids_df = pd.read_csv(f'gs://{BUCKET}/phase2/cluster_centroids.csv')
logger.info(f"Loaded {len(centroids_df)} cluster centroids")

#############################################
# STEP 2: GENERATE EMBEDDINGS
#############################################

logger.info("[2/6] Loading PubMedBERT model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
model = model.to(device)
model.eval()
logger.info("Model loaded successfully")

def embed_texts_batch(texts, batch_size=BATCH_SIZE):
    """Generate embeddings with progress bar"""
    embeddings = []
    
    with tqdm(total=len(texts), desc="Generating embeddings") as pbar:
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            # Tokenize
            encoded = tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors='pt'
            )
            encoded = {k: v.to(device) for k, v in encoded.items()}
            
            # Generate embeddings
            with torch.no_grad():
                outputs = model(**encoded)
                batch_emb = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            
            embeddings.append(batch_emb)
            pbar.update(len(batch))
            
            # Memory cleanup
            del encoded, outputs, batch_emb
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
    
    return np.vstack(embeddings)

logger.info("Generating embeddings for unclustered awards...")
texts = df_new['combined_text'].fillna('').tolist()
embeddings_new = embed_texts_batch(texts)
logger.info(f"Generated embeddings: {embeddings_new.shape}")

# Save embeddings
logger.info("Saving embeddings...")
np.save('/tmp/phase2_embeddings.npy', embeddings_new)
logger.info("Embeddings saved to /tmp/phase2_embeddings.npy")

# Free memory
del model, tokenizer
if torch.cuda.is_available():
    torch.cuda.empty_cache()
gc.collect()

#############################################
# STEP 3: LOAD REFERENCE CLUSTERED AWARDS
#############################################

logger.info("[3/6] Loading reference clustered awards...")
df_ref = pd.read_parquet(f'gs://{BUCKET}/phase2/reference_clustered_*.parquet')
df_ref = df_ref[df_ref['cluster_id'].notna()].copy()
logger.info(f"Loaded {len(df_ref):,} reference awards")

# Get UMAP coordinates
ref_coords = df_ref[['umap_x', 'umap_y']].values
ref_clusters = df_ref['cluster_id'].values

logger.info(f"Reference UMAP space: {ref_coords.shape}")

#############################################
# STEP 4: PROJECT TO UMAP SPACE
#############################################

logger.info("[4/6] Projecting to UMAP space...")
logger.info("Note: Using approximate UMAP projection via embedding similarity")

# Since we don't have the original UMAP model, we'll use KNN in embedding space
# to find similar awards and use their UMAP coordinates

# Load reference embeddings (if available) or approximate
logger.info("Using KNN to approximate UMAP coordinates...")

# For each new embedding, find K nearest neighbors in reference set
# and average their UMAP coordinates
K_NEIGHBORS = 10

# We need reference embeddings - let's generate for a sample
logger.info("Generating reference embeddings (sample)...")
ref_sample = df_ref.sample(min(50000, len(df_ref)), random_state=42)
ref_texts = (ref_sample['type1_title'].fillna('') + ' ' + 
             ref_sample['type1_project_terms'].fillna('')).tolist()

# Reload model temporarily
logger.info("Reloading model for reference embeddings...")
model = AutoModel.from_pretrained(MODEL_NAME)
model = model.to(device)
model.eval()

ref_embeddings = embed_texts_batch(ref_texts)
logger.info(f"Reference embeddings: {ref_embeddings.shape}")

del model
if torch.cuda.is_available():
    torch.cuda.empty_cache()
gc.collect()

# Build KNN index
logger.info("Building KNN index...")
knn_embedding = NearestNeighbors(n_neighbors=K_NEIGHBORS, metric='cosine', n_jobs=-1)
knn_embedding.fit(ref_embeddings)

# Find neighbors for new embeddings
logger.info("Finding nearest neighbors...")
distances, indices = knn_embedding.kneighbors(embeddings_new)

# Get UMAP coordinates from neighbors
ref_sample_coords = ref_sample[['umap_x', 'umap_y']].values
umap_coords_new = np.array([
    ref_sample_coords[idx].mean(axis=0) 
    for idx in tqdm(indices, desc="Computing UMAP coords")
])

df_new['umap_x'] = umap_coords_new[:, 0]
df_new['umap_y'] = umap_coords_new[:, 1]
logger.info(f"Assigned UMAP coordinates: {umap_coords_new.shape}")

#############################################
# STEP 5: ASSIGN CLUSTERS
#############################################

logger.info("[5/6] Assigning clusters...")

# Use cluster centroids from reference
centroids = centroids_df[['centroid_x', 'centroid_y']].values
centroid_ids = centroids_df['cluster_id'].values

logger.info(f"Using {len(centroids)} cluster centroids")

# Find nearest centroid for each new award
knn_clusters = NearestNeighbors(n_neighbors=1, metric='euclidean')
knn_clusters.fit(centroids)

new_coords = df_new[['umap_x', 'umap_y']].values
cluster_distances, cluster_indices = knn_clusters.kneighbors(new_coords)

# Assign clusters
df_new['cluster_id'] = centroid_ids[cluster_indices.flatten()]
df_new['cluster_distance'] = cluster_distances.flatten()

logger.info("Merging cluster metadata...")
df_new = df_new.merge(
    centroids_df[['cluster_id', 'cluster_label', 'domain_id', 'domain_name']],
    on='cluster_id',
    how='left'
)

# Summary
logger.info("\nCluster assignment summary:")
cluster_counts = df_new['cluster_id'].value_counts().head(10)
for cid, count in cluster_counts.items():
    label = df_new[df_new['cluster_id']==cid]['cluster_label'].iloc[0]
    logger.info(f"  Cluster {cid} ({label}): {count:,} awards")

#############################################
# STEP 6: SAVE TO BIGQUERY
#############################################

logger.info("[6/6] Saving results to BigQuery...")

output_df = df_new[[
    'CORE_PROJECT_NUM',
    'cluster_id',
    'cluster_label',
    'domain_id',
    'domain_name',
    'umap_x',
    'umap_y',
    'cluster_distance'
]]

client = bigquery.Client(project=PROJECT_ID)

table_id = f"{PROJECT_ID}.{DATASET}.phase2_cluster_assignments"
job_config = bigquery.LoadJobConfig(
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
)

job = client.load_table_from_dataframe(
    output_df, 
    table_id, 
    job_config=job_config
)
job.result()

logger.info(f"✓ Saved {len(output_df):,} assignments to BigQuery")

print("\n" + "="*80)
print("✅ PHASE 2 CLUSTERING COMPLETE")
print("="*80)
print(f"\nProcessed: {len(df_new):,} awards")
print(f"Total funding: ${df_new['TOTAL_LIFETIME_FUNDING'].sum()/1e9:.1f}B")
print(f"Assigned to: {df_new['cluster_id'].nunique()} clusters")
print(f"Domains covered: {df_new['domain_id'].nunique()}")
print(f"\nResults saved to: {table_id}")
print("="*80)
PYSCRIPT

# Upload script to VM
gcloud compute scp /tmp/phase2_cluster.py $VM_NAME:~/ --zone=$ZONE

echo "  ✓ Uploaded clustering script to VM"

#############################################
# PART 6: RUN CLUSTERING
#############################################

echo ""
echo "[6/8] Starting clustering on VM..."
echo "  This will take 3-5 hours"
echo ""

gcloud compute ssh $VM_NAME --zone=$ZONE --command='
nohup python3 phase2_cluster.py > phase2_clustering.log 2>&1 &
echo $! > clustering.pid
echo "✓ Clustering started (PID: $(cat clustering.pid))"
echo ""
echo "Monitor progress with:"
echo "  tail -f phase2_clustering.log"
'

echo "  ✓ Clustering job started"
echo ""
echo "=========================================="
echo "MONITORING INSTRUCTIONS"
echo "=========================================="
echo ""
echo "Connect to VM:"
echo "  gcloud compute ssh $VM_NAME --zone=$ZONE"
echo ""
echo "Monitor progress:"
echo "  tail -f phase2_clustering.log"
echo ""
echo "Check if complete:"
echo "  ps -p \$(cat clustering.pid)"
echo ""
echo "Download log:"
echo "  gcloud compute scp $VM_NAME:~/phase2_clustering.log ./ --zone=$ZONE"
echo ""

#############################################
# PART 7: CREATE COMPLETION CHECK SCRIPT
#############################################

cat > check_phase2_complete.sh << 'CHECKSCRIPT'
#!/bin/bash

VM_NAME="clustering-phase2-ml"
ZONE="us-central1-a"
PROJECT_ID="od-cl-odss-conroyri-f75a"

echo "Checking clustering status..."

# Check VM process
gcloud compute ssh $VM_NAME --zone=$ZONE --command='
if [ -f clustering.pid ]; then
  if ps -p $(cat clustering.pid) > /dev/null 2>&1; then
    echo "Status: RUNNING"
    echo ""
    tail -n 30 phase2_clustering.log
  else
    echo "Status: COMPLETE"
    echo ""
    tail -n 50 phase2_clustering.log
  fi
else
  echo "Status: NOT STARTED"
fi
' 2>/dev/null || echo "VM not accessible"

# Check BigQuery
echo ""
echo "Checking BigQuery table..."
bq query --use_legacy_sql=false --format=csv \
  "SELECT COUNT(*) as assignments FROM \`$PROJECT_ID.nih_analytics.phase2_cluster_assignments\`" 2>/dev/null | tail -n 1
CHECKSCRIPT

chmod +x check_phase2_complete.sh

echo ""
echo "[7/8] Next steps after completion..."
cat > update_grant_cards_after_phase2.sh << 'UPDATESCRIPT'
#!/bin/bash
set -e

echo "Updating grant_cards with Phase 2 results..."

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v2_0_complete` AS
SELECT 
  g.*,
  COALESCE(g.cluster_id, p.cluster_id) as cluster_id_new,
  COALESCE(g.cluster_label, p.cluster_label) as cluster_label_new,
  COALESCE(g.domain_id, p.domain_id) as domain_id_new,
  COALESCE(g.domain_name, p.domain_name) as domain_name_new,
  COALESCE(g.umap_x, p.umap_x) as umap_x_new,
  COALESCE(g.umap_y, p.umap_y) as umap_y_new,
  CASE 
    WHEN g.cluster_id IS NOT NULL THEN 'Phase 1 (ML)'
    WHEN p.cluster_id IS NOT NULL THEN 'Phase 2 (ML)'
    ELSE 'Unclustered'
  END as clustering_phase
FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency` g
LEFT JOIN `od-cl-odss-conroyri-f75a.nih_analytics.phase2_cluster_assignments` p
  ON g.CORE_PROJECT_NUM = p.CORE_PROJECT_NUM;

-- Clean up
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v2_0_complete` AS
SELECT 
  * EXCEPT(cluster_id, cluster_label, domain_id, domain_name, umap_x, umap_y, is_clustered,
           cluster_id_new, cluster_label_new, domain_id_new, domain_name_new, umap_x_new, umap_y_new),
  cluster_id_new as cluster_id,
  cluster_label_new as cluster_label,
  domain_id_new as domain_id,
  domain_name_new as domain_name,
  umap_x_new as umap_x,
  umap_y_new as umap_y,
  CASE WHEN cluster_id_new IS NOT NULL THEN TRUE ELSE FALSE END as is_clustered,
  clustering_phase
FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v2_0_complete`;
EOSQL

echo "✓ Grant cards updated"

# Summary
bq query --use_legacy_sql=false << 'EOSQL'
SELECT 
  clustering_phase,
  COUNT(*) as awards,
  ROUND(SUM(TOTAL_LIFETIME_FUNDING)/1e9, 2) as funding_b,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as pct
FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v2_0_complete`
GROUP BY clustering_phase;
EOSQL
UPDATESCRIPT

chmod +x update_grant_cards_after_phase2.sh

echo ""
echo "[8/8] Cleanup script..."
cat > cleanup_phase2_vm.sh << 'CLEANUPSCRIPT'
#!/bin/bash
VM_NAME="clustering-phase2-ml"
ZONE="us-central1-a"

echo "Deleting VM: $VM_NAME"
gcloud compute instances delete $VM_NAME --zone=$ZONE --quiet
echo "✓ VM deleted"
CLEANUPSCRIPT

chmod +x cleanup_phase2_vm.sh

echo ""
echo "=========================================="
echo "✅ PHASE 2 SETUP COMPLETE"
echo "=========================================="
echo ""
echo "Clustering is now running on VM: $VM_NAME"
echo "Estimated completion: 3-5 hours"
echo ""
echo "Scripts created:"
echo "  ./check_phase2_complete.sh - Check status"
echo "  ./update_grant_cards_after_phase2.sh - Update after completion"
echo "  ./cleanup_phase2_vm.sh - Delete VM when done"
echo ""
echo "=========================================="
