#!/bin/bash
# Create and configure a high-memory VM for 50k clustering

PROJECT_ID="od-cl-odss-conroyri-f75a"
ZONE="us-central1-a"
VM_NAME="nih-clustering-vm"
MACHINE_TYPE="n1-highmem-8"  # 8 vCPUs, 52 GB RAM
DISK_SIZE="200GB"

echo "=============================================="
echo "Creating High-Memory VM for NIH Clustering"
echo "=============================================="
echo ""
echo "Configuration:"
echo "  Machine: $MACHINE_TYPE (8 vCPUs, 52 GB RAM)"
echo "  Disk: $DISK_SIZE"
echo "  Estimated cost: ~$0.50/hour"
echo ""

# Create VM
gcloud compute instances create $VM_NAME \
  --project=$PROJECT_ID \
  --zone=$ZONE \
  --machine-type=$MACHINE_TYPE \
  --boot-disk-size=$DISK_SIZE \
  --boot-disk-type=pd-standard \
  --image-family=debian-11 \
  --image-project=debian-cloud \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --metadata=startup-script='#!/bin/bash
    # Install Python and dependencies
    apt-get update
    apt-get install -y python3-pip python3-venv git
    
    # Create workspace
    mkdir -p /workspace
    cd /workspace
    
    # Install Python packages
    pip3 install --upgrade pip
    pip3 install pandas numpy scipy scikit-learn \
                 google-cloud-bigquery google-cloud-aiplatform \
                 vertexai nltk tqdm pyarrow
    
    # Download NLTK data
    python3 -c "import nltk; nltk.download(\"wordnet\"); nltk.download(\"omw-1.4\")"
    
    echo "VM setup complete" > /workspace/setup_complete.txt
  '

echo ""
echo "✅ VM creation initiated"
echo ""
echo "Next steps:"
echo "  1. Wait 2-3 minutes for VM to start"
echo "  2. Connect: gcloud compute ssh $VM_NAME --zone=$ZONE"
echo "  3. Transfer your files"
echo "  4. Run clustering on VM"
echo ""
echo "To check VM status:"
echo "  gcloud compute instances describe $VM_NAME --zone=$ZONE"
echo ""
echo "To delete VM when done (IMPORTANT - saves costs):"
echo "  gcloud compute instances delete $VM_NAME --zone=$ZONE"
echo ""
