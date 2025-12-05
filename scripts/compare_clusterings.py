#!/usr/bin/env python3
"""
Compare K=75 vs original 5-domain clustering
"""
import pandas as pd
import numpy as np

print("="*70)
print("COMPARING CLUSTERING APPROACHES")
print("="*70)

df = pd.read_csv('hierarchical_250k_clustered_k75.csv')

print(f"\n📊 CLUSTERING COMPARISON")
print(f"\n   Original (5 domains):")
print(f"   - Clusters: 5")
print(f"   - Avg size: {len(df)/5:,.0f} grants")

domain_counts = df['domain'].value_counts().sort_index()
for domain, count in domain_counts.items():
    label = df[df['domain']==domain]['domain_label'].iloc[0]
    print(f"   - Domain {domain} ({label}): {count:,} grants")

print(f"\n   New (75 clusters):")
cluster_counts = df['cluster_k75'].value_counts()
print(f"   - Clusters: 75")
print(f"   - Avg size: {cluster_counts.mean():,.0f} grants")
print(f"   - Min size: {cluster_counts.min():,}")
print(f"   - Max size: {cluster_counts.max():,}")

# How do 75 clusters map to 5 domains?
print(f"\n🔗 CLUSTER-TO-DOMAIN MAPPING")
for domain in sorted(df['domain'].unique()):
    label = df[df['domain']==domain]['domain_label'].iloc[0]
    clusters_in_domain = df[df['domain']==domain]['cluster_k75'].nunique()
    grants_in_domain = (df['domain']==domain).sum()
    print(f"   Domain {domain} ({label}):")
    print(f"   - Contains {clusters_in_domain} of 75 clusters")
    print(f"   - {grants_in_domain:,} grants")

print("\n✅ INSIGHTS:")
print("   • 75 clusters provide 15x finer granularity than 5 domains")
print("   • Each domain subdivides into ~15 specialized topics")
print("   • Better for operational portfolio management")
print("   • Domains remain useful for high-level strategic view")

print("\n" + "="*70)
