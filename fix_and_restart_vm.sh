#!/bin/bash
# Fix VM dependencies and restart embedding generation

set -e

PROJECT_ID="od-cl-odss-conroyri-f75a"
ZONE="us-central1-a"
VM_NAME="nih-embeddings-gpu-vm"

echo "========================================================================"
echo "Fixing VM Dependencies and Restarting Job"
echo "========================================================================"
echo ""

# Install dependencies directly via SSH
echo "Step 1: Installing CUDA drivers and dependencies..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command='
set -e
echo "Installing CUDA drivers..."
curl https://raw.githubusercontent.com/GoogleCloudPlatform/compute-gpu-installation/main/linux/install_gpu_driver.py --output /tmp/install_gpu_driver.py
sudo python3 /tmp/install_gpu_driver.py || echo "GPU driver installation attempted"

echo ""
echo "Installing Python packages..."
sudo apt-get update -qq
sudo apt-get install -y python3-pip git -qq
sudo pip3 install --upgrade pip -q
sudo pip3 install pandas pyarrow numpy torch transformers tqdm google-cloud-bigquery google-cloud-storage -q

echo ""
echo "Verifying installations..."
python3 -c "import torch; print(f\"PyTorch: {torch.__version__}\")"
python3 -c "from google.cloud import bigquery; print(\"BigQuery: OK\")"
python3 -c "from transformers import AutoModel; print(\"Transformers: OK\")"

echo ""
echo "Setup complete!"
'

echo ""
echo "Step 2: Checking GPU..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command='nvidia-smi || echo "GPU not ready yet - will work with CPU"'

echo ""
echo "Step 3: Restarting embedding generation..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command='
cd ~/nih-topic-maps
nohup bash run_with_autoshutdown.sh > ~/embedding.log 2>&1 &
echo "Job restarted in background"
'

echo ""
echo "========================================================================"
echo "Job Restarted!"
echo "========================================================================"
echo ""
echo "Monitor progress:"
echo "  bash monitor_gpu_vm.sh"
echo ""
echo "Check log:"
echo "  gcloud compute ssh $VM_NAME --zone=$ZONE --command='tail -f ~/embedding.log'"
