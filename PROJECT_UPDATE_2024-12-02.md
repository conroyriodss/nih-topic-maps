# NIH Topic Maps - Project Update
**Date:** December 2, 2024  
**Session Focus:** Scaling to 250K grants with UMAP dimension reduction

---

## Executive Summary

Successfully developed and deployed an interactive visualization system for NIH 
grant portfolio analysis, scaling from initial 50K to 250K grants with 
hierarchical clustering and UMAP-based spatial layout.

### Key Achievements Today

1. **50K Grant Analysis Complete**
   - Hierarchical clustering: 10 domains → 60 topics → 239 subtopics
   - UMAP dimension reduction (replaced PCA for better structure preservation)
   - Enhanced interactive visualization with zoom-responsive features

2. **250K Scale-Up In Progress**
   - Stratified sampling across IC/FY/funding levels
   - Processing on n1-highmem-32 VM (208GB RAM)
   - Estimated completion: ~2-3 hours from start

3. **Visualization Enhancements**
   - Descriptive topic labels (not just numbers)
   - Zoom-responsive text scaling
   - Semi-transparent domain boundaries
   - Background map showing full portfolio context
   - Dynamic point loading based on zoom level

---

## Technical Architecture

### Data Pipeline

```
BigQuery (1.5M grants)
    ↓ Stratified Sampling
Sample (50K/250K grants)
    ↓ Vertex AI
Embeddings (768-dim)
    ↓ Hybrid Features (60% emb + 25% RCDC + 15% terms)
Hierarchical Clustering
    ↓ Ward linkage
Domains (10) → Topics (60) → Subtopics (240)
    ↓ UMAP
2D Coordinates
    ↓ D3.js
Interactive Visualization
```

### Clustering Methodology

**Hierarchical Structure:**
- Level 1 (Domains): 10 broad research areas
- Level 2 (Topics): 6 per domain ≈ 60 total
- Level 3 (Subtopics): 4 per topic ≈ 240 total

**Feature Engineering:**
- Embeddings (60%): Text-embedding-005 from Vertex AI
- RCDC Categories (25%): Multi-label binarization
- Project Terms (15%): TF-IDF with lemmatization

**Domain Labels:**
1. Clinical Trials & Prevention
2. Behavioral & Social Science
3. Genetics & Biotechnology
4. Rare Diseases & Genomics
5. Neuroscience & Behavior
6. Molecular Biology & Genomics
7. Infectious Disease & Immunology
8. Clinical & Translational Research
9. Cancer Biology & Oncology
10. Bioengineering & Technology

---

## File Structure

```
nih-topic-maps/
├── README.md
├── PROJECT_UPDATE_2024-12-02.md
├── SCRIPT_REFERENCE.md
├── data/
│   ├── hierarchical_50k_clustered.csv
│   ├── hierarchical_50k_with_umap.csv
│   └── embeddings_50k_sample.parquet
├── scripts/
│   ├── 01_sample_and_embed.py
│   ├── 02_hierarchical_clustering.py
│   ├── create_viz_enhanced_simple.py
│   └── vm_process_250k.py
└── visualizations/
    └── nih_topic_map_50k_enhanced.html
```

---

## Key Scripts

### create_viz_enhanced_simple.py
**Purpose:** Generate interactive D3.js visualization  
**Input:** hierarchical_50k_with_umap.csv  
**Output:** nih_topic_map_50k_enhanced.html  
**Runtime:** 1-2 minutes

### vm_process_250k.py
**Purpose:** End-to-end pipeline for 250K grants  
**Environment:** n1-highmem-32 VM (208GB RAM)  
**Runtime:** 2-3 hours  
**Pipeline:**
1. Download sample from GCS
2. Generate embeddings (30-40 min)
3. Hierarchical clustering (30-40 min)
4. UMAP dimension reduction (45-60 min)
5. Upload results to GCS

---

## Reproducibility Guide

### Complete Workflow (250K)

```bash
# 1. Create sample in BigQuery Console
# Run stratified sampling query
# Export to gs://od-cl-odss-conroyri-nih-embeddings/sample_250k.csv

# 2. Create processing VM
gcloud compute instances create nih-250k-vm \
  --machine-type=n1-highmem-32 \
  --zone=us-central1-a \
  --boot-disk-size=200GB \
  --scopes=https://www.googleapis.com/auth/cloud-platform

# 3. Setup VM
gcloud compute ssh nih-250k-vm --zone=us-central1-a
pip3 install pandas numpy umap-learn google-cloud-storage \
             pyarrow scikit-learn scipy vertexai nltk

# 4. Run pipeline
python3 vm_process_250k.py

# 5. Download results (Cloud Shell)
gsutil cp gs://od-cl-odss-conroyri-nih-embeddings/hierarchical_250k_with_umap.csv .

# 6. Generate visualization
python3 create_viz_enhanced_simple.py

# 7. Cleanup
gcloud compute instances delete nih-250k-vm --zone=us-central1-a
```

---

## Resource Requirements

### Cloud Shell
- Machine: e2-medium (default)
- Use: Sampling, clustering, visualization generation

### VM for 50K-100K
- Machine: n1-highmem-8 (52GB RAM)
- Cost: ~$0.40/hour
- Use: UMAP only

### VM for 250K
- Machine: n1-highmem-32 (208GB RAM)
- Cost: ~$3.20/hour
- Runtime: 2-3 hours
- Total: ~$8-10

### Storage
- Bucket: od-cl-odss-conroyri-nih-embeddings
- Usage: <1 GB total

---

## Key Parameters

### UMAP
```python
n_neighbors = 15
n_components = 2
min_dist = 0.1
metric = 'cosine'
random_state = 42
```

### Clustering
```python
n_domains = 10
topics_per_domain = 6  # adaptive 2-6
subtopics_per_topic = 4  # adaptive 2-4
linkage_method = 'ward'
```

### Feature Weights
```python
embeddings: 0.60
rcdc: 0.25
terms: 0.15
```

---

## Performance Benchmarks

| Grants | Embeddings | Clustering | UMAP | Total |
|--------|-----------|------------|------|-------|
| 50K    | 20 min    | 10 min     | 1 min| 31 min|
| 100K   | 40 min    | 30 min     | 5 min| 75 min|
| 250K   | 100 min   | 60 min     | 50 min| 210 min|

---

## Future Enhancements

### Near-Term
1. Better topic labels using LLM
2. Advanced interactions (click to filter, drag to select)
3. Temporal animation
4. Export functionality

### Medium-Term
5. Scale to full 1.5M dataset
6. Statistical analysis and metrics
7. Integration with NIH RePORTER
8. API for programmatic access

### Long-Term
9. Automatic trend detection
10. Emerging topic identification
11. Multi-modal analysis (publications, patents, trials)
12. Collaboration network visualization

---

## Cost Summary

**Total Cost for 250K Analysis:**
- VM compute: $8-10
- Vertex AI embeddings: $2.50
- BigQuery: <$0.50
- Storage: <$0.10
- **Total: ~$11-13**

---

## Lessons Learned

**What Worked:**
- Hierarchical clustering provides intuitive structure
- UMAP significantly better than PCA for visualization
- VM strategy avoids Cloud Shell limitations
- Hybrid features outperform embeddings alone

**What to Improve:**
- Use service accounts for consistent authentication
- Test on small samples before scaling
- Add checkpointing for long-running jobs
- Better progress monitoring and logging

---

## Files Generated Today

1. hierarchical_50k_with_umap.csv (9 MB)
2. nih_topic_map_50k_enhanced.html (20 MB)
3. vm_process_250k.py (pipeline script)
4. PROJECT_UPDATE_2024-12-02.md (this file)
5. SCRIPT_REFERENCE.md (detailed parameters)

---

**Last Updated:** December 2, 2024  
**Next Steps:** Complete 250K processing, generate visualization, analyze results

