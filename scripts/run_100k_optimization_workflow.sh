#!/bin/bash
# Orchestration script for 100k sample clustering optimization workflow

set -e  # Exit on error

echo "======================================================================"
echo "NIH TOPIC MAPS - 100K CLUSTERING OPTIMIZATION WORKFLOW"
echo "======================================================================"
echo ""

# Configuration
WORK_DIR="$HOME/nih-topic-maps"
SCRIPTS_DIR="$WORK_DIR/scripts"

cd "$WORK_DIR" || exit 1

# Step 1: Create stratified sample
echo "[1/5] Creating stratified 100k sample from BigQuery..."
if [ -f "grants_100k_stratified.parquet" ]; then
    echo "  Sample already exists. Skip? (y/n)"
    read -r SKIP
    if [ "$SKIP" != "y" ]; then
        python3 "$SCRIPTS_DIR/create_100k_stratified_sample.py"
    fi
else
    python3 "$SCRIPTS_DIR/create_100k_stratified_sample.py"
fi

# Step 2: Generate embeddings
echo ""
echo "[2/5] Generating PubMedBERT embeddings..."
if [ -f "embeddings_100k_pubmedbert.parquet" ]; then
    echo "  Embeddings already exist. Skip? (y/n)"
    read -r SKIP
    if [ "$SKIP" != "y" ]; then
        # Modify script 05 to use the 100k sample
        python3 "$SCRIPTS_DIR/05_generate_embeddings_pubmedbert.py" \
            --input grants_100k_stratified.parquet \
            --output embeddings_100k_pubmedbert.parquet
    fi
else
    python3 "$SCRIPTS_DIR/05_generate_embeddings_pubmedbert.py" \
        --input grants_100k_stratified.parquet \
        --output embeddings_100k_pubmedbert.parquet
fi

# Step 3: Hierarchical clustering parameter sweep
echo ""
echo "[3/5] Running hierarchical clustering parameter sweep..."
echo "  This will test multiple linkage methods and distance thresholds"
echo "  Estimated time: 15-30 minutes"
python3 "$SCRIPTS_DIR/hierarchical_param_sweep.py"

# Step 4: Apply best hierarchical clustering
echo ""
echo "[4/5] Applying best hierarchical clustering configuration..."
echo "  Check hierarchical_recommendations.json for best parameters"
echo ""
echo "  Apply best clustering? (y/n)"
read -r APPLY

if [ "$APPLY" = "y" ]; then
    # This would be a new script to apply the best config
    python3 "$SCRIPTS_DIR/apply_hierarchical_clustering.py"
fi

# Step 5: UMAP parameter sweep
echo ""
echo "[5/5] Running UMAP parameter sweep for visualization..."
echo "  This will test multiple UMAP configurations"
echo "  Estimated time: 30-60 minutes"
python3 "$SCRIPTS_DIR/umap_param_sweep.py"

echo ""
echo "======================================================================"
echo "OPTIMIZATION WORKFLOW COMPLETE!"
echo "======================================================================"
echo ""
echo "Results summary:"
echo "  - Hierarchical clustering: hierarchical_param_sweep_results.csv"
echo "  - Best hierarchical config: hierarchical_recommendations.json"
echo "  - UMAP parameters: umap_param_sweep_results.csv"
echo "  - Best UMAP config: umap_recommendations.json"
echo ""
echo "Next steps:"
echo "  1. Review visualizations: hierarchical_param_sweep_results.png"
echo "  2. Review UMAP results: umap_param_sweep_results.png"
echo "  3. Apply best configuration to full 2.09M dataset"
echo "  4. Generate production visualization"
