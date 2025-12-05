#!/usr/bin/env python3
"""
Create visualization of 250k clusters using matplotlib
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

print("Creating 250k visualization...")

# Load clustered data
df = pd.read_csv('hierarchical_250k_clustered_k75.csv')
print(f"Loaded {len(df):,} grants with {df['cluster_k75'].nunique()} clusters")

# Sample for visualization performance
sample_size = 50000
df_sample = df.sample(n=sample_size, random_state=42)
print(f"Sampling {sample_size:,} grants for visualization")

# Create figure
fig, ax = plt.subplots(figsize=(16, 12))

# Plot points colored by cluster
scatter = ax.scatter(
    df_sample['umap_x'],
    df_sample['umap_y'],
    c=df_sample['cluster_k75'],
    s=5,
    alpha=0.6,
    cmap='tab20'
)

# Add cluster centroids and labels
cluster_stats = df.groupby('cluster_k75').agg({
    'umap_x': 'mean',
    'umap_y': 'mean',
    'APPLICATION_ID': 'count'
}).reset_index()

for _, row in cluster_stats.iterrows():
    ax.text(
        row['umap_x'],
        row['umap_y'],
        f"C{int(row['cluster_k75'])}",
        fontsize=8,
        ha='center',
        va='center',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7, edgecolor='black')
    )

ax.set_xlabel('UMAP Dimension 1', fontsize=12)
ax.set_ylabel('UMAP Dimension 2', fontsize=12)
ax.set_title(f'NIH Grant Topic Map: 250,000 Grants, 75 Clusters\n(Showing {sample_size:,} sampled grants)', 
             fontsize=14, fontweight='bold')

plt.colorbar(scatter, ax=ax, label='Cluster ID', pad=0.02)
plt.tight_layout()

# Save
output_file = 'nih_topic_map_250k_k75.png'
plt.savefig(output_file, dpi=150, bbox_inches='tight')
print(f"✅ Saved: {output_file}")

# Also create cluster summary stats
cluster_stats_full = df.groupby('cluster_k75').agg({
    'APPLICATION_ID': 'count',
    'TOTAL_COST': 'sum',
    'IC_NAME': lambda x: x.mode()[0] if len(x) > 0 else 'Unknown',
    'FY': ['min', 'max']
}).round(0)
cluster_stats_full.columns = ['n_grants', 'total_funding', 'lead_ic', 'fy_min', 'fy_max']
cluster_stats_full.to_csv('cluster_250k_stats.csv')
print(f"✅ Saved: cluster_250k_stats.csv")

print(f"\n📊 Quick Stats:")
print(f"   Largest cluster: {cluster_stats['APPLICATION_ID'].max():,.0f} grants")
print(f"   Smallest cluster: {cluster_stats['APPLICATION_ID'].min():,.0f} grants")
print(f"   Average cluster: {cluster_stats['APPLICATION_ID'].mean():,.0f} grants")

