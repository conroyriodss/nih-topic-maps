#!/bin/bash
# Deploy code to GPU VM and run embedding generation

set -e

PROJECT_ID="od-cl-odss-conroyri-f75a"
ZONE="us-central1-a"
VM_NAME="nih-embeddings-gpu-vm"

echo "========================================================================"
echo "Deploying Code and Running Embedding Generation"
echo "========================================================================"
echo ""

# Verify VM is running
if ! gcloud compute instances describe $VM_NAME --zone=$ZONE 2>/dev/null; then
    echo "❌ VM $VM_NAME not found!"
    echo "Run: bash launch_gpu_vm.sh"
    exit 1
fi

# Create remote directory
echo "Setting up remote directory..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command="mkdir -p ~/nih-topic-maps/scripts"

# Copy the embedding script
echo "Copying embedding generation script..."
gcloud compute scp scripts/05b_generate_embeddings_project_terms.py \
    $VM_NAME:~/nih-topic-maps/scripts/ --zone=$ZONE

# Create and copy auto-shutdown script
cat > /tmp/run_with_autoshutdown.sh << 'INNER_EOF'
#!/bin/bash
# Run embedding generation and auto-shutdown on completion

echo "========================================================================"
echo "Starting PROJECT_TERMS Embedding Generation with Auto-Shutdown"
echo "========================================================================"
echo ""
echo "Checking GPU..."
nvidia-smi
echo ""

cd ~/nih-topic-maps

# Run the embedding script
echo "Starting embedding generation..."
python3 scripts/05b_generate_embeddings_project_terms.py

EXIT_CODE=$?

echo ""
echo "========================================================================"
echo "Embedding Generation Complete!"
echo "Exit code: $EXIT_CODE"
echo "========================================================================"
echo ""

if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Success! Results uploaded to GCS."
    echo "  Shutting down VM in 60 seconds..."
    echo "  (Cancel with Ctrl+C if you want to keep VM running)"
    sleep 60
    sudo shutdown -h now
else
    echo "❌ Error occurred. NOT shutting down automatically."
    echo "   SSH to VM to investigate: gcloud compute ssh $VM_NAME --zone=$ZONE"
    exit $EXIT_CODE
fi
INNER_EOF

gcloud compute scp /tmp/run_with_autoshutdown.sh $VM_NAME:~/nih-topic-maps/ --zone=$ZONE
gcloud compute ssh $VM_NAME --zone=$ZONE --command="chmod +x ~/nih-topic-maps/run_with_autoshutdown.sh"

echo ""
echo "========================================================================"
echo "Ready to Start!"
echo "========================================================================"
echo ""
echo "The embedding generation will:"
echo "  1. Process 50K grants with PROJECT_TERMS"
echo "  2. Generate PubMedBERT embeddings (768-dim)"
echo "  3. Upload results to GCS"
echo "  4. Auto-shutdown VM when complete (~15-30 min)"
echo ""
echo "Start now with:"
echo "  gcloud compute ssh $VM_NAME --zone=$ZONE --command='nohup ~/nih-topic-maps/run_with_autoshutdown.sh > ~/embedding.log 2>&1 &'"
echo ""
echo "Monitor progress:"
echo "  gcloud compute ssh $VM_NAME --zone=$ZONE --command='tail -f ~/embedding.log'"
echo ""
echo "Or run interactively (no auto-shutdown):"
echo "  gcloud compute ssh $VM_NAME --zone=$ZONE"
echo "  cd ~/nih-topic-maps && python3 scripts/05b_generate_embeddings_project_terms.py"
