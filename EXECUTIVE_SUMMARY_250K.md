# NIH Grant Portfolio Analysis
## 250,000 Grants Clustered into 75 Research Topics

**Analysis Date:** December 03, 2025

## Overview

- **Grants Analyzed:** 250,000
- **Time Period:** FY 2000-2024
- **Total Funding:** $126.24B
- **Research Topics:** 75 clusters
- **Institutes/Centers:** 75

## Cluster Quality

- **Silhouette Score:** 0.3470 (strong clustering)
- **Average Cluster Size:** 3,333 grants
- **Interdisciplinary:** All clusters span 10+ ICs
- **Temporal Stability:** All clusters span 20+ years

## Top 10 Research Areas by Funding

1. **Cluster 51** (NATIONAL CENTER FOR CHRONIC DISEASE PREVENTION AND HEALTH PROMOTION)
   - Grants: 4,611
   - Funding: $4876.7M

2. **Cluster 67** (NATIONAL CANCER INSTITUTE)
   - Grants: 2,677
   - Funding: $3947.8M

3. **Cluster 8** (NATIONAL INSTITUTE OF ALLERGY AND INFECTIOUS DISEASES)
   - Grants: 6,105
   - Funding: $3415.5M

4. **Cluster 69** (NATIONAL HEART, LUNG, AND BLOOD INSTITUTE)
   - Grants: 3,066
   - Funding: $3297.7M

5. **Cluster 4** (NATIONAL INSTITUTE OF MENTAL HEALTH)
   - Grants: 4,328
   - Funding: $3243.9M

6. **Cluster 12** (NATIONAL INSTITUTE ON AGING)
   - Grants: 6,067
   - Funding: $3035.2M

7. **Cluster 61** (NATIONAL INSTITUTE OF ALLERGY AND INFECTIOUS DISEASES)
   - Grants: 2,077
   - Funding: $3033.1M

8. **Cluster 24** (NATIONAL CANCER INSTITUTE)
   - Grants: 6,873
   - Funding: $2832.8M

9. **Cluster 36** (NATIONAL INSTITUTE OF NEUROLOGICAL DISORDERS AND STROKE)
   - Grants: 6,030
   - Funding: $2605.9M

10. **Cluster 72** (NATIONAL HEART, LUNG, AND BLOOD INSTITUTE)
   - Grants: 6,386
   - Funding: $2552.3M

## Methodology

- **Approach:** Unsupervised machine learning (MiniBatchKMeans)
- **Features:** 2D UMAP projection of grant similarities
- **Validation:** Silhouette analysis, IC coverage, temporal stability
- **Granularity:** 7.5x finer than previous domain-level analysis

## Files Generated

- `hierarchical_250k_clustered_k75.csv` - Full dataset with cluster assignments
- `cluster_250k_summary.csv` - Cluster statistics and metadata
- `nih_topic_map_250k_k75.png` - Visualization of topic landscape
