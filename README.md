# NIH Topic Maps Project

Interactive visualization and analysis of NIH grants using PubMedBERT embeddings and topic modeling.

## 🔗 Live Demo

**[View Interactive Visualization](https://storage.googleapis.com/od-cl-odss-conroyri-nih-embeddings/sample/topic_map_interactive.html)**

## 📊 Overview

- **Data**: 2.6M NIH ExPORTER grants (1990-2024), deduplicated to 2.09M unique projects
- **Sample**: 50,000 grants (FY 2000-2024) with funding data
- **Embeddings**: PubMedBERT 768-dimensional vectors
- **Topics**: 74 clusters (K-means) - currently being optimized to 150
- **Visualization**: Interactive 2D UMAP projection with filtering

## 📈 Key Statistics

| Metric | Value |
|--------|-------|
| **Total Funding** | $781.71B (FY 2000-2024) |
| **Active ICs** | 27 institutes/centers |
| **Fiscal Years** | 35 years (1990-2024) |
| **Abstracts** | 2.33M matched (88% coverage) |

## 🗂️ Repository Structure

    nih-topic-maps/
    ├── CONTEXT_FOR_NEXT_SESSION.md  # Session continuity
    ├── PROJECT_LOG.md                # Development history
    ├── scripts/
    │   ├── validation/               # Data quality checks
    │   ├── analyze_clustering.py     # Cluster quality analysis
    │   └── find_optimal_k.py         # K optimization
    ├── archive/
    │   └── visualizations/           # Old viz versions
    └── create_full_viz_v6.html       # Current visualization

## 🗄️ BigQuery Datasets

| Dataset | Description | Rows |
|---------|-------------|------|
| `nihexporter` | Raw source data | 2.64M projects |
| `nihprocessed` | Deduplicated projects | 2.09M unique |

## 🚀 Quick Start

See [CONTEXT_FOR_NEXT_SESSION.md](./CONTEXT_FOR_NEXT_SESSION.md) for latest status.

## 📝 Current Work (Nov 26, 2025)

- ✅ Data validation complete
- ✅ Visualization working with 50K sample
- 🔄 Optimizing clustering (K=74 → K=150 per NIH Maps standard)
- 📋 Next: Improve topic labels and UMAP parameters

---

*Last updated: November 26, 2025*
