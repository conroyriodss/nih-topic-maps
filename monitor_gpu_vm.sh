#!/bin/bash
# Monitor GPU VM progress

PROJECT_ID="od-cl-odss-conroyri-f75a"
ZONE="us-central1-a"
VM_NAME="nih-embeddings-gpu-vm"

echo "========================================================================"
echo "Monitoring GPU VM Progress"
echo "========================================================================"
echo ""

# Check if VM exists and is running
STATUS=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format="get(status)" 2>/dev/null || echo "NOT_FOUND")

if [ "$STATUS" = "NOT_FOUND" ]; then
    echo "❌ VM not found. Either:"
    echo "  1. Not created yet - run: bash launch_gpu_vm.sh"
    echo "  2. Already shut down - check GCS for results"
    exit 1
fi

echo "VM Status: $STATUS"
echo ""

if [ "$STATUS" = "RUNNING" ]; then
    echo "Showing last 50 lines of log (press Ctrl+C to exit)..."
    echo ""
    gcloud compute ssh $VM_NAME --zone=$ZONE --command="tail -50 ~/embedding.log 2>/dev/null || echo 'Log not started yet. Job may not be running.'"
    
    echo ""
    echo "========================================================================"
    echo "Commands:"
    echo "========================================================================"
    echo "Follow live log:"
    echo "  gcloud compute ssh $VM_NAME --zone=$ZONE --command='tail -f ~/embedding.log'"
    echo ""
    echo "Check GPU usage:"
    echo "  gcloud compute ssh $VM_NAME --zone=$ZONE --command='nvidia-smi'"
    echo ""
    echo "Check if job is running:"
    echo "  gcloud compute ssh $VM_NAME --zone=$ZONE --command='ps aux | grep python'"
else
    echo "VM is $STATUS - not running"
fi
