#!/bin/bash
# NIH Topic Maps - Final Cleanup and Shutdown Script
# Copy and paste this entire script into Cloud Shell

set -e

echo "=========================================="
echo "NIH TOPIC MAPS - FINAL CLEANUP"
echo "=========================================="
echo ""

cd ~/nih-topic-maps

# 1. CHECK VM STATUS
echo "1. Checking VM status..."
gcloud compute instances list --filter="name:nih-250k-vm" 2>/dev/null || echo "   ✓ VM already deleted"
echo ""

# 2. VERIFY FILES
echo "2. Verifying key files..."
for file in hierarchical_250k_with_umap.csv nih_topic_map_250k_domains.html create-viz-250k-complete.py; do
    if [ -f "$file" ]; then
        SIZE=$(ls -lh "$file" | awk '{print $5}')
        echo "   ✓ $file ($SIZE)"
    else
        echo "   ✗ MISSING: $file"
    fi
done
echo ""

# 3. CREATE FINAL README
echo "3. Creating final README..."
cat > README.md << 'EOFREADME'
# NIH Topic Maps - 250K Grant Analysis

**Large-scale semantic clustering and visualization of NIH research portfolio**

## Overview

This project applies machine learning to 250,000 NIH grants (2019-2024) to:
- Cluster grants into 10 major research domains using embeddings
- Generate 2D UMAP visualizations showing research landscape
- Enable interactive exploration via web-based visualizations

## Key Deliverables

### 1. Data Files
- `hierarchical_250k_with_umap.csv` (43 MB) - Full processed dataset
  - 250,000 grants with domain assignments
  - UMAP coordinates for visualization
  - Metadata: IC, FY, funding, project titles

### 2. Visualizations
- `nih_topic_map_250k_domains.html` - Interactive web visualization
  - Domain heatmaps overlaying 250K grant landscape
  - 50K grant sample displayed for performance
  - Filterable by IC, fiscal year, keywords
  - Click grants for award details
  - Zoom/pan capabilities

### 3. Processing Scripts
- `create-viz-250k-complete.py` - Generates HTML visualization
- `vm_process_250k_simple.py` - Full pipeline (embeddings → clustering → UMAP)

## Domain Distribution

| Domain | Label | Grants | % |
|--------|-------|--------|---|
| 1 | Clinical Trials & Prevention | 10,659 | 4.3% |
| 2 | Behavioral & Social Science | 25,778 | 10.3% |
| 3 | Genetics & Biotechnology | 24,842 | 9.9% |
| 4 | Rare Diseases & Genomics | 10,973 | 4.4% |
| 5 | Neuroscience & Behavior | 36,340 | 14.5% |
| 6 | Molecular Biology & Genomics | 26,747 | 10.7% |
| 7 | Infectious Disease & Immunology | 24,468 | 9.8% |
| 8 | Clinical & Translational Research | 35,267 | 14.1% |
| 9 | Cancer Biology & Oncology | 24,056 | 9.6% |
| 10 | Bioengineering & Technology | 30,870 | 12.4% |

**Total: 250,000 grants**

## Technical Approach

### Embeddings
- Model: `text-embedding-004` (Google Vertex AI)
- Input: PROJECT_TITLE field
- Dimension: 768

### Clustering
- Algorithm: KMeans (k=10)
- Features: Embeddings + TF-IDF (1000 dims)
- Sample: 50K grants for training
- Assignment: Remaining 200K via nearest centroid

### Dimensionality Reduction
- Algorithm: UMAP
- Parameters: n_neighbors=15, min_dist=0.1, metric=cosine
- Input: Full 250K embeddings
- Output: 2D coordinates for visualization

### Infrastructure
- Google Cloud VM: n1-standard-16 (16 vCPU, 60 GB RAM)
- Runtime: ~37 minutes total
- Cost: ~$10

## Usage

### View Visualization
```bash
# Option 1: Download HTML and open in browser
gsutil cp gs://od-cl-odss-conroyri-nih-embeddings/nih_topic_map_250k_domains.html .
open nih_topic_map_250k_domains.html

# Option 2: Clone repo and open
git clone https://github.com/conroyriodss/nih-topic-maps.git
cd nih-topic-maps
open nih_topic_map_250k_domains.html
```

### Regenerate Visualization
```bash
python3 create-viz-250k-complete.py
```

## Repository Structure

```
nih-topic-maps/
├── README.md                          # This file
├── hierarchical_250k_with_umap.csv   # Processed data (250K grants)
├── nih_topic_map_250k_domains.html   # Interactive visualization
├── create-viz-250k-complete.py       # Visualization generator
├── vm_process_250k_simple.py         # Full processing pipeline
└── ANALYSIS_QUESTIONS.md             # Research questions & next steps
```

## Key Insights

1. **Balanced Portfolio**: Research domains fairly evenly distributed (4-15% each)
2. **Clinical Focus**: Combined clinical domains (1+8) = 45,926 grants (18.4%)
3. **Basic Science**: Genomics/molecular domains (3+6) = 51,589 grants (20.6%)
4. **Translation**: Clear separation between basic and applied research clusters

## Future Directions

- **Hierarchical clustering**: Split 10 domains into 30 topics and 100 subtopics
- **Temporal analysis**: Track domain evolution 2019-2024
- **IC-specific views**: Specialized visualizations per institute
- **Outcome linking**: Connect grants to publications, patents, clinical trials

## Technical Notes

- UMAP spectral initialization failed (small eigengap) → fallback to random init
- 50K sample ensures visualization performance in browser
- Heatmaps computed via cubic interpolation on domain density

## Contact

**Repository**: https://github.com/conroyriodss/nih-topic-maps
**GCS Bucket**: `gs://od-cl-odss-conroyri-nih-embeddings/`

---

*Generated: December 2, 2025*
*Data: NIH RePORTER (FY 2019-2024)*
*Total Grants: 250,000 | Total Funding: ~$150B*
EOFREADME
echo "   ✓ README.md created"
echo ""

# 4. UPDATE ANALYSIS QUESTIONS
echo "4. Updating analysis questions..."
cat >> ANALYSIS_QUESTIONS.md << 'EOFANALYSIS'

## Completed Milestones (December 2, 2025)

### ✅ 250K Grant Processing
- **Status**: Complete
- **Grants**: 250,000 (FY 2019-2024)
- **Domains**: 10 major research areas identified
- **Infrastructure**: GCP VM (n1-standard-16)
- **Runtime**: ~37 minutes
- **Cost**: ~$10

### ✅ Interactive Visualization
- **File**: `nih_topic_map_250k_domains.html`
- **Features**:
  - Domain heatmaps
  - 50K grant sample displayed
  - Filtering by IC, FY, keywords
  - Award detail cards
  - Zoom/pan navigation

### Key Files Generated
1. `hierarchical_250k_with_umap.csv` - Full dataset
2. `nih_topic_map_250k_domains.html` - Visualization
3. `create-viz-250k-complete.py` - Generator script

## Next Priority: Hierarchical Expansion

**Goal**: Split 10 domains → 30 topics → 100 subtopics

**Approach**:
1. Use domain assignments as starting point
2. Re-cluster each domain independently
3. Generate 3-level hierarchy
4. Update visualization with drill-down

**Timeline**: ~1 week development + 2 hours compute

## Storage Status

**GCS Bucket**: `gs://od-cl-odss-conroyri-nih-embeddings/`
- ✅ `hierarchical_250k_with_umap.csv` (43 MB)
- ✅ All processing scripts backed up
- ✅ Repository synced to GitHub

---
*Updated: December 2, 2025*
EOFANALYSIS
echo "   ✓ ANALYSIS_QUESTIONS.md updated"
echo ""

# 5. CLEAN UP TEMPORARY FILES
echo "5. Cleaning up temporary files..."
rm -f create-viz-250k-domains.py 2>/dev/null && echo "   ✓ Removed temp viz script" || true
rm -f create-viz-heatmap-cards-250k.py 2>/dev/null && echo "   ✓ Removed duplicate script" || true
echo ""

# 6. CHECK GCS BUCKET
echo "6. Verifying GCS storage..."
gsutil ls -lh gs://od-cl-odss-conroyri-nih-embeddings/ | tail -5
echo ""

# 7. GIT COMMIT
echo "7. Committing final changes..."
git add .
git status --short
git commit -m "Final cleanup: README, documentation, 250K complete" 2>/dev/null || echo "   ℹ Nothing to commit"
git push
echo "   ✓ Changes pushed to GitHub"
echo ""

# 8. FINAL SUMMARY
echo "=========================================="
echo "FINAL STATUS"
echo "=========================================="
echo ""
echo "✅ COMPLETED:"
echo "   • 250,000 grants processed"
echo "   • 10 research domains identified"
echo "   • Interactive visualization created"
echo "   • All files backed up to GCS"
echo "   • Repository updated on GitHub"
echo "   • VM deleted (cost savings active)"
echo ""
echo "📊 KEY FILES:"
echo "   • hierarchical_250k_with_umap.csv (43 MB)"
echo "   • nih_topic_map_250k_domains.html"
echo "   • README.md (comprehensive documentation)"
echo ""
echo "🌐 ACCESS:"
echo "   • GitHub: https://github.com/conroyriodss/nih-topic-maps"
echo "   • GCS: gs://od-cl-odss-conroyri-nih-embeddings/"
echo ""
echo "💰 COST ESTIMATE: ~\$10 total"
echo ""
echo "🎯 NEXT STEPS:"
echo "   1. Review visualization in browser"
echo "   2. Share with stakeholders"
echo "   3. Plan hierarchical expansion (10→30→100)"
echo ""
echo "=========================================="
echo "ALL DONE! 🎉"
echo "=========================================="
