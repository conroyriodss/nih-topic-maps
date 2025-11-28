#!/bin/bash
# Launch GPU VM for fast embedding generation
# Estimated time with T4 GPU: 15-30 minutes vs 2-4 hours on CPU

set -e

PROJECT_ID="od-cl-odss-conroyri-f75a"
ZONE="us-central1-a"
VM_NAME="nih-embeddings-gpu-vm"
MACHINE_TYPE="n1-standard-4"
GPU_TYPE="nvidia-tesla-t4"
GPU_COUNT=1
BOOT_DISK_SIZE="100GB"

echo "========================================================================"
echo "Launching GPU VM for PROJECT_TERMS Embedding Generation"
echo "========================================================================"
echo "VM Name: $VM_NAME"
echo "Zone: $ZONE"
echo "GPU: $GPU_TYPE"
echo "Estimated cost: ~$0.50/hour (~$0.25-0.50 total for 30 min job)"
echo "========================================================================"
echo ""

# Check if VM already exists
if gcloud compute instances describe $VM_NAME --zone=$ZONE 2>/dev/null; then
    echo "WARNING: VM $VM_NAME already exists!"
    echo "Options:"
    echo "  1. Delete it: gcloud compute instances delete $VM_NAME --zone=$ZONE"
    echo "  2. SSH to it: gcloud compute ssh $VM_NAME --zone=$ZONE"
    exit 1
fi

# Create the VM with NO startup script (we'll install after)
echo "Creating GPU VM..."
gcloud compute instances create $VM_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --accelerator=type=$GPU_TYPE,count=$GPU_COUNT \
    --maintenance-policy=TERMINATE \
    --boot-disk-size=$BOOT_DISK_SIZE \
    --boot-disk-type=pd-standard \
    --image-family=debian-11 \
    --image-project=debian-cloud \
    --scopes=https://www.googleapis.com/auth/cloud-platform

echo ""
echo "VM created! Waiting 30 seconds for boot..."
sleep 30

echo ""
echo "Installing dependencies..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command='
set -e
echo "Step 1: Installing CUDA drivers..."
curl -s https://raw.githubusercontent.com/GoogleCloudPlatform/compute-gpu-installation/main/linux/install_gpu_driver.py --output /tmp/install_gpu_driver.py
sudo python3 /tmp/install_gpu_driver.py 2>&1 | grep -E "Installing|Successfully|Error" || echo "GPU driver installation attempted"

echo ""
echo "Step 2: Installing Python packages..."
sudo apt-get update -qq
sudo apt-get install -y python3-pip git -qq
sudo pip3 install --upgrade pip -q
sudo pip3 install pandas pyarrow numpy torch transformers tqdm google-cloud-bigquery google-cloud-storage -q

echo ""
echo "Step 3: Verifying installations..."
python3 -c "import torch; print(\"PyTorch installed\")" || exit 1
python3 -c "from google.cloud import bigquery; print(\"BigQuery installed\")" || exit 1
python3 -c "from transformers import AutoModel; print(\"Transformers installed\")" || exit 1

echo ""
echo "All dependencies installed successfully!"
'

echo ""
echo "========================================================================"
echo "VM Ready!"
echo "========================================================================"
echo "To check GPU: gcloud compute ssh $VM_NAME --zone=$ZONE --command='nvidia-smi'"
echo ""
echo "Next step: Deploy code and run embeddings"
echo "  bash deploy_and_run_embeddings.sh"
