#!/bin/bash
# Complete GPU pipeline: launch, deploy, run, monitor

set -e

echo "========================================================================"
echo "GPU Embedding Generation Pipeline"
echo "========================================================================"
echo ""
echo "This will:"
echo "  1. Launch GPU VM (~$0.50/hour)"
echo "  2. Deploy code and dependencies"
echo "  3. Run PROJECT_TERMS embedding generation (~15-30 min)"
echo "  4. Auto-shutdown when complete"
echo ""
echo "Total estimated cost: ~$0.25-0.50"
echo ""
echo "Continue? (y/n)"
read -r response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 0
fi

# Step 1: Launch VM
echo ""
echo "========================================================================"
echo "Step 1/3: Launching GPU VM"
echo "========================================================================"
bash launch_gpu_vm.sh

# Step 2: Deploy code
echo ""
echo "========================================================================"
echo "Step 2/3: Deploying Code"
echo "========================================================================"
bash deploy_and_run_embeddings.sh

# Step 3: Start job in background
echo ""
echo "========================================================================"
echo "Step 3/3: Starting Embedding Generation"
echo "========================================================================"
VM_NAME="nih-embeddings-gpu-vm"
ZONE="us-central1-a"

gcloud compute ssh $VM_NAME --zone=$ZONE --command='nohup ~/nih-topic-maps/run_with_autoshutdown.sh > ~/embedding.log 2>&1 &'

echo ""
echo "✓ Job started in background!"
echo ""
echo "========================================================================"
echo "Monitoring"
echo "========================================================================"
echo "Monitor progress:"
echo "  bash monitor_gpu_vm.sh"
echo ""
echo "Check results (after ~15-30 min):"
echo "  bash check_results_and_cleanup.sh"
echo ""
echo "Emergency stop:"
echo "  bash emergency_stop_vm.sh"
echo ""
echo "The VM will auto-shutdown when complete."
