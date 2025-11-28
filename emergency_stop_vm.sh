#!/bin/bash
# Emergency stop and cleanup of GPU VM

PROJECT_ID="od-cl-odss-conroyri-f75a"
ZONE="us-central1-a"
VM_NAME="nih-embeddings-gpu-vm"

echo "========================================================================"
echo "Emergency Stop and Cleanup"
echo "========================================================================"
echo ""
echo "This will DELETE the VM: $VM_NAME"
echo "Any in-progress work will be lost."
echo ""
echo "Are you sure? (type 'yes' to confirm)"
read -r response

if [ "$response" != "yes" ]; then
    echo "Cancelled"
    exit 0
fi

echo ""
echo "Deleting VM..."
gcloud compute instances delete $VM_NAME --zone=$ZONE --quiet 2>/dev/null || echo "VM not found or already deleted"

echo ""
echo "✓ Cleanup complete"
