#!/usr/bin/env python3
"""
Cluster 110K research awards (not transactions)
Same methodology as 250K transaction clustering
"""
import pandas as pd
import numpy as np
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt

print("="*70)
print("AWARD-LEVEL CLUSTERING: 110K Research Programs")
print("="*70)

# Load awards
print("\n[1/6] Loading award data...")
df = pd.read_csv('awards_110k_for_clustering.csv')
print(f"Loaded {len(df):,} awards")
print(f"ICs: {df['ic_name'].nunique()}")
print(f"Years: {df['first_fiscal_year'].min():.0f}-{df['last_fiscal_year'].max():.0f}")
print(f"Total funding: ${df['total_lifetime_funding'].sum()/1e9:.1f}B")

# Check for duplicates
print(f"\nChecking data quality:")
print(f"  Unique CORE_PROJECT_NUMs: {df['core_project_num'].nunique():,}")
print(f"  Total rows: {len(df):,}")
if df['core_project_num'].duplicated().any():
    print(f"  ⚠️  Duplicates found: {df['core_project_num'].duplicated().sum():,}")
    print("  Removing duplicates...")
    df = df.drop_duplicates(subset='core_project_num', keep='first')
    print(f"  After dedup: {len(df):,} awards")

# Prepare for clustering
print("\n[2/6] Preparing for clustering...")
print("NOTE: This dataset has award-level records, not transactions")
print(f"  • Each row = one complete research program (CORE_PROJECT_NUM)")
print(f"  • Average duration: {df['distinct_fiscal_years'].mean():.1f} years")
print(f"  • Multi-component awards: {df['subproject_count'].fillna(0).gt(0).sum():,}")

# Generate features from available data
print("\n[3/6] Generating features from award metadata...")

from sklearn.preprocessing import LabelEncoder

le_ic = LabelEncoder()
le_activity = LabelEncoder()

df['ic_encoded'] = le_ic.fit_transform(df['administering_ic'].fillna('UNKNOWN'))
df['activity_encoded'] = le_activity.fit_transform(df['activity'].fillna('UNKNOWN'))
df['funding_log'] = np.log10(df['total_lifetime_funding'].fillna(1).clip(lower=1))
df['duration'] = df['distinct_fiscal_years'].fillna(1)

# For now, use these features for initial clustering
features = df[['ic_encoded', 'activity_encoded', 'funding_log', 'duration']].values.astype(np.float32)

print(f"Feature matrix: {features.shape}")

# Cluster with K=75 (same as before)
print("\n[4/6] Clustering awards with MiniBatchKMeans (K=75)...")
kmeans = MiniBatchKMeans(
    n_clusters=75,
    batch_size=1000,
    random_state=42,
    n_init=10,
    verbose=1
)
df['cluster_k75'] = kmeans.fit_predict(features)

# Calculate silhouette score
print("\n[5/6] Evaluating cluster quality...")
sample_size = min(10000, len(df))
silhouette = silhouette_score(features, df['cluster_k75'], sample_size=sample_size)
print(f"Silhouette score: {silhouette:.4f}")

# Cluster statistics
cluster_sizes = df['cluster_k75'].value_counts()
print(f"\nCluster size distribution:")
print(f"  Min: {cluster_sizes.min():,} awards")
print(f"  Median: {cluster_sizes.median():.0f} awards")
print(f"  Max: {cluster_sizes.max():,} awards")

# Save clustered awards
print("\n[6/6] Saving clustered awards...")
df.to_csv('awards_110k_clustered_k75.csv', index=False)
print("✅ Saved: awards_110k_clustered_k75.csv")

# Quick cluster analysis
print("\n" + "="*70)
print("CLUSTER SUMMARY")
print("="*70)

cluster_summary = df.groupby('cluster_k75').agg({
    'core_project_num': 'count',
    'total_lifetime_funding': 'sum',
    'ic_name': lambda x: x.mode()[0] if len(x) > 0 else 'Unknown',
    'activity': lambda x: x.mode()[0] if len(x) > 0 else 'Unknown'
}).rename(columns={'core_project_num': 'n_awards'})

cluster_summary.to_csv('award_cluster_summary_k75.csv')

print("\nTop 10 clusters by award count:")
top10 = cluster_summary.nlargest(10, 'n_awards')
for idx, row in top10.iterrows():
    print(f"  C{idx:2d}: {row['n_awards']:>5,} awards | {row['ic_name'][:40]:40s} | {row['activity']}")

print("\nTop 10 clusters by funding:")
top10_funding = cluster_summary.nlargest(10, 'total_lifetime_funding')
for idx, row in top10_funding.iterrows():
    print(f"  C{idx:2d}: ${row['total_lifetime_funding']/1e9:>5.2f}B | {row['ic_name'][:40]:40s} | {row['n_awards']:,} awards")

print("\n✅ Award-level clustering complete!")
print("\nIMPORTANT NOTE:")
print("  This clustering used basic features (IC, activity, funding, duration)")
print("  For better results, we should use text embeddings from project_title")
print("  That will give semantic clustering like your transaction-level work")

print("\n" + "="*70)
