#!/bin/bash
# Check if embeddings completed and cleanup VM

PROJECT_ID="od-cl-odss-conroyri-f75a"
ZONE="us-central1-a"
VM_NAME="nih-embeddings-gpu-vm"
BUCKET="od-cl-odss-conroyri-nih-embeddings"

echo "========================================================================"
echo "Checking Results and Cleanup"
echo "========================================================================"
echo ""

# Check if embeddings are in GCS
echo "Checking for PROJECT_TERMS embeddings in GCS..."
if gsutil ls gs://$BUCKET/sample/embeddings_project_terms_50k.parquet 2>/dev/null; then
    echo "✓ Embeddings found in GCS!"
    
    # Get file info
    gsutil ls -lh gs://$BUCKET/sample/embeddings_project_terms_50k.parquet
    gsutil ls -lh gs://$BUCKET/sample/embeddings_manifest_project_terms.json
    
    echo ""
    echo "✓ Embedding generation completed successfully!"
    echo ""
    
    # Check if VM still exists
    if gcloud compute instances describe $VM_NAME --zone=$ZONE 2>/dev/null; then
        echo "VM still exists. Delete it now? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            echo "Deleting VM..."
            gcloud compute instances delete $VM_NAME --zone=$ZONE --quiet
            echo "✓ VM deleted"
        else
            echo "VM kept running. Delete manually later with:"
            echo "  gcloud compute instances delete $VM_NAME --zone=$ZONE"
        fi
    else
        echo "✓ VM already auto-shutdown"
    fi
    
    echo ""
    echo "========================================================================"
    echo "Next Steps:"
    echo "========================================================================"
    echo "1. Cluster PROJECT_TERMS embeddings (K=100):"
    echo "   python3 scripts/06_cluster_project_terms.py --k 100"
    echo ""
    echo "2. Compare with full-text clustering:"
    echo "   python3 scripts/compare_clustering_methods.py"
    
else
    echo "❌ Embeddings not found in GCS yet"
    echo ""
    
    # Check VM status
    if gcloud compute instances describe $VM_NAME --zone=$ZONE 2>/dev/null; then
        echo "VM still exists. Check progress:"
        echo "  bash monitor_gpu_vm.sh"
    else
        echo "VM not found. Something went wrong."
        echo "Check logs or re-run: bash launch_gpu_vm.sh"
    fi
fi
