# Context for Next Session

_Last updated: 2025-11-25_

## Project Summary

NIH Topic Maps builds interactive visualizations of NIH ExPORTER grant data using PubMedBERT embeddings and clustering over ~50,000 grants (FY 2000–2024). The current public entry point is `index.html`, which links to a hosted interactive topic map and topic metadata JSON in Google Cloud Storage.

## Current Architecture

- **Data source:** NIH ExPORTER parquet files (1990–2024) in `gs://od-cl-odss-conroyri-nih-embeddings/exporter/`
- **Catalog/summary:** `data/EXPORTER_SUMMARY.md`, `data/exporter_catalog.json`, `data/parquet_inspection_summary.json`
- **Processing scripts (in `scripts/`):**
  - `01_download_nih_data.sh` and `01_download_nih_data_api.py` – discovery and download of ExPORTER data
  - `02_load_discovered_parquet.py`, `03_create_unified_tables.py` – load and unify projects/abstracts/link tables
  - `04_create_sample.py` – construct 50K grant sample (2000–2024)
  - `05_generate_embeddings_pubmedbert.py` – compute PubMedBERT embeddings for grant texts
  - `10_setup_bigquery_full.py`, `11_find_and_load_data.py`, `18_load_all_years.sh` – BigQuery dataset and table loading
- **Visualization:**
  - Iterative HTML visualizations: `create_full_viz.html`, `create_full_viz_v2.html` … `create_full_viz_v6.html`
  - Public-facing landing page: `index.html`
  - IC legend: `ic_mapping.json`

## GCP / BigQuery Context

- **GCP project:** `od-cl-odss-conroyri-f75a`
- **GCS buckets:** main ExPORTER and embedding storage at `gs://od-cl-odss-conroyri-nih-embeddings/`
- **BigQuery dataset:** contains at least:
  - Projects tables by year (1990–2024)
  - Abstracts tables by year (1990–2024)
  - Link tables by year (1990–2024)
  - Sample/embedding tables for the 50K grants used in the visualization

(Exact table names should be verified and documented in the next step when inspecting BigQuery.)

## What Is Working Now

- End‑to‑end path from ExPORTER parquet → unified tables → sample → PubMedBERT embeddings
- K‑Means clustering into 74 topics
- Interactive visualization (v6) with:
  - 2D projection of grants
  - Color‑coded topics (74)
  - IC color mapping (27 ICs)
  - Index page showing counts and links to:
    - Hosted topic map HTML
    - Topic metadata JSON

## Open Questions / Next Steps

1. **BigQuery verification (Priority now):**
   - Enumerate all datasets and tables in the project
   - Confirm schema of:
     - Projects, abstracts, link tables
     - Embedding/sample tables
   - Confirm row counts and time coverage (by FY)
   - Document canonical table names to be used by downstream analysis/visualizations

2. **Documentation:**
   - Add a top‑level `README.md` explaining:
     - Setup (GCP, Python environment, APIs)
     - Data pipeline (scripts ordering, expected inputs/outputs)
     - How to regenerate embeddings and visualizations
   - Keep `CONTEXT_FOR_NEXT_SESSION.md` updated with decisions and TODOs

3. **Analysis Enhancements (future work):**
   - Temporal analysis of topics (2000–2024)
   - IC‑specific topic portfolios and co‑funding patterns
   - Topic stability and emerging/declining themes

4. **Visualization Enhancements (future work):**
   - Grant‑level tooltips (title, IC, FY, amount, key terms)
   - Filters (IC, FY range, mechanism, topic)
   - Time slider or animation for topic evolution
   - Performance optimization for >50K points (WebGL, progressive rendering)

## Next Session Plan

- Start by:
  1. Connecting to BigQuery in project `od-cl-odss-conroyri-f75a`
  2. Listing datasets and tables
  3. For each key table, recording:
     - Dataset.table name
     - Approximate row count
     - Key fields (especially identifiers linking to embeddings and topics)

- Then update this file with:
  - Verified table inventory
  - Any schema surprises or quality issues
  - Decisions on which tables will serve as the “system of record” for:
    - Grants
    - Embeddings
    - Topics
    - IC mappings

## Scorecard Tables (Complete)

| Scorecard | Description | Key Features |
|-----------|-------------|--------------|
| grant_scorecard | Grant-level rollup | Subprojects, outputs, timelines |
| pi_scorecard | PI career metrics | Funding tiers, productivity, multi-IC |
| institution_scorecard | Institutional portfolios | Geography, types, outputs |
| ic_scorecard_enhanced | IC comparisons | Portfolio size, productivity metrics |


## Visualization Status (Nov 26, 2025)

✅ **Working visualization hosted at:**
`https://storage.googleapis.com/od-cl-odss-conroyri-nih-embeddings/sample/topic_map_interactive.html`

**Data Pipeline:**
- 50K sample from FY 2000-2024
- PubMedBERT embeddings (228 MB parquet in GCS)
- UMAP 2D coordinates (1 MB parquet in GCS)  
- 74 topics via K-means
- viz_data.json (12.35 MB) loaded by interactive HTML

**Note:** Embeddings stored in GCS only, not BigQuery. This is fine for visualization purposes.
