#!/usr/bin/env python3
"""
Create comprehensive visualization suite for 250k clusters
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

print("="*70)
print("CREATING VISUALIZATION SUITE FOR 250K CLUSTERS")
print("="*70)

# Load data
df = pd.read_csv('hierarchical_250k_clustered_k75.csv')
labels = pd.read_csv('cluster_75_labels.csv', index_col=0)

print(f"\nLoaded {len(df):,} grants in {df['cluster_k75'].nunique()} clusters")

# === VIZ 1: Main Topic Map with Labels ===
print("\n[1/4] Creating main topic map with cluster labels...")

fig, ax = plt.subplots(figsize=(20, 16))

# Sample 30k for performance
df_sample = df.sample(n=30000, random_state=42)

# Plot points
scatter = ax.scatter(
    df_sample['umap_x'],
    df_sample['umap_y'],
    c=df_sample['cluster_k75'],
    s=3,
    alpha=0.5,
    cmap='tab20c'
)

# Add cluster labels at centroids
cluster_stats = df.groupby('cluster_k75').agg({
    'umap_x': 'mean',
    'umap_y': 'mean',
    'APPLICATION_ID': 'count'
}).reset_index()

for _, row in cluster_stats.iterrows():
    cluster_id = int(row['cluster_k75'])
    label = labels.loc[cluster_id, 'label']
    
    # Shorten label if too long
    if len(label) > 25:
        label = label[:22] + '...'
    
    ax.text(
        row['umap_x'],
        row['umap_y'],
        f"{cluster_id}\n{label}",
        fontsize=7,
        ha='center',
        va='center',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.8, edgecolor='gray', linewidth=0.5)
    )

ax.set_xlabel('UMAP Dimension 1', fontsize=14)
ax.set_ylabel('UMAP Dimension 2', fontsize=14)
ax.set_title('NIH Grant Portfolio: 250,000 Grants in 75 Research Topic Clusters\nFY 2000-2024 | $126.24B Total Funding', 
             fontsize=16, fontweight='bold', pad=20)
ax.grid(True, alpha=0.2)

plt.tight_layout()
plt.savefig('nih_250k_labeled_map.png', dpi=150, bbox_inches='tight')
print("   ✅ Saved: nih_250k_labeled_map.png")

# === VIZ 2: Cluster Size Distribution ===
print("\n[2/4] Creating cluster size distribution...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

cluster_sizes = df['cluster_k75'].value_counts().sort_index()

# Histogram
ax1.hist(cluster_sizes.values, bins=30, color='steelblue', alpha=0.7, edgecolor='black')
ax1.axvline(cluster_sizes.median(), color='red', linestyle='--', linewidth=2, label=f'Median: {cluster_sizes.median():,.0f}')
ax1.axvline(cluster_sizes.mean(), color='orange', linestyle='--', linewidth=2, label=f'Mean: {cluster_sizes.mean():,.0f}')
ax1.set_xlabel('Cluster Size (# of grants)', fontsize=12)
ax1.set_ylabel('Number of Clusters', fontsize=12)
ax1.set_title('Distribution of Cluster Sizes', fontsize=14, fontweight='bold')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Bar chart of top 20
top20 = cluster_sizes.nlargest(20)
colors = plt.cm.viridis(np.linspace(0, 1, 20))
ax2.barh(range(20), top20.values, color=colors)
ax2.set_yticks(range(20))
ax2.set_yticklabels([f"C{c}" for c in top20.index])
ax2.set_xlabel('Number of Grants', fontsize=12)
ax2.set_title('Top 20 Largest Clusters', fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3, axis='x')

plt.tight_layout()
plt.savefig('nih_250k_cluster_sizes.png', dpi=150, bbox_inches='tight')
print("   ✅ Saved: nih_250k_cluster_sizes.png")

# === VIZ 3: Funding Distribution ===
print("\n[3/4] Creating funding distribution...")

fig, ax = plt.subplots(figsize=(16, 10))

# Sort labels by funding
labels_sorted = labels.sort_values('funding_millions', ascending=True).tail(30)

colors = plt.cm.RdYlGn(np.linspace(0.3, 0.9, 30))
bars = ax.barh(range(30), labels_sorted['funding_millions'], color=colors)

ax.set_yticks(range(30))
ax.set_yticklabels([f"C{idx}: {labels_sorted.loc[idx, 'label'][:35]}" 
                     for idx in labels_sorted.index], fontsize=9)
ax.set_xlabel('Total Funding (Millions $)', fontsize=12)
ax.set_title('Top 30 Clusters by Total Funding (FY 2000-2024)', 
             fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='x')

# Add value labels
for i, (idx, row) in enumerate(labels_sorted.iterrows()):
    ax.text(row['funding_millions'] + 50, i, f"${row['funding_millions']:,.0f}M", 
            va='center', fontsize=8)

plt.tight_layout()
plt.savefig('nih_250k_funding_distribution.png', dpi=150, bbox_inches='tight')
print("   ✅ Saved: nih_250k_funding_distribution.png")

# === VIZ 4: IC Distribution by Cluster ===
print("\n[4/4] Creating IC distribution heatmap...")

# Get top 15 ICs and top 20 clusters by size
top_ics = df['IC_NAME'].value_counts().head(15).index
top_clusters = cluster_sizes.nlargest(20).index

# Create IC-cluster matrix
ic_cluster_matrix = pd.crosstab(
    df[df['IC_NAME'].isin(top_ics)]['IC_NAME'],
    df[df['cluster_k75'].isin(top_clusters)]['cluster_k75']
)

fig, ax = plt.subplots(figsize=(16, 10))
im = ax.imshow(ic_cluster_matrix.values, cmap='YlOrRd', aspect='auto')

# Set ticks
ax.set_xticks(range(len(ic_cluster_matrix.columns)))
ax.set_xticklabels([f"C{c}" for c in ic_cluster_matrix.columns], rotation=0)
ax.set_yticks(range(len(ic_cluster_matrix.index)))
ax.set_yticklabels([ic.replace('NATIONAL INSTITUTE OF ', 'NI ').replace('NATIONAL INSTITUTE ON ', 'NI ')[:40] 
                     for ic in ic_cluster_matrix.index], fontsize=9)

ax.set_xlabel('Cluster ID', fontsize=12)
ax.set_ylabel('Institute/Center', fontsize=12)
ax.set_title('Grant Distribution: Top 15 ICs × Top 20 Clusters', 
             fontsize=14, fontweight='bold')

plt.colorbar(im, ax=ax, label='Number of Grants')
plt.tight_layout()
plt.savefig('nih_250k_ic_cluster_heatmap.png', dpi=150, bbox_inches='tight')
print("   ✅ Saved: nih_250k_ic_cluster_heatmap.png")

print("\n" + "="*70)
print("VISUALIZATION SUITE COMPLETE")
print("="*70)
print("\n📊 Created 4 comprehensive visualizations:")
print("   1. nih_250k_labeled_map.png - Main topic map with cluster labels")
print("   2. nih_250k_cluster_sizes.png - Size distribution analysis")
print("   3. nih_250k_funding_distribution.png - Top 30 by funding")
print("   4. nih_250k_ic_cluster_heatmap.png - IC × Cluster heatmap")
print("\n✅ Ready for presentations and reports!")
