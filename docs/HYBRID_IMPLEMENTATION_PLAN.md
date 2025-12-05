# Hybrid Clustering Implementation Plan

## Available Data

1. PROJECT_TERMS (all years)
   - Granular text-mined keywords
   - Example: "dopamine;serotonin;gene expression;neurons"
   - ~10-50 terms per grant

2. NIH_SPENDING_CATS (FY2008+)
   - RCDC congressional categories
   - Example: "Aging;Biomedical Imaging;Osteoporosis"
   - ~3-5 categories per grant

3. IC_NAME
   - Administering Institute/Center
   - 27 institutes

4. ACTIVITY
   - Grant mechanism (R01, P01, K08, etc.)
   - ~100 activity codes

## Recommended Hybrid Approach

Weight combination:
- 60% PubMedBERT semantic embeddings
- 25% NIH_SPENDING_CATS (RCDC)
- 10% PROJECT_TERMS (top keywords)
- 5% IC_NAME

## Expected Improvements

Current K=74 issues:
- Generic labels ("health care based")
- 10+ topics with 32+ ICs
- Outlier clusters

After hybrid:
- Labels from RCDC categories ("Cancer Research", "Neuroscience")
- Better IC coherence within topics
- Fewer outlier clusters

## Implementation Steps

1. Extract RCDC categories from 50K sample
2. One-hot encode or TF-IDF vectorize
3. Concatenate with scaled PubMedBERT embeddings
4. Cluster with K=150
5. Generate labels from top RCDC terms per cluster
