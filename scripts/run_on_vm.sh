#!/bin/bash
# Run this script ON THE VM via SSH

echo "Setting up clustering environment..."

# Install dependencies if not already installed
sudo apt-get update -qq
sudo apt-get install -y python3-pip python3-venv git -qq

pip3 install --quiet pandas numpy scipy scikit-learn \
     google-cloud-bigquery google-cloud-storage google-cloud-aiplatform \
     vertexai nltk tqdm pyarrow

# Download NLTK data
python3 -c "import nltk; nltk.download('wordnet', quiet=True); nltk.download('omw-1.4', quiet=True)"

# Create working directory
mkdir -p ~/workspace
cd ~/workspace

# Download embeddings from GCS (they're already there from earlier)
echo "Checking for embeddings in GCS..."
gsutil ls gs://od-cl-odss-conroyri-nih-embeddings/embeddings_50k_sample.parquet 2>/dev/null

if [ $? -eq 0 ]; then
    echo "Downloading embeddings from GCS..."
    gsutil cp gs://od-cl-odss-conroyri-nih-embeddings/embeddings_50k_sample.parquet .
else
    echo "ERROR: Embeddings not found in GCS. Need to upload first."
    exit 1
fi

# Copy the script
cp ~/vm_clustering_script.py .

# Run clustering
echo ""
echo "Starting clustering (15-20 minutes)..."
python3 vm_clustering_script.py

# Upload results
if [ -f hierarchical_50k_clustered.csv ]; then
    gsutil cp hierarchical_50k_clustered.csv gs://od-cl-odss-conroyri-nih-embeddings/
    echo "✅ Results uploaded to GCS"
else
    echo "ERROR: Clustering output not found"
    exit 1
fi
