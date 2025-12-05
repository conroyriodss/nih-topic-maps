#!/usr/bin/env python3
"""
Comprehensive cluster quality analysis for 250k
"""
import pandas as pd
import numpy as np

print("="*70)
print("250K CLUSTER ANALYSIS REPORT")
print("="*70)

df = pd.read_csv('hierarchical_250k_clustered_k75.csv')

# Overall statistics
print(f"\n📊 DATASET OVERVIEW")
print(f"   Total grants: {len(df):,}")
print(f"   Fiscal years: {df['FY'].min():.0f}-{df['FY'].max():.0f}")
print(f"   ICs: {df['IC_NAME'].nunique()}")
print(f"   Clusters: {df['cluster_k75'].nunique()}")
print(f"   Total funding: ${df['TOTAL_COST'].sum()/1e9:.2f}B")

# Cluster size distribution
cluster_sizes = df['cluster_k75'].value_counts().sort_index()
print(f"\n📈 CLUSTER SIZE DISTRIBUTION")
print(f"   Min: {cluster_sizes.min():,} grants")
print(f"   25th percentile: {cluster_sizes.quantile(0.25):,.0f}")
print(f"   Median: {cluster_sizes.median():,.0f}")
print(f"   75th percentile: {cluster_sizes.quantile(0.75):,.0f}")
print(f"   Max: {cluster_sizes.max():,} grants")
print(f"   Std dev: {cluster_sizes.std():.0f}")

# Quality checks
print(f"\n✅ QUALITY CHECKS")
tiny = (cluster_sizes < 500).sum()
small = ((cluster_sizes >= 500) & (cluster_sizes < 2000)).sum()
medium = ((cluster_sizes >= 2000) & (cluster_sizes < 4000)).sum()
large = (cluster_sizes >= 4000).sum()

print(f"   Tiny (<500): {tiny} clusters")
print(f"   Small (500-2k): {small} clusters")
print(f"   Medium (2k-4k): {medium} clusters")
print(f"   Large (4k+): {large} clusters")

# IC coverage
print(f"\n🏛️  IC COVERAGE")
ic_coverage = df.groupby('cluster_k75')['IC_NAME'].nunique()
print(f"   Clusters with 1 IC: {(ic_coverage == 1).sum()}")
print(f"   Clusters with 2-5 ICs: {((ic_coverage >= 2) & (ic_coverage <= 5)).sum()}")
print(f"   Clusters with 6-10 ICs: {((ic_coverage >= 6) & (ic_coverage <= 10)).sum()}")
print(f"   Clusters with 10+ ICs: {(ic_coverage > 10).sum()}")

# Temporal distribution
print(f"\n📅 TEMPORAL DISTRIBUTION")
fy_per_cluster = df.groupby('cluster_k75')['FY'].agg(['min', 'max', 'count'])
fy_span = fy_per_cluster['max'] - fy_per_cluster['min']
print(f"   Clusters spanning <10 years: {(fy_span < 10).sum()}")
print(f"   Clusters spanning 10-20 years: {((fy_span >= 10) & (fy_span < 20)).sum()}")
print(f"   Clusters spanning 20+ years: {(fy_span >= 20).sum()}")

# Top 10 largest clusters
print(f"\n🔝 TOP 10 LARGEST CLUSTERS")
top10 = df.groupby('cluster_k75').agg({
    'APPLICATION_ID': 'count',
    'IC_NAME': lambda x: x.mode()[0] if len(x) > 0 else 'Unknown',
    'PROJECT_TITLE': lambda x: x.iloc[0][:60] if len(x) > 0 else ''
}).nlargest(10, 'APPLICATION_ID')

for idx, (cluster, row) in enumerate(top10.iterrows(), 1):
    print(f"   {idx:2d}. Cluster {cluster:2d}: {row['APPLICATION_ID']:,} grants")
    print(f"       Lead IC: {row['IC_NAME']}")
    print(f"       Sample: {row['PROJECT_TITLE']}...")

# Save detailed stats
cluster_details = df.groupby('cluster_k75').agg({
    'APPLICATION_ID': 'count',
    'TOTAL_COST': ['sum', 'mean'],
    'FY': ['min', 'max'],
    'IC_NAME': lambda x: x.mode()[0] if len(x) > 0 else 'Unknown',
}).round(0)
cluster_details.columns = ['n_grants', 'total_funding', 'avg_funding', 'fy_min', 'fy_max', 'lead_ic']
cluster_details.to_csv('cluster_250k_summary.csv')

print(f"\n💾 SAVED: cluster_250k_summary.csv")
print(f"   Detailed statistics for all 75 clusters")

print("\n" + "="*70)
print("ANALYSIS COMPLETE")
print("="*70)
