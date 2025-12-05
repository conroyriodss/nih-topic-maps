# NIH Grant Topic Modeling Project Log

## Date: 2025-11-25 21:18 UTC

### Project Summary

- **Source Data:** NIH ExPORTER grants and PubMed linkage, 50,000-sample (`embedding_sample_v2_50k.jsonl`)
- **Cloud Platform:** GCP (BigQuery, Cloud Shell, Compute Engine, GCS)
- **Objective:** Topical clustering of NIH grants (TF-IDF, PubMedBERT), analytic dashboards, NIH-maps-style networks, and MeSH/RCDC/IC/funding category overlays.
- **Main Products:**
  - `nih_analytics.topic_clusters_tfidf`: 74 grant topic clusters (TF-IDF/kmeans)
  - `nih_analytics.grant_topic_mapping_tfidf`: Grant-to-topic assignments
  - Disease categories, funding categories, IC mappings
  - Interactive dashboards: topic, cluster, RCDC, IC, funding
  - Project-level map of 5k/50k grants using (soon) PubMedBERT embeddings and UMAP coordinates

---

### Pipeline Chronology

**1. Setup & Sampling**
- Extract 50K grants for pilot analysis
- Data stored as `/tmp/data.jsonl` and in GCS: `embedding_sample_v2_50k.jsonl`

**2. Topic Modeling**
- Generate text embeddings (first via TF-IDF, then PubMedBERT)
- Cluster grants:
  - _TF-IDF + k-means (n=74)_; Top terms, IC, funding extracted per cluster
- Define clusters: `topic_clusters_tfidf`, `grant_topic_mapping_tfidf`

**3. Save Results to BigQuery**
- Used pandas-gbq, then switched to direct BigQuery client + bq CLI for resilience
- All tables: `nih_analytics` dataset

**4. Disease & Funding Category Overlays**
- Disease assignment: Rule-based on cluster label keywords (e.g., '%cancer%' → Cancer)
- Funding overlays from `grant_scorecard_v2`
- RCDC mapping: Boolean/array columns for multi-category topics

**5. Interactive Visualization**
- D3.js/Plotly HTML apps for:
    - Topic cluster maps (bubble, force-directed network)
    - Funding category matrix
    - IC network
    - RCDC/MeSH overlays (pipeline ongoing)
    - Project-level network (5k/50k grants; PubMedBERT embedding upgrade in flight)

**6. GCP GPU Workflow**
- VM: n1-standard-4 + NVIDIA T4, with PyTorch GPU image or custom setup
- PubMedBERT embedding script in Python/Torch/Transformers, run on GPU
- Uploaded: `embeddings_pubmedbert_50k.npy`, project coordinate JSONs, and loaded to BigQuery (`project_coordinates_pubmedbert`)

**7. Documentation & Log Sync**
- All scripts for BigQuery, visualization, and batch/VM runs are in `scripts/`
- Visualizations and data exports are in `/tmp/` during development and moved to `viz/` or `data/` in repo

---

### Key File and Table Inventory

| Type             | Artifact/Location                                         | Description                                      |
|------------------|-----------------------------------------------------------|--------------------------------------------------|
| Data sample      | embedding_sample_v2_50k.jsonl (GCS, /tmp)                | 50K grants for analysis                          |
| Cluster/Topic    | topic_clusters_tfidf, grant_topic_mapping_tfidf (BQ)     | Clusters and grant-topic mapping                 |
| Disease mapping  | topic_disease_categories, topic_rcdc_mapping (BQ)        | Label overlays by disease, funding, or RCDC      |
| Project coords   | project_coordinates_2d, project_coordinates_pubmedbert    | Location of each project in UMAP space           |
| Network maps     | map_funding_categories.html, map_by_ic.html, ... (viz/)  | Interactive D3/Plotly HTML network visualizations |
| Embeddings       | embeddings_pubmedbert_50k.npy (GCS)                      | PubMedBERT 768d vectors                          |
| Visualization    | projects_pubmedbert_5k.json, 50k.json (GCS/viz/)         | Grant metadata/coords for maps                   |
| Scripts          | scripts/* (repo)                                         | All automation, viz, ingestion, and analysis     |

---

### Most Recent/Active Commands

\`\`\`bash
# (main VM+embedding setup, run, and cleanup)
gcloud compute instances create ...           # Provision T4 GPU VM
gcloud compute ssh ...                       # SSH to VM
nvidia-smi                                   # Confirm GPU in VM
pip install torch transformers ...            # Install python deps
python3 pubmedbert_gpu.py                    # Generate embeddings and coords
gcloud compute instances delete ...           # Teardown

# Table and data ops:
bq query --use_legacy_sql=false ...           # Run queries for cluster/category/RCDC
bq load ...                                   # Data loads from JSONL to BQ

# Visualization:
cloudshell edit /tmp/map_projects_50k.html   # Review/edit interactive HTML
python3 -m http.server 8080                  # Serve for web preview
cloudshell get-web-preview-url -p 8080       # Get preview link

# GitHub Sync (see below)
\`\`\`

---

### GitHub Sync Steps

\`\`\`bash
cd "$REPO_DIR"

# Stage changes (update as appropriate)
git add PROJECT_LOG.md scripts/ viz/ data/ notebooks/ README.md

# Write a clear commit message
git commit -m "Update: pipeline docs, new visualization scripts, PubMedBERT embedding infra, data exports"

# Push to remote
git push origin main  # or your active branch
\`\`\`

---

### Next Steps

- Monitor PubMedBERT runs, update map scripts for new embedding-based coordinates
- Continue MeSH-based alignment and create map overlays or faceting
- Refine dashboard for export (PDF, PNG, data download, etc.)
- Document limitations and possible next-phase developments

---

> **This log is auto-generated as of $(date). Review and expand as needed for collaborators.**

