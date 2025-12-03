#!/usr/bin/env python3
"""
Compare award-level vs transaction-level clustering
"""
import pandas as pd

print("="*70)
print("CLUSTERING APPROACH COMPARISON")
print("="*70)

# Load both datasets
print("\nLoading datasets...")
awards = pd.read_csv('awards_110k_clustered_k75.csv')
transactions = pd.read_csv('hierarchical_250k_clustered_k75.csv')

print("\n" + "="*70)
print("1. DATASET COMPARISON")
print("="*70)

print("\nAward-Level Clustering:")
print(f"  Records: {len(awards):,} unique research programs")
print(f"  Time span: {awards['first_fiscal_year'].min():.0f}-{awards['last_fiscal_year'].max():.0f}")
print(f"  Total funding: ${awards['total_lifetime_funding'].sum()/1e9:.1f}B")
print(f"  Silhouette score: 0.4573")
print(f"  Avg duration: {awards['distinct_fiscal_years'].mean():.1f} years")

print("\nTransaction-Level Clustering:")
print(f"  Records: {len(transactions):,} APPLICATION_IDs")
print(f"  Time span: {transactions['FY'].min():.0f}-{transactions['FY'].max():.0f}")
print(f"  Total funding: ${transactions['TOTAL_COST'].sum()/1e9:.1f}B")
print(f"  Silhouette score: 0.3470")
print(f"  Note: Same awards counted multiple times")

print("\n" + "="*70)
print("2. CLUSTER SIZE COMPARISON")
print("="*70)

award_sizes = awards['cluster_k75'].value_counts()
transaction_sizes = transactions['cluster_k75'].value_counts()

print("\nAward-level clusters:")
print(f"  Min: {award_sizes.min():,} | Median: {award_sizes.median():.0f} | Max: {award_sizes.max():,}")

print("\nTransaction-level clusters:")
print(f"  Min: {transaction_sizes.min():,} | Median: {transaction_sizes.median():.0f} | Max: {transaction_sizes.max():,}")

print("\n" + "="*70)
print("3. KEY INSIGHTS")
print("="*70)

print("\n✅ AWARD-LEVEL ADVANTAGES:")
print("  • Each cluster = unique research programs (no duplication)")
print("  • Higher quality (Silhouette: 0.457 vs 0.347)")
print("  • True portfolio representation")
print("  • Enables PI/institution analysis")
print("  • Tracks funding across award lifecycle")

print("\n⚠️  TRANSACTION-LEVEL LIMITATIONS:")
print("  • Same award counted multiple times")
print("  • Inflated by multi-year funding")
print("  • Lower clustering quality")
print("  • Confuses temporal analysis")

print("\n" + "="*70)
print("4. RECOMMENDATION")
print("="*70)

print("\n🎯 USE AWARD-LEVEL CLUSTERING for:")
print("  • Portfolio analysis and planning")
print("  • Topic/domain identification")
print("  • IC strategic reviews")
print("  • PI and institution analysis")
print("  • Funding trend analysis")

print("\n📊 USE TRANSACTION-LEVEL data for:")
print("  • Annual budget analysis")
print("  • Fiscal year spending reports")
print("  • Payment/obligation tracking")
print("  • Administrative reporting")

print("\n" + "="*70)
print("5. NEXT STEPS FOR AWARD-LEVEL CLUSTERING")
print("="*70)

print("\n📈 IMMEDIATE IMPROVEMENTS:")
print("  1. Generate text embeddings from project_title")
print("  2. Create semantic clusters (like transaction version)")
print("  3. Label clusters with TF-IDF keywords")
print("  4. Generate visualizations")

print("\n🚀 SCALE-UP PATH:")
print("  1. Expand to all ~560K awards in scorecard")
print("  2. Generate 768D PubMedBERT embeddings")
print("  3. Create production-grade clustering")
print("  4. Build interactive dashboard")

print("\n" + "="*70)
