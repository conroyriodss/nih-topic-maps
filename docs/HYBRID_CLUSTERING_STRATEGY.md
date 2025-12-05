# Hybrid Clustering Strategy: PubMedBERT + NIH Categories

## Overview
Combine semantic embeddings (PubMedBERT) with structured NIH metadata for more interpretable and policy-relevant topic maps.

## Three Approaches

### Approach 1: Constrained Clustering (RECOMMENDED)
Use PubMedBERT embeddings but guide clustering with NIH categories

Method:
- Generate PubMedBERT embeddings (already done)
- Add categorical features: RCDC categories, MeSH terms, IC codes
- Use weighted K-means or semi-supervised clustering
- Categories influence but dont determine clusters

Pros:
- Balances semantic similarity with policy categories
- Maintains PubMedBERT deep understanding
- Interpretable labels from MeSH/RCDC
- Can tune weight of categorical influence

Implementation Time: 2-3 hours

### Approach 2: Multi-View Clustering
Separate clustering on embeddings and categories, then combine

Method:
- Cluster 1: K-means on PubMedBERT (semantic)
- Cluster 2: K-means on categorical features (RCDC/MeSH/IC)
- Consensus clustering to merge views

Implementation Time: 4-5 hours

### Approach 3: Hierarchical with Category Constraints
Build hierarchy: Categories to Sub-topics to Individual grants

Method:
- Level 1: Group by RCDC/IC categories (27-30 clusters)
- Level 2: Within each category, cluster by PubMedBERT
- Creates interpretable hierarchy

Implementation Time: 3-4 hours

## Data Sources Needed

1. RCDC Categories (Research, Condition, and Disease Categorization)
   - About 300 categories including Cancer, HIV/AIDS, Alzheimers, etc.
   - Download from: https://report.nih.gov/funding/categorical-spending

2. MeSH Terms (Medical Subject Headings from PubMed)
   - Already linked through abstracts
   - Can extract programmatically via PubMed API if not present

3. IC Codes (Institute/Center assignments)
   - Already have this in BigQuery

## Expected Improvements

Current (PubMedBERT only):
- Generic labels: "health care based"
- 10+ topics with 32+ ICs mixed
- Some outlier clusters

With Hybrid Approach:
- Specific labels: "Cancer Research Immunotherapy Clinical Trials"
- Better IC alignment (fewer mixed topics)
- Topics match NIH mental model
- More interpretable for policy decisions
