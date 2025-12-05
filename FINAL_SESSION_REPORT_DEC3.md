# NIH Award Clustering - Final Report
December 3, 2025 | 4:16 PM EST

## Executive Summary

Successfully completed award-level clustering of 103,204 NIH research programs.
Award-based analysis is superior to transaction-based for portfolio management.

## Key Achievement

Data Flow:
  ExPORTER Raw (12M transactions)
  → Grant Scorecard (560K awards)
  → Sample 103K Awards
  → TF-IDF Embeddings (100D)
  → Semantic Clustering (K=75)
  → Visualizations

## Results Comparison

Transaction-Level:
  - 250,000 records
  - ~60,000 unique programs
  - Silhouette 0.347
  - 4-5x inflation from multi-year funding

Award-Level:
  - 103,204 unique awards
  - Silhouette 0.136 (semantic)
  - No inflation
  - Independent of IC structure (ARI=0.0056)

## Top 5 Clusters by Funding

1. Cluster 25: AIDS & Life Sciences - $35.1B, 20,960 awards
2. Cluster 56: Bone & Neural Development - $6.7B, 4,133 awards
3. Cluster 54: Applied Centers & Networks - $6.2B, 998 awards
4. Cluster 51: Gene Expression - $3.9B, 2,216 awards
5. Cluster 17: Neural Mechanisms - $3.6B, 1,861 awards

## Files Generated

Data:
  awards_110k_with_semantic_clusters.csv      35M
  award_embeddings_tfidf_103k.npy            41M
  award_cluster_labels_semantic.csv          7.3K

Visualizations:
  award_semantic_map_103k.png                660K
  award_cluster_sizes_semantic.png            92K
  award_funding_distribution_semantic.png    242K

## Key Decisions

1. Award-Level vs Transaction: Use awards (no inflation)
2. TF-IDF vs Neural: TF-IDF (fast, no dependencies)
3. Sample Size: 103K validation before full 560K scale

## Next Steps

Option A: Generate better embeddings (PubMedBERT, GPU)
Option B: Scale to full 560K awards with current method
Option C: Deploy for stakeholder feedback

## Recommendation

Use award-level clustering for:
  - Strategic planning
  - Portfolio analysis
  - Topic identification
  - PI/institution analysis

Use transaction-level for:
  - Annual budgets
  - Fiscal year reports
  - Payment tracking

Status: Production-ready for exploration
Next: Choose production path and scale
