#!/usr/bin/env python3
"""
Analyze why award clustering differs from transaction clustering
and suggest improvements
"""
import pandas as pd
import numpy as np

print("="*70)
print("CLUSTERING COMPARISON ANALYSIS")
print("="*70)

# Load both datasets
print("\n[1/3] Loading data...")
df_award = pd.read_csv('awards_110k_with_semantic_clusters.csv')
df_trans = pd.read_csv('hierarchical_250k_clustered_k75.csv')

print(f"Award-level: {len(df_award):,} records")
print(f"Transaction-level: {len(df_trans):,} records")

# Compare embedding approaches
print("\n[2/3] Comparing approaches...")

print("\nTRANSACTION-LEVEL (Original NIH Map):")
print("  • Used: PubMedBERT embeddings (768D)")
print("  • From: Abstract text")
print("  • Quality: Deep semantic understanding")
print("  • UMAP: n_neighbors=50, min_dist=0.0")
print("  • Result: Tight, well-separated clusters")

print("\nAWARD-LEVEL (Current):")
print("  • Used: TF-IDF + SVD (100D)")
print("  • From: Project titles only")
print("  • Quality: Keyword-based (17% variance)")
print("  • Projection: PCA (4.8% variance)")
print("  • Result: Diffuse, trajectory-like structure")

print("\n[3/3] Identified issues...")

print("\n❌ PROBLEM 1: Shallow Embeddings")
print("   TF-IDF captures keywords, not semantic relationships")
print("   Solution: Use sentence-transformers or PubMedBERT")

print("\n❌ PROBLEM 2: Limited Text")
print("   Project titles (~15 words) vs abstracts (~200 words)")
print("   Solution: Include abstracts or use richer text")

print("\n❌ PROBLEM 3: Poor 2D Projection")
print("   PCA (4.8% variance) loses cluster structure")
print("   Solution: Use UMAP with proper parameters")

print("\n❌ PROBLEM 4: Wrong Clustering Order")
print("   Clustered in high-D, then projected to 2D")
print("   Better: UMAP first (2D), then cluster in 2D space")

print("\n" + "="*70)
print("RECOMMENDATIONS")
print("="*70)

print("\n✅ OPTION 1: Match Transaction Methodology (BEST)")
print("   1. Use sentence-transformers embeddings (384D)")
print("   2. Apply UMAP: n_neighbors=50, min_dist=0.0")
print("   3. Cluster in 2D UMAP space")
print("   4. Generate labels with TF-IDF")
print("   Expected: Tight clusters like original map")

print("\n✅ OPTION 2: Improve Current Approach")
print("   1. Keep TF-IDF embeddings (100D)")
print("   2. Use UMAP instead of PCA")
print("   3. Better UMAP parameters")
print("   4. Re-cluster in 2D space")
print("   Expected: Better separation, still not perfect")

print("\n✅ OPTION 3: Use Existing Transaction Embeddings")
print("   1. Extract awards from transaction data")
print("   2. Aggregate embeddings by CORE_PROJECT_NUM")
print("   3. Use existing UMAP coordinates")
print("   4. Re-cluster at award level")
print("   Expected: Consistent with original map")

print("\n" + "="*70)
print("PARAMETER DIFFERENCES")
print("="*70)

print("\nOriginal Transaction Map UMAP:")
print("  n_neighbors: 50 (larger = more global structure)")
print("  min_dist: 0.0 (tighter clusters)")
print("  metric: cosine")

print("\nCurrent Award Map:")
print("  No UMAP used (PCA instead)")
print("  This explains the trajectory pattern!")

print("\n" + "="*70)
