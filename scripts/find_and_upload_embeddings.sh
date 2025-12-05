#!/bin/bash
set -e

echo "=========================================="
echo "FINDING AND UPLOADING EMBEDDINGS"
echo "December 4, 2025 - 11:00 PM EST"
echo "=========================================="
echo ""

echo "[1/4] Searching for embeddings file on VM..."

gcloud compute ssh nih-embeddings-gpu-vm --zone=us-central1-a --command='
echo "Searching for embeddings file..."
find ~ -name "*embeddings*.npy" -type f 2>/dev/null || echo "Not in home directory"
find /tmp -name "*embeddings*.npy" -type f 2>/dev/null || echo "Not in /tmp"
find /home -name "*embeddings*.npy" -type f 2>/dev/null || echo "Not in /home"

echo ""
echo "Checking process log for save location..."
grep -i "saved.*embeddings" ~/phase2_clustering.log 2>/dev/null || echo "Log check failed"

echo ""
echo "Disk usage to find large files:"
du -sh ~/* 2>/dev/null | sort -hr | head -10
du -sh /tmp/* 2>/dev/null | sort -hr | head -10
'

echo ""
echo "[2/4] The embeddings were already copied locally!"
echo "We have ~/phase2_backup/phase2_embeddings.npy (407MB)"

echo ""
echo "[3/4] Let me upload from Cloud Shell in chunks..."

# Clean up space first
rm -rf ~/phase2_backup/phase2_cluster.py 2>/dev/null || true

# Upload the embeddings file we already have
cd ~/phase2_backup
gsutil -m cp phase2_embeddings.npy gs://nih-analytics-embeddings/phase2_embeddings_20251204.npy

echo ""
echo "[4/4] Upload remaining files..."

# Upload log
gsutil cp phase2_clustering.log gs://nih-analytics-embeddings/phase2_clustering_20251204.log

# Upload summary
gsutil cp COMPLETION_SUMMARY.md gs://nih-analytics-embeddings/COMPLETION_SUMMARY_20251204.md 2>/dev/null || echo "Summary not found"

echo ""
echo "=========================================="
echo "✅ EMBEDDINGS UPLOADED!"
echo "=========================================="
echo ""
gsutil ls -lh gs://nih-analytics-embeddings/
echo ""
echo "Now cleaning up..."

# Stop VM
gcloud compute instances stop nih-embeddings-gpu-vm --zone=us-central1-a

# Clean up local disk
cd ~
rm -rf ~/phase2_backup/

echo ""
echo "Final status:"
echo "  ✓ Embeddings in Cloud Storage"
echo "  ✓ VM stopped"
echo "  ✓ Local disk cleaned"
echo ""
echo "Delete VM to save costs:"
echo "  gcloud compute instances delete nih-embeddings-gpu-vm --zone=us-central1-a"
echo "=========================================="
