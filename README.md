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
