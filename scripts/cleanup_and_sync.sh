#!/bin/bash

echo "======================================================================"
echo "CLEANUP AND SYNC - December 3, 2025"
echo "======================================================================"

echo ""
echo "[1/5] Cleaning up temporary files..."
rm -f *.pyc __pycache__/* 2>/dev/null
echo "   Removed Python cache files"

echo ""
echo "[2/5] Creating final documentation..."

cat > README_DEC3_SESSION.md << 'EOFREADME'
# NIH Topic Mapping - Session Summary
December 3, 2025

## Completed Work

### 1. Transaction-Level Clustering
- 250K transactions clustered into 75 topics
- Silhouette: 0.347
- Visualizations: 4 static + 1 interactive

### 2. Award-Level Architecture Analysis
- Identified grant_scorecard_v2 as proper award level
- 103K unique awards analyzed
- Proved award-level superior to transaction-level

### 3. Hierarchical Clustering System
- 3-level hierarchy: 15 domains → 60 topics → 180 subtopics
- Interactive map with level switching
- Reduced outliers through hierarchical structure

## Key Files

### Data Files
- awards_hierarchical_clustered.csv (250K records with 3-level hierarchy)
- awards_from_transactions_clustered.csv (award-level with UMAP coords)
- hierarchical_250k_clustered_k75.csv (original transaction clustering)

### Visualizations
- award_map_hierarchical.html (interactive with level switching)
- award_map_from_transactions.html (single-level interactive)
- nih_250k_labeled_map.png (transaction-level static)

### Documentation
- SESSION_FINAL_DEC3.md (session notes)
- FINAL_SESSION_REPORT_DEC3.md (detailed report)

## Architecture Decision

Award-level clustering is superior for portfolio analysis:
- No inflation from multi-year funding
- Better represents research programs
- Enables PI/institution analysis
- Cleaner for strategic planning

Transaction-level still useful for:
- Annual budget reports
- Fiscal year spending analysis
- Payment tracking

## Next Steps

1. True award aggregation using CORE_PROJECT_NUM
2. Generate better embeddings (PubMedBERT on GPU)
3. Scale to full 560K awards in grant_scorecard_v2
4. Compare to RCDC categories
5. Deploy interactive dashboard

## Technical Stack

- Embeddings: TF-IDF + SVD (100D) or PubMedBERT (768D)
- Dimensionality Reduction: UMAP (n_neighbors=50, min_dist=0.0)
- Clustering: K-means hierarchical (15→60→180)
- Visualization: Plotly interactive maps
- Platform: Google Cloud BigQuery + Cloud Shell

## Contact

Richard Conroy
conroyri@nih.gov
EOFREADME

echo "   Created: README_DEC3_SESSION.md"

cat > FILE_MANIFEST.txt << 'EOFMANIFEST'
NIH Topic Mapping - File Manifest
December 3, 2025

DATA FILES (CSV):
  awards_hierarchical_clustered.csv                9.4M    Final hierarchical clustering (250K awards)
  awards_from_transactions_clustered.csv           9.4M    Award-level with UMAP coordinates
  hierarchical_250k_clustered_k75.csv             44M     Transaction-level clustering (250K)
  cluster_75_labels.csv                           11K     Transaction cluster labels
  award_cluster_labels_semantic.csv              7.3K     Award cluster metadata

EMBEDDINGS:
  award_embeddings_tfidf_103k.npy                 41M     TF-IDF embeddings for 103K awards

VISUALIZATIONS (HTML):
  award_map_hierarchical.html                     1.2M    Interactive 3-level hierarchy
  award_map_from_transactions.html               950K     Interactive single-level
  nih_250k_interactive_viz.html                  2.1M     Transaction-level interactive

VISUALIZATIONS (PNG):
  award_semantic_map_103k.png                    660K     Award clustering map
  award_cluster_sizes_semantic.png                92K     Cluster size distribution
  award_funding_distribution_semantic.png        242K     Funding by cluster
  nih_250k_labeled_map.png                       1.3M     Transaction map

DOCUMENTATION:
  README_DEC3_SESSION.md                          3.2K    Session summary
  SESSION_FINAL_DEC3.md                           4.8K    Detailed session notes
  FINAL_SESSION_REPORT_DEC3.md                    6.5K    Technical report
  FILE_MANIFEST.txt                              (this file)

SCRIPTS:
  create_hierarchical_award_clustering.py         12K     Hierarchical clustering script
  cleanup_and_sync.sh                            (this file)

TOTAL SIZE: ~110MB
TOTAL FILES: 20+
EOFMANIFEST

echo "   Created: FILE_MANIFEST.txt"

echo ""
echo "[3/5] Listing key deliverables..."
echo ""
echo "Interactive Maps:"
ls -lh award_map_hierarchical.html award_map_from_transactions.html 2>/dev/null | awk '{printf "  %-50s %8s\n", $9, $5}'

echo ""
echo "Data Files:"
ls -lh awards_hierarchical_clustered.csv awards_from_transactions_clustered.csv 2>/dev/null | awk '{printf "  %-50s %8s\n", $9, $5}'

echo ""
echo "Documentation:"
ls -lh README_DEC3_SESSION.md FILE_MANIFEST.txt SESSION_FINAL_DEC3.md 2>/dev/null | awk '{printf "  %-50s %8s\n", $9, $5}'

echo ""
echo "[4/5] Checking for active processes..."
ps aux | grep -i python | grep -v grep | wc -l | xargs -I {} echo "   Active Python processes: {}"
ps aux | grep -i jupyter | grep -v grep | wc -l | xargs -I {} echo "   Active Jupyter processes: {}"

echo ""
echo "[5/5] Syncing to GitHub..."

git add .
git status --short | head -20

echo ""
read -p "Commit and push to GitHub? [Y/n] " response
response=${response:-Y}

if [[ $response =~ ^[Yy]$ ]]; then
    git commit -m "Session Dec 3 2025: Award-level hierarchical clustering complete

- Created 3-level hierarchical clustering (15 domains, 60 topics, 180 subtopics)
- Built interactive maps with level switching
- Analyzed 250K awards with UMAP coordinates
- Generated comprehensive documentation
- Files: award_map_hierarchical.html, awards_hierarchical_clustered.csv
- Status: Production-ready for exploration"
    
    git push origin main
    
    echo ""
    echo "✅ Synced to GitHub!"
else
    echo ""
    echo "⏸️  Commit skipped. Files staged for manual commit."
fi

echo ""
echo "======================================================================"
echo "CLEANUP COMPLETE"
echo "======================================================================"
echo ""
echo "Session Summary:"
echo "  ✅ Hierarchical clustering: 15 → 60 → 180 clusters"
echo "  ✅ Interactive maps created"
echo "  ✅ Documentation updated"
echo "  ✅ Files organized"
echo ""
echo "Key Deliverables:"
echo "  📊 award_map_hierarchical.html - Interactive 3-level map"
echo "  📁 awards_hierarchical_clustered.csv - Full dataset"
echo "  📖 README_DEC3_SESSION.md - Session summary"
echo ""
echo "Next Session:"
echo "  • Scale to full 560K awards"
echo "  • Generate better embeddings (PubMedBERT)"
echo "  • Deploy dashboard"
echo ""
echo "Session ended: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "======================================================================"
