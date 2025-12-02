# Context for Next Session

## Current State
- **Previous work:** 43,320 grants clustered (FY 2000-2024) with 5 domains × 13 topics × 24 subtopics
- **New focus:** 100k stratified sample for clustering parameter optimization

## Active Task: 100k Clustering Optimization

### Objective
Build a 100k stratified sample to systematically explore and optimize:
1. **Hierarchical clustering parameters** (linkage methods, distance thresholds)
2. **UMAP visualization parameters** (n_neighbors, min_dist, metric)

### Why 100k Sample?
- Enables rapid iteration (minutes vs hours)
- Large enough to represent population diversity
- Balanced across fiscal years (1990-2024), ICs, and research domains
- Computationally tractable for parameter sweeps

## New Scripts Created (Dec 2, 2025)

### 1. `scripts/create_100k_stratified_sample.py`
**Purpose:** Generate representative 100k sample from BigQuery
- Stratified by fiscal year and IC
- Validates RCDC coverage and data quality
- Outputs: `grants_100k_stratified.parquet`, `grants_100k_metadata.json`

### 2. `scripts/hierarchical_param_sweep.py`
**Purpose:** Systematic exploration of hierarchical clustering parameters
- **Tests:** Ward, complete, average, single linkage
- **Metrics:** Silhouette score, Calinski-Harabasz, Davies-Bouldin
- **Analyzes:** Cluster size distribution, tiny cluster percentage
- **Outputs:** 
  - `hierarchical_param_sweep_results.csv` (all combinations)
  - `hierarchical_param_sweep_results.png` (4-panel visualization)
  - `hierarchical_recommendations.json` (best configurations)

### 3. `scripts/umap_param_sweep.py`
**Purpose:** Optimize 2D visualization projection
- **Tests:** n_neighbors [5, 15, 30, 50, 100, 200] × min_dist [0.0, 0.1, 0.25, 0.5, 0.8] × metric [euclidean, cosine]
- **Metrics:** Silhouette in 2D space, trustworthiness, cluster cohesion
- **Outputs:**
  - `umap_param_sweep_results.csv`
  - `umap_param_sweep_results.png` (parameter effects)
  - `umap_embedding_comparison.png` (visual comparison)
  - `umap_recommendations.json` (best configurations)

### 4. `scripts/run_100k_optimization_workflow.sh`
**Purpose:** End-to-end orchestration
- Runs all steps sequentially with checkpoints
- Interactive prompts for skipping existing outputs

## Recommended Workflow

```bash
cd ~/nih-topic-maps

# Option A: Full automated workflow
chmod +x scripts/run_100k_optimization_workflow.sh
./scripts/run_100k_optimization_workflow.sh

# Option B: Step-by-step manual execution

# Step 1: Create stratified sample
python3 scripts/create_100k_stratified_sample.py
# ⏱️  ~5-10 minutes
# ✅ Outputs: grants_100k_stratified.parquet (balanced across FY/IC)

# Step 2: Generate embeddings for 100k sample
# (Adapt existing script 05 or use your embedding pipeline)
python3 scripts/05_generate_embeddings_pubmedbert.py \
    --input grants_100k_stratified.parquet \
    --output embeddings_100k_pubmedbert.parquet
# ⏱️  ~30-60 minutes (GPU recommended)

# Step 3: Hierarchical clustering parameter sweep
python3 scripts/hierarchical_param_sweep.py
# ⏱️  ~15-30 minutes
# ✅ Tests: 4 linkage methods × multiple K values
# ✅ Identifies: Best method for your data characteristics

# Step 4: UMAP parameter sweep
python3 scripts/umap_param_sweep.py
# ⏱️  ~30-60 minutes
# ✅ Tests: 60 parameter combinations
# ✅ Identifies: Optimal visualization parameters
```

## Expected Outputs

### Hierarchical Clustering Insights
- **Best linkage method** (likely Ward or complete for biomedical data)
- **Optimal K** balancing granularity vs interpretability
- **Cluster quality metrics** for evidence-based decisions
- **Size distribution analysis** (tiny clusters, outliers)

### UMAP Visualization Insights
- **n_neighbors** effect on global vs local structure
- **min_dist** effect on cluster tightness
- **metric** comparison (euclidean vs cosine for PubMedBERT)
- **Trustworthiness scores** for projection fidelity

## Decision Points

### After Parameter Sweeps

**Review results:**
```bash
cat hierarchical_recommendations.json
cat umap_recommendations.json
```

**Key questions:**
1. Does Ward linkage outperform other methods?
2. What K value provides best silhouette score without excessive tiny clusters?
3. Which UMAP parameters balance cluster separation and local structure?
4. Do results differ between euclidean and cosine metrics?

### Scaling to Full Dataset

Once optimal parameters identified:

```bash
# Apply best configuration to full 2.09M dataset
python3 scripts/apply_best_clustering_full.py \
    --linkage ward \
    --n_clusters 150 \
    --umap_neighbors 50 \
    --umap_min_dist 0.1
```

## Alternative Approaches to Consider

### Hybrid Clustering (Already Implemented)
- Your `hybrid_clustering.py` combines PubMedBERT embeddings + RCDC categories + IC
- **Weights:** 70% embedding, 20% RCDC, 10% IC
- **Can optimize:** Test different weight combinations on 100k sample

### Multi-Resolution Clustering
- Hierarchical structure with 2-3 levels
- Domains (K=10-15) → Topics (K=100-150) → Subtopics (K=500-1000)
- Better aligns with NIH organizational structure

### Temporal Clustering
- Cluster within fiscal year blocks
- Track topic evolution over time
- Identify emerging vs declining research areas

## Integration with Current Work

### Your Existing 43k Visualization
- Compare 43k (FY 2000-2024) vs 100k (FY 1990-2024) cluster quality
- Historical grants may reveal different topic structure
- Spider web layout will benefit from denser temporal coverage

### Phase 2: Topic Network View
- After optimal clustering established
- Create edges between related topics
- Weight by grant overlap, PI collaboration, or citation patterns

## Troubleshooting

### If embeddings generation fails
```bash
# Check GPU availability
nvidia-smi

# Fallback to CPU (slower)
export CUDA_VISIBLE_DEVICES=""
python3 scripts/05_generate_embeddings_pubmedbert.py ...
```

### If BigQuery quota exceeded
```bash
# Monitor query costs
bq ls --max_results=100

# Use cached tables instead
bq query --use_cache ...
```

### If parameter sweep too slow
```bash
# Reduce parameter grid in scripts
# Edit hierarchical_param_sweep.py:
N_CLUSTERS_WARD = [75, 100, 150]  # Fewer values

# Or subsample further for initial exploration
python3 scripts/create_50k_sample.py  # Faster prototyping
```

## References

### Key Metrics Explained

**Silhouette Score [-1, 1]:**
- Measures how similar points are to their cluster vs other clusters
- >0.5: Strong structure
- 0.25-0.5: Reasonable structure
- <0.25: Weak structure

**Calinski-Harabasz (higher is better):**
- Ratio of between-cluster to within-cluster variance
- No absolute threshold; compare relative values

**Davies-Bouldin (lower is better):**
- Average similarity between each cluster and its most similar cluster
- <1.0: Good separation

**Trustworthiness [0, 1]:**
- How well 2D projection preserves local neighborhoods
- >0.9: Excellent preservation
- 0.8-0.9: Good preservation

### Linkage Methods

**Ward:** Minimizes within-cluster variance (requires euclidean distance)
- Best for: Balanced, spherical clusters
- NIH use case: ✅ Excellent for biomedical embeddings

**Complete:** Minimizes maximum distance between cluster members
- Best for: Compact, well-separated clusters
- NIH use case: ✅ Good for distinct research areas

**Average:** Uses mean distance between all pairs
- Best for: Elongated or irregular clusters
- NIH use case: ⚠️  May merge related but distinct topics

**Single:** Minimizes minimum distance between cluster members
- Best for: Chaining, hierarchical structures
- NIH use case: ❌ Often creates unbalanced clusters

## Next Session Commands

```bash
# Navigate to project
cd ~/nih-topic-maps

# Check status of outputs
ls -lh grants_100k* embeddings_100k* hierarchical_* umap_*

# Run workflow if not started
./scripts/run_100k_optimization_workflow.sh

# OR continue from checkpoint:
# If sample created but no embeddings:
python3 scripts/05_generate_embeddings_pubmedbert.py \
    --input grants_100k_stratified.parquet \
    --output embeddings_100k_pubmedbert.parquet

# If embeddings ready:
python3 scripts/hierarchical_param_sweep.py

# Review results:
cat hierarchical_recommendations.json | jq .
open hierarchical_param_sweep_results.png
```

## Questions for Next Session

1. **Embedding source:** Use existing PubMedBERT embeddings or regenerate for 100k?
2. **Hybrid vs pure:** Test both pure embedding clustering and hybrid (embedding+RCDC+IC)?
3. **Evaluation criteria:** Prioritize silhouette score, Calinski-Harabasz, or domain expert validation?
4. **Visualization goals:** Static publication figure vs interactive exploration tool?
5. **Production timeline:** When do you need full 2.09M results?

---

**Last updated:** December 2, 2025  
**Status:** Ready to run 100k optimization workflow  
**Estimated total time:** 1-2 hours (mostly unattended computation)
