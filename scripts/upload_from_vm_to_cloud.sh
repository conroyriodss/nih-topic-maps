#!/bin/bash
set -e

echo "=========================================="
echo "UPLOADING DIRECTLY FROM VM TO CLOUD"
echo "December 4, 2025 - 10:56 PM EST"
echo "=========================================="
echo ""

# ==========================================
# STEP 1: CREATE CLOUD STORAGE BUCKET
# ==========================================
echo "[1/3] Creating Cloud Storage bucket..."

gsutil mb -p od-cl-odss-conroyri-f75a -l us-central1 gs://nih-analytics-embeddings/ 2>/dev/null || echo "✓ Bucket already exists"

# ==========================================
# STEP 2: START VM TEMPORARILY
# ==========================================
echo ""
echo "[2/3] Starting VM to upload embeddings..."

gcloud compute instances start nih-embeddings-gpu-vm --zone=us-central1-a

echo "Waiting 30 seconds for VM to boot..."
sleep 30

# ==========================================
# STEP 3: UPLOAD FROM VM TO CLOUD STORAGE
# ==========================================
echo ""
echo "[3/3] Uploading embeddings from VM to Cloud Storage..."

gcloud compute ssh nih-embeddings-gpu-vm --zone=us-central1-a --command='
echo "Uploading embeddings to Cloud Storage..."

# Upload embeddings
gsutil -m cp /tmp/phase2_embeddings.npy gs://nih-analytics-embeddings/phase2_embeddings_20251204.npy

# Upload log
gsutil cp ~/phase2_clustering.log gs://nih-analytics-embeddings/phase2_clustering_20251204.log 2>/dev/null || echo "Log not found"

# Create and upload metadata
cat > /tmp/metadata.json << "METADATA"
{
  "creation_date": "2025-12-04",
  "completion_time": "2025-12-05 02:24 AM EST",
  "total_runtime_hours": 8,
  "model": "PubMedBERT",
  "embedding_dimensions": 768,
  "total_embeddings": 1015021,
  "file_size_mb": 407,
  "awards_clustered": 253487,
  "clusters_used": 30,
  "vm_type": "n1-standard-4 with GPU",
  "bigquery_table": "phase2_cluster_assignments"
}
METADATA

gsutil cp /tmp/metadata.json gs://nih-analytics-embeddings/EMBEDDINGS_METADATA.json

echo "Upload complete!"
ls -lh /tmp/phase2_embeddings.npy
'

echo ""
echo "Verifying upload..."
gsutil ls -lh gs://nih-analytics-embeddings/

echo ""
echo "Stopping VM..."
gcloud compute instances stop nih-embeddings-gpu-vm --zone=us-central1-a

echo ""
echo "=========================================="
echo "✅ EMBEDDINGS UPLOADED TO CLOUD!"
echo "=========================================="
echo ""
gsutil ls -lh gs://nih-analytics-embeddings/
echo ""
echo "You can now DELETE the VM:"
echo "  gcloud compute instances delete nih-embeddings-gpu-vm --zone=us-central1-a"
echo ""
echo "And clean up local disk:"
echo "  rm -rf ~/phase2_backup/"
echo "=========================================="
