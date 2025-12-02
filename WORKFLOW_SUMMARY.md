# NIH Topic Maps - 50K Hierarchical Clustering Workflow

**Date:** December 2, 2025  
**Dataset:** 1.5M NIH grants (FY 2000-2024)  
**Sample:** 50,000 grants (stratified by IC, FY, funding level)

## Workflow Overview

### Phase 1: Data Preparation ✅
1. **Created 50k Stratified Sample**
   - Query: BigQuery stratified sampling
   - Strata: IC_NAME × FY × Funding_Level (Low/Med/High)
   - Output: `sample_50k_stratified.parquet`
   - Time: 3 minutes
   - Coverage: All 75 ICs, FY 2000-2024, $25.87B total

### Phase 2: Embedding Generation ✅
1. **Method:** Vertex AI text-embedding-005
   - Dimensions: 768 (consistent with PubMedBERT)
   - Batch size: 250 grants/batch
   - Input: PROJECT_TITLE
   - Output: `embeddings_50k_sample.parquet`
   - Time: 4 minutes
   - Quality: 100% non-zero embeddings, mean norm = 1.00

### Phase 3: Hierarchical Clustering 🔄 IN PROGRESS
**Running on:** GCE n1-highmem-8 (52GB RAM, 8 vCPUs)

**Methodology:**
- **Level 1: 10 Scientific Domains**
  - Method: Ward hierarchical clustering
  - Features: Hybrid (60% embeddings + 25% RCDC + 15% terms)
  - Labels: Manually curated based on RCDC analysis
  
- **Level 2: ~60 Topics** (6 per domain)
  - Method: Sub-clustering within each domain
  - Labels: Most distinctive RCDC category per topic
  
- **Level 3: ~240 Subtopics** (4 per topic)
  - Method: Sub-clustering within each topic
  - Labels: Inherited from topic hierarchy

**Domain Classification:**
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

**Key Features:**
- ✅ Clusters by TYPE OF SCIENCE (not by IC/administrative structure)
- ✅ Lemmatized terms to group related concepts
- ✅ TF-IDF weighting for distinctive scientific vocabulary
- ✅ Hierarchical structure supports drill-down navigation

**Estimated completion:** 15-20 minutes from start  
**Output:** `hierarchical_50k_clustered.csv` → GCS

### Phase 4: Visualization (NEXT)
1. Add UMAP 2D coordinates
2. Refine topic labels with distinctiveness scoring
3. Create interactive HTML with:
   - Background layer (all 50k grants, semi-transparent)
   - Foreground layer (filtered selection)
   - Domain/Topic/Subtopic view modes
   - Multi-select filters (IC, FY sliders)
   - Cluster labels on centroids
   - Zoom-responsive label sizing

### Phase 5: Deployment (PLANNED)
- Deploy to Google Cloud Storage
- Public URL for web access
- Export BigQuery table for queryability

## Technical Decisions

### Why Hierarchical vs K-Means?
- **Hierarchical**: Natural drill-down (Domain → Topic → Subtopic)
- **Ward linkage**: Minimizes within-cluster variance
- **Deterministic**: Reproducible results

### Why Hybrid Features?
- **Embeddings (60%)**: Capture semantic meaning
- **RCDC (25%)**: Leverage NIH's expert categorization
- **Terms (15%)**: Add specificity (e.g., "Alzheimer", "HIV")

### Why Vertex AI Embeddings vs PubMedBERT?
- **Faster**: 4 min vs 15 min for 50k
- **No dependencies**: Avoids torch/torchvision conflicts
- **Same dimensions**: 768-dim, comparable quality
- **API-based**: No local compute requirements

## Key Files

### Data Files
- `sample_50k_stratified.parquet` - Base 50k sample with metadata
- `embeddings_50k_sample.parquet` - With 768-dim embeddings
- `hierarchical_50k_clustered.csv` - Final clustering results

### Scripts
- `scripts/create_50k_stratified_sample.py` - BigQuery sampling
- `scripts/generate_embeddings_50k_vertex.py` - Vertex AI embeddings
- `vm_clustering_script.py` - Hierarchical clustering (runs on VM)
- `run_on_vm.sh` - VM setup and execution wrapper

### Visualization
- `hierarchical_viz_deployment/index_optimized.html` - Interactive viz (12k version)
- Will update with 50k version after clustering completes

## Resource Usage

### Cloud Shell Limitations (why we used VM)
- Disk: 5GB (100% full with 50k features)
- RAM: ~8GB (insufficient for linkage matrix)
- Killed at clustering step

### GCE VM (n1-highmem-8)
- RAM: 52GB (sufficient for 50k × 1,500 features)
- Disk: 200GB
- Cost: ~$0.50/hour
- Estimated total cost: ~$0.35 for this job

## Lessons Learned

1. **Stratified sampling crucial** - Preserves IC/FY distribution
2. **Vertex AI embeddings** - Fast, reliable, no local dependencies
3. **VM for heavy compute** - Cloud Shell insufficient for 50k
4. **Lemmatization essential** - Groups cell/cells, protein/proteins
5. **Domain labels need curation** - Auto-labeling too generic
6. **Background layer helpful** - Shows full context while filtering

## Next Session Checklist

When clustering completes:
- [ ] Download results from GCS
- [ ] Add UMAP coordinates (can do in Cloud Shell with subsampling)
- [ ] Refine topic labels with distinctiveness scoring
- [ ] Create 50k interactive visualization
- [ ] Deploy to GCS with public URL
- [ ] Delete VM to stop charges
- [ ] Update this documentation with final metrics

## Questions Resolved

**Q: Why not cluster full 1.5M dataset?**  
A: 50k stratified sample provides comprehensive coverage at 3% of computational cost. Can scale later if needed.

**Q: Why not use IC as a clustering feature?**  
A: ICs are administrative, not scientific. We want to cluster by type of research, not by organizational structure.

**Q: How to handle domain label quality?**  
A: Used manual curation based on RCDC frequency analysis. Auto-labeling was too generic (e.g., 4 domains labeled "Genetics & Neurosciences").

**Q: Why 10 domains specifically?**  
A: Balance between:
- Too few (< 8): Overly broad, loses scientific distinction
- Too many (> 15): Fragmented, hard to navigate
- 10 provides intuitive top-level organization

## Contact & Repository
- **GitHub:** github.com/conroyriodss/nih-topic-maps
- **GCS Bucket:** od-cl-odss-conroyri-nih-embeddings
- **BigQuery Dataset:** od-cl-odss-conroyri-f75a.nih_exporter
