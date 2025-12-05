#!/bin/bash
# Fix corrupted PyTorch installation and restart job

set -e

PROJECT_ID="od-cl-odss-conroyri-f75a"
ZONE="us-central1-a"
VM_NAME="nih-embeddings-gpu-vm"

echo "========================================================================"
echo "Fixing PyTorch Installation and Restarting Job"
echo "========================================================================"
echo ""

echo "Step 1: Cleaning up corrupted PyTorch installation..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command='
set -e

echo "Removing old PyTorch installation..."
sudo pip3 uninstall -y torch torchvision torchaudio 2>/dev/null || true
sudo rm -rf /usr/local/lib/python3.9/dist-packages/torch* 2>/dev/null || true

echo ""
echo "Installing PyTorch with CUDA support..."
sudo pip3 install torch --index-url https://download.pytorch.org/whl/cu118 --no-cache-dir

echo ""
echo "Installing other dependencies..."
sudo pip3 install transformers tqdm pandas pyarrow numpy google-cloud-bigquery google-cloud-storage --no-cache-dir

echo ""
echo "Verifying installations..."
python3 -c "import torch; print(f\"PyTorch: {torch.__version__}, CUDA available: {torch.cuda.is_available()}\")"
python3 -c "from google.cloud import bigquery; print(\"BigQuery: OK\")"
python3 -c "from transformers import AutoModel; print(\"Transformers: OK\")"

echo ""
echo "All dependencies installed successfully!"
'

echo ""
echo "Step 2: Checking GPU..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command='nvidia-smi'

echo ""
echo "Step 3: Restarting embedding generation..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command='
cd ~/nih-topic-maps
rm -f ~/embedding.log
nohup bash run_with_autoshutdown.sh > ~/embedding.log 2>&1 &
echo "Job restarted in background"
sleep 3
echo ""
echo "Initial log output:"
tail -20 ~/embedding.log
'

echo ""
echo "========================================================================"
echo "Job Restarted!"
echo "========================================================================"
echo ""
echo "Monitor progress:"
echo "  bash monitor_gpu_vm.sh"
echo ""
echo "Or follow live:"
echo "  gcloud compute ssh $VM_NAME --zone=$ZONE --command='tail -f ~/embedding.log'"
