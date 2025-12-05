import pandas as pd
import numpy as np

df = pd.read_parquet('grants_50k_SEMANTIC_clustered.parquet')

print("=" * 70)
print("CLUSTER ANALYSIS")
print("=" * 70)

# Size distribution
sizes = df.groupby('cluster').size().sort_values(ascending=False)
print(f"\n📊 Cluster Size Distribution:")
print(f"  Total clusters: {len(sizes)}")
print(f"  Median size: {sizes.median():.0f}")
print(f"  Size range: {sizes.min()}-{sizes.max()}")

print(f"\nTop 10 largest clusters:")
for cid, size in sizes.head(10).items():
    print(f"  Cluster {cid}: {size:,} grants ({size/len(df)*100:.1f}%)")

# IC diversity
if 'IC_NAME' in df.columns:
    print(f"\n🏛️ IC Distribution (top 5 clusters):")
    for cid in sizes.head(5).index:
        cluster_df = df[df['cluster'] == cid]
        ic_dist = cluster_df['IC_NAME'].value_counts().head(3)
        print(f"\n  Cluster {cid} ({len(cluster_df):,} grants):")
        for ic, count in ic_dist.items():
            print(f"    {ic}: {count} ({count/len(cluster_df):.1%})")

# Temporal patterns
if 'FY' in df.columns:
    print(f"\n📅 Temporal Patterns (sample clusters):")
    for cid in sizes.head(3).index:
        cluster_df = df[df['cluster'] == cid]
        year_range = f"{cluster_df['FY'].min():.0f}-{cluster_df['FY'].max():.0f}"
        recent = (cluster_df['FY'] >= 2020).sum()
        print(f"  Cluster {cid}: Years {year_range}, Recent (2020+): {recent} ({recent/len(cluster_df):.1%})")

# Save summary
summary = pd.DataFrame({
    'cluster': sizes.index,
    'size': sizes.values,
    'pct_of_total': (sizes.values / len(df) * 100).round(1)
})
summary.to_csv('cluster_summary.csv', index=False)
print("\n✓ Saved cluster_summary.csv")
