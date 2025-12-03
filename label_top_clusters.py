#!/usr/bin/env python3
import pandas as pd

df = pd.read_parquet('grants_50k_SEMANTIC_clustered.parquet')

top_clusters = [53, 0, 18, 56, 24]  # From executive summary

print("=" * 70)
print("TOP 5 CLUSTERS: SAMPLE TITLES FOR THEMATIC LABELING")
print("=" * 70)

for cid in top_clusters:
    cluster_df = df[df['cluster'] == cid]
    
    print(f"\n{'='*70}")
    print(f"CLUSTER {cid}")
    print(f"{'='*70}")
    print(f"Size: {len(cluster_df):,} grants")
    print(f"ICs: {cluster_df['IC_NAME'].nunique()} unique")
    print(f"Top IC: {cluster_df['IC_NAME'].value_counts().index[0]} ({cluster_df['IC_NAME'].value_counts().iloc[0]} grants)")
    print(f"\nSample Titles (random 10):")
    
    for i, title in enumerate(cluster_df['PROJECT_TITLE'].sample(10, random_state=42), 1):
        print(f"  {i}. {title[:100]}...")
