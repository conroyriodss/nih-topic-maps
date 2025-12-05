# NIH Topic Maps: Clustering Optimization Guide

## Overview

This guide walks through the systematic optimization of hierarchical clustering and UMAP visualization parameters using a 100k stratified sample.

## Quick Start

```bash
cd ~/nih-topic-maps
chmod +x scripts/run_100k_optimization_workflow.sh
./scripts/run_100k_optimization_workflow.sh
```

**Total estimated time:** 1-2 hours (mostly unattended)

---

## Detailed Workflow

### Step 1: Create Stratified Sample (5-10 minutes)

```bash
python3 scripts/create_100k_stratified_sample.py
```

**What it does:**
- Queries BigQuery for all grants (FY 1990-2024)
- Stratifies by fiscal year and IC proportionally
- Validates data quality (RCDC coverage, abstract availability)
- Outputs balanced 100k sample

**Outputs:**
- `grants_100k_stratified.parquet` (100,000 grants)
- `grants_100k_metadata.json` (statistics)

**Expected distribution:**
- ~35 fiscal years × 27 ICs = 900+ strata
- 50-200 grants per stratum (varies by IC size)
- Representative of full 2.09M population

---

### Step 2: Generate Embeddings (30-60 minutes)

```bash
# Option A: Modify existing script to use 100k sample
python3 scripts/05_generate_embeddings_pubmedbert.py \
    --input grants_100k_stratified.parquet \
    --output embeddings_100k_pubmedbert.parquet

# Option B: Use your existing embedding pipeline
# Ensure output matches expected format:
# - APPLICATION_ID column
# - embedding column (array of 768 floats)
# - Other metadata columns (FY, IC_NAME, etc.)
```

**What it does:**
- Loads PubMedBERT model
- Generates 768-dimensional embeddings from PROJECT_TITLE + ABSTRACT_TEXT
- Saves to Parquet with metadata

**Outputs:**
- `embeddings_100k_pubmedbert.parquet`

**Hardware recommendations:**
- GPU: ~30 minutes (NVIDIA A100/V100)
- CPU: ~2-3 hours (fallback)

---

### Step 3: Hierarchical Clustering Parameter Sweep (15-30 minutes)

```bash
python3 scripts/hierarchical_param_sweep.py
```

**What it does:**
- Tests 4 linkage methods: Ward, Complete, Average, Single
- For Ward: Tests K = [50, 75, 100, 125, 150, 200]
- For others: Tests distance thresholds = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
- Computes quality metrics: Silhouette, Calinski-Harabasz, Davies-Bouldin
- Analyzes cluster size distribution and tiny clusters

**Outputs:**
- `hierarchical_param_sweep_results.csv` (all combinations with metrics)
- `hierarchical_param_sweep_results.png` (4-panel visualization)
- `hierarchical_recommendations.json` (best configurations)

**Metrics explained:**

| Metric | Range | Interpretation | Goal |
|--------|-------|----------------|------|
| **Silhouette Score** | [-1, 1] | Cluster separation vs cohesion | Maximize (>0.25 good) |
| **Calinski-Harabasz** | [0, ∞) | Between/within cluster variance ratio | Maximize |
| **Davies-Bouldin** | [0, ∞) | Avg similarity to most similar cluster | Minimize (<1.0 good) |

**Expected results:**
- Ward linkage typically performs best for biomedical embeddings
- Optimal K usually 100-150 for NIH portfolio
- Silhouette scores 0.25-0.40 typical for complex domains

---

### Step 4: Apply Best Clustering (5 minutes)

```bash
python3 scripts/apply_hierarchical_clustering.py
```

**What it does:**
- Reads best config from `hierarchical_recommendations.json`
- Applies clustering to full 100k embeddings
- Generates topic labels from RCDC categories
- Computes cluster statistics (size, funding, IC distribution)

**Outputs:**
- `hierarchical_best_clustering.csv` (cluster assignments)
- `hierarchical_topic_labels.json` (human-readable labels)
- `hierarchical_topic_stats.json` (per-cluster statistics)
- `hierarchical_clustering_metadata.json` (configuration)

---

### Step 5: UMAP Parameter Sweep (30-60 minutes)

```bash
python3 scripts/umap_param_sweep.py
```

**What it does:**
- Tests n_neighbors: [5, 15, 30, 50, 100, 200]
- Tests min_dist: [0.0, 0.1, 0.25, 0.5, 0.8]
- Tests metrics: [euclidean, cosine]
- Total: 60 parameter combinations
- Evaluates: Silhouette in 2D, trustworthiness, cluster cohesion

**Outputs:**
- `umap_param_sweep_results.csv` (all combinations)
- `umap_param_sweep_results.png` (parameter effect plots)
- `umap_embedding_comparison.png` (visual comparison)
- `umap_recommendations.json` (best configurations)

**Parameters explained:**

| Parameter | Effect | Typical Range | Recommendation |
|-----------|--------|---------------|----------------|
| **n_neighbors** | Controls global vs local structure | 5-200 | 30-50 for balanced view |
| **min_dist** | Controls cluster tightness | 0.0-1.0 | 0.1-0.3 for biomedical data |
| **metric** | Distance calculation | euclidean/cosine | Cosine for normalized embeddings |

**Trade-offs:**
- Small n_neighbors: Emphasizes local structure, may fragment topics
- Large n_neighbors: Emphasizes global structure, may merge topics
- Small min_dist: Tight clusters, clear separation
- Large min_dist: Loose clusters, emphasizes topology

**Expected results:**
- n_neighbors=50, min_dist=0.1-0.25 often optimal
- Cosine metric may outperform euclidean for PubMedBERT
- Trustworthiness >0.85 indicates good 2D projection

---

## Interpreting Results

### Review Hierarchical Clustering

```bash
# View recommendations
cat hierarchical_recommendations.json | jq .

# Open visualization
open hierarchical_param_sweep_results.png  # macOS
xdg-open hierarchical_param_sweep_results.png  # Linux
```

**Key questions:**

1. **Which linkage method wins?**
   - Ward typically best for balanced clusters
   - Complete good if you want compact, well-separated topics
   - Average/Single rarely optimal for NIH data

2. **What's the optimal K?**
   - Look for "elbow" in silhouette score plot
   - Balance granularity vs interpretability
   - NIH standard: 100-150 topics aligns with RCDCs

3. **Are cluster sizes balanced?**
   - Check "tiny clusters" percentage
   - <10% tiny clusters (<50 grants) is healthy
   - >20% suggests over-clustering

4. **How do metrics agree?**
   - Best configs should rank high on multiple metrics
   - Disagreement may indicate instability

### Review UMAP Results

```bash
# View recommendations
cat umap_recommendations.json | jq .

# Open visualizations
open umap_param_sweep_results.png
open umap_embedding_comparison.png
```

**Key questions:**

1. **What n_neighbors value?**
   - Look at silhouette vs trustworthiness trade-off
   - 30-50 usually optimal for 100k samples
   - Higher for smoother global structure
   - Lower for detailed local neighborhoods

2. **What min_dist value?**
   - Check cluster cohesion plots
   - 0.0-0.1: Very tight, clear boundaries
   - 0.25-0.5: Moderate, natural spread
   - >0.5: Loose, emphasizes continuum

3. **Euclidean or cosine?**
   - Compare heatmaps side-by-side
   - Cosine often better for normalized embeddings
   - Euclidean preserves absolute magnitudes

4. **Visual inspection:**
   - Do clusters look well-separated?
   - Are related topics positioned nearby?
   - Is there excessive overlap or fragmentation?

---

## Common Issues & Solutions

### Issue: Low Silhouette Scores (<0.15)

**Causes:**
- Insufficient embedding quality
- Data truly has weak cluster structure
- Wrong number of clusters

**Solutions:**
```bash
# Try different K values
# Edit hierarchical_param_sweep.py:
N_CLUSTERS_WARD = [30, 50, 75, 100, 150, 200, 300]

# Test hybrid clustering (embedding + RCDC + IC)
python3 scripts/hybrid_clustering.py
```

### Issue: Too Many Tiny Clusters

**Causes:**
- Over-clustering
- Outliers forming singleton clusters
- Single linkage creating chains

**Solutions:**
- Reduce K (try K=75 or K=50)
- Use Ward or Complete linkage (not Single)
- Post-process: merge clusters <50 grants with nearest neighbor

### Issue: UMAP Parameter Sweep Too Slow

**Causes:**
- 60 combinations × 100k samples = computationally intensive

**Solutions:**
```bash
# Reduce parameter grid
# Edit umap_param_sweep.py:
N_NEIGHBORS = [15, 50, 100]  # Focus on key values
MIN_DIST = [0.0, 0.25, 0.5]  # Reduce to 3 values
# Total: 3 × 3 × 2 = 18 combinations

# Or subsample for initial exploration
python3 scripts/create_50k_sample.py  # Create smaller sample
```

### Issue: Out of Memory

**Causes:**
- Distance matrix for 100k × 100k = 5GB+ RAM
- Multiple UMAP embeddings cached

**Solutions:**
```bash
# Reduce sample size
python3 scripts/create_50k_sample.py

# Use Ward linkage (no distance matrix needed)
# Ward operates directly on embeddings

# Clear Python cache
import gc
gc.collect()
```

---

## Scaling to Full Dataset

### Once Parameters Optimized

```bash
# Extract best parameters
LINKAGE=$(jq -r '.best_overall.linkage_method' hierarchical_recommendations.json)
K=$(jq -r '.best_overall.n_clusters_actual' hierarchical_recommendations.json)
N_NEIGHBORS=$(jq -r '.best_balanced.n_neighbors' umap_recommendations.json)
MIN_DIST=$(jq -r '.best_balanced.min_dist' umap_recommendations.json)

echo "Optimal config: $LINKAGE linkage, K=$K, UMAP n=$N_NEIGHBORS, d=$MIN_DIST"
```

### Apply to Full 2.09M Dataset

```bash
# 1. Generate embeddings for full dataset (if not already done)
# This is the bottleneck: ~24-48 hours on CPU, ~4-8 hours on GPU

# 2. Apply clustering with best parameters
python3 scripts/cluster_full_dataset.py \
    --linkage ward \
    --n_clusters 150 \
    --embeddings gs://od-cl-odss-conroyri-nih-embeddings/full/embeddings_2M.parquet

# 3. Generate UMAP projection
python3 scripts/umap_full_dataset.py \
    --n_neighbors 50 \
    --min_dist 0.1 \
    --metric cosine \
    --embeddings gs://od-cl-odss-conroyri-nih-embeddings/full/embeddings_2M.parquet \
    --clusters clusters_full_dataset.parquet

# 4. Generate production visualization
python3 scripts/generate_production_viz.py
```

**Computational requirements (full dataset):**
- Hierarchical clustering: 2-4 hours (RAM: 64GB+)
- UMAP: 6-12 hours (RAM: 128GB+)
- Alternative: Use Spark/Dask for distributed computation

---

## Advanced Optimizations

### Multi-Resolution Clustering

```python
# Level 1: Domains (K=10-15)
from scipy.cluster.hierarchy import linkage, fcluster
Z = linkage(embeddings, method='ward')
domains = fcluster(Z, 12, criterion='maxclust')

# Level 2: Topics within each domain (K=8-12 per domain)
for domain_id in range(1, 13):
    domain_mask = domains == domain_id
    domain_embeddings = embeddings[domain_mask]
    Z_domain = linkage(domain_embeddings, method='ward')
    topics = fcluster(Z_domain, 10, criterion='maxclust')
```

### Hybrid Weighting Optimization

```python
# Test different weight combinations
for w_emb in [0.5, 0.6, 0.7, 0.8, 0.9]:
    w_rcdc = (1 - w_emb) * 0.67  # 2/3 of remaining
    w_ic = (1 - w_emb) * 0.33    # 1/3 of remaining
    
    hybrid_features = np.hstack([
        w_emb * embeddings_scaled,
        w_rcdc * rcdc_scaled,
        w_ic * ic_scaled
    ])
    
    # Evaluate clustering quality
    labels = KMeans(n_clusters=100).fit_predict(hybrid_features)
    score = silhouette_score(hybrid_features, labels)
```

### Temporal Analysis

```python
# Cluster separately by era
eras = [(1990, 1999), (2000, 2009), (2010, 2019), (2020, 2024)]

for start_fy, end_fy in eras:
    mask = (df['FY'] >= start_fy) & (df['FY'] <= end_fy)
    era_embeddings = embeddings[mask]
    
    # Cluster this era
    labels = cluster_era(era_embeddings)
    
    # Track topic evolution across eras
```

---

## Validation & Quality Checks

### Cluster Quality Checklist

- [ ] Silhouette score >0.25
- [ ] <15% tiny clusters (<50 grants)
- [ ] Balanced cluster sizes (max/min ratio <20)
- [ ] Topic labels interpretable and distinct
- [ ] High-value topics align with known research areas
- [ ] IC distribution reasonable (not all grants from one IC)

### UMAP Quality Checklist

- [ ] Trustworthiness >0.85
- [ ] Clusters visually separated
- [ ] Related topics positioned nearby
- [ ] No extreme aspect ratios (x_range/y_range near 1)
- [ ] Funding hot-spots align with visual density

### Expert Validation

```bash
# Export sample for review
python3 scripts/export_validation_sample.py \
    --n_per_cluster 5 \
    --output validation_sample.xlsx

# Send to domain experts for review:
# - Are cluster labels accurate?
# - Are grants in correct topics?
# - Any surprising groupings?
```

---

## References

### Key Papers

1. **Hierarchical Clustering:**
   - Müllner, D. (2011). Modern hierarchical, agglomerative clustering algorithms. *arXiv:1109.2378*

2. **UMAP:**
   - McInnes, L., Healy, J., & Melville, J. (2018). UMAP: Uniform Manifold Approximation and Projection for Dimension Reduction. *arXiv:1802.03426*

3. **PubMedBERT:**
   - Gu, Y. et al. (2021). Domain-Specific Language Model Pretraining for Biomedical Natural Language Processing. *ACM TOIS*

4. **Clustering Validation:**
   - Rousseeuw, P. J. (1987). Silhouettes: A graphical aid to the interpretation and validation of cluster analysis. *J Comp App Math*

### NIH Resources

- **RCDC Categories:** https://report.nih.gov/funding/categorical-spending
- **RePORTER:** https://reporter.nih.gov/
- **NIH Organization:** https://www.nih.gov/institutes-nih

---

## Support

**Questions or issues?**

1. Check `CONTEXT_FOR_NEXT_SESSION.md` for latest status
2. Review `PROJECT_LOG.md` for historical context
3. Examine script comments for implementation details

**Contact:**
- Repository: github.com/conroyriodss/nih-topic-maps
- Documentation: README.md

---

**Last updated:** December 2, 2025  
**Version:** 1.0  
**Status:** Production-ready
