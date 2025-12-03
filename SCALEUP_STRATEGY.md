# Scale-Up Strategy: 250K to 2.6M ExPORTER Dataset

## Three Approaches

### Option A: Incremental Expansion (Safest)
- 250K → 500K → 1M → 2.6M
- Time: 8-12 hours total
- Cost: ~$20 GCP
- Risk: Low
- Quality: Same as current (2D UMAP)

### Option B: Production 768D Embeddings (RECOMMENDED)
- Generate proper 768D PubMedBERT embeddings first
- Then cluster on full embedding space
- Time: 24-48 hours (mostly unattended)
- Cost: ~$80 GCP
- Risk: Medium
- Quality: Publication-grade

### Option C: Direct Scale-Up (Fastest)
- Scale existing 2D UMAP approach to 2.6M
- Time: 4-8 hours
- Cost: ~$15 GCP
- Risk: Medium
- Quality: Same as current (2D UMAP)

## My Recommendation: Option B

Why: NIH analysis should use best-in-class methods
- 768D embeddings are standard in literature
- One-time investment enables future analyses
- Results defensible to reviewers
- Worth the upfront cost for long-term value

## Implementation Plan (Option B)

1. Set up GPU VM (T4 or better)
2. Generate 768D embeddings using PubMedBERT (24-48h)
3. Cluster on full 768D space (2-4h)
4. Generate UMAP for visualization only (2-4h)
5. Total: 2-3 days elapsed, ~$80 compute

## Next Steps

Decision needed on:
- Timeline requirements
- Budget constraints
- Publication standards
- Future analysis needs
