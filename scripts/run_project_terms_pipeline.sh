#!/bin/bash
# Complete pipeline for PROJECT_TERMS clustering

echo "========================================================================"
echo "PROJECT_TERMS Clustering Pipeline"
echo "========================================================================"
echo ""

# Step 1: Check K optimization results
echo "Step 1: Checking K optimization results..."
python3 scripts/check_k_results.py
echo ""

# Step 2: Generate PROJECT_TERMS embeddings
echo "========================================================================"
echo "Step 2: Generating PROJECT_TERMS embeddings..."
echo "========================================================================"
python3 scripts/05b_generate_embeddings_project_terms.py

echo ""
echo "========================================================================"
echo "Pipeline Status"
echo "========================================================================"
echo "✓ K optimization checked"
echo "✓ PROJECT_TERMS embeddings generated"
echo ""
echo "Next steps:"
echo "  1. Cluster with optimal K (after checking K results)"
echo "  2. Compare PROJECT_TERMS vs full text clustering"
echo ""
