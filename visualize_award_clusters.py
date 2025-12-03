#!/usr/bin/env python3
"""
Create comprehensive visualizations for award-level semantic clustering
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer

print("="*70)
print("CREATING AWARD CLUSTER VISUALIZATIONS")
print("="*70)

# Load clustered awards
print("\n[1/5] Loading data...")
df = pd.read_csv('awards_110k_with_semantic_clusters.csv')
print(f"Loaded {len(df):,} awards with semantic clusters")

# === VIZ 1: Main Topic Map ===
print("\n[2/5] Creating main topic map...")

fig, ax = plt.subplots(figsize=(20, 16))

# Sample for performance
sample_size = min(30000, len(df))
df_sample = df.sample(n=sample_size, random_state=42)

# Plot points
scatter = ax.scatter(
    df_sample['umap_x'],
    df_sample['umap_y'],
    c=df_sample['cluster_semantic_k75'],
    s=4,
    alpha=0.5,
    cmap='tab20c'
)

# Add cluster labels at centroids
cluster_stats = df.groupby('cluster_semantic_k75').agg({
    'umap_x': 'mean',
    'umap_y': 'mean',
    'core_project_num': 'count'
}).reset_index()

for _, row in cluster_stats.iterrows():
    cluster_id = int(row['cluster_semantic_k75'])
    ax.text(
        row['umap_x'],
        row['umap_y'],
        f"{cluster_id}",
        fontsize=9,
        ha='center',
        va='center',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='gray', linewidth=1)
    )

ax.set_xlabel('Dimension 1', fontsize=14)
ax.set_ylabel('Dimension 2', fontsize=14)
ax.set_title('NIH Award Portfolio: 103K Research Programs in 75 Semantic Clusters\nFY 2000-2024 | $179.7B Total Funding', 
             fontsize=16, fontweight='bold', pad=20)
ax.grid(True, alpha=0.2)

plt.tight_layout()
plt.savefig('award_semantic_map_103k.png', dpi=150, bbox_inches='tight')
print("   ✅ Saved: award_semantic_map_103k.png")
plt.close()

# === VIZ 2: Cluster Size Distribution ===
print("\n[3/5] Creating cluster distribution...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

cluster_sizes = df['cluster_semantic_k75'].value_counts().sort_index()

# Histogram
ax1.hist(cluster_sizes.values, bins=30, color='steelblue', alpha=0.7, edgecolor='black')
ax1.axvline(cluster_sizes.median(), color='red', linestyle='--', linewidth=2, label=f'Median: {cluster_sizes.median():.0f}')
ax1.axvline(cluster_sizes.mean(), color='orange', linestyle='--', linewidth=2, label=f'Mean: {cluster_sizes.mean():.0f}')
ax1.set_xlabel('Cluster Size (# of awards)', fontsize=12)
ax1.set_ylabel('Number of Clusters', fontsize=12)
ax1.set_title('Distribution of Semantic Cluster Sizes', fontsize=14, fontweight='bold')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Top 20
top20 = cluster_sizes.nlargest(20)
colors = plt.cm.viridis(np.linspace(0, 1, 20))
ax2.barh(range(20), top20.values, color=colors)
ax2.set_yticks(range(20))
ax2.set_yticklabels([f"C{c}" for c in top20.index])
ax2.set_xlabel('Number of Awards', fontsize=12)
ax2.set_title('Top 20 Largest Semantic Clusters', fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3, axis='x')

plt.tight_layout()
plt.savefig('award_cluster_sizes_semantic.png', dpi=150, bbox_inches='tight')
print("   ✅ Saved: award_cluster_sizes_semantic.png")
plt.close()

# === VIZ 3: Funding Distribution ===
print("\n[4/5] Creating funding distribution...")

cluster_funding = df.groupby('cluster_semantic_k75').agg({
    'total_lifetime_funding': 'sum',
    'core_project_num': 'count'
}).sort_values('total_lifetime_funding', ascending=True).tail(30)

fig, ax = plt.subplots(figsize=(16, 10))

colors = plt.cm.RdYlGn(np.linspace(0.3, 0.9, 30))
bars = ax.barh(range(30), cluster_funding['total_lifetime_funding']/1e9, color=colors)

ax.set_yticks(range(30))
ax.set_yticklabels([f"Cluster {idx}" for idx in cluster_funding.index], fontsize=10)
ax.set_xlabel('Total Funding (Billions $)', fontsize=12)
ax.set_title('Top 30 Semantic Clusters by Total Funding (FY 2000-2024)', 
             fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='x')

# Add value labels
for i, (idx, row) in enumerate(cluster_funding.iterrows()):
    ax.text(row['total_lifetime_funding']/1e9 + 0.05, i, 
            f"${row['total_lifetime_funding']/1e9:.1f}B ({row['core_project_num']:,} awards)", 
            va='center', fontsize=8)

plt.tight_layout()
plt.savefig('award_funding_distribution_semantic.png', dpi=150, bbox_inches='tight')
print("   ✅ Saved: award_funding_distribution_semantic.png")
plt.close()

# === VIZ 4: Cluster Labels with Keywords ===
print("\n[5/5] Generating cluster labels...")

# Extract keywords for all clusters
cluster_labels = []

for cluster_id in sorted(df['cluster_semantic_k75'].unique()):
    cluster_df = df[df['cluster_semantic_k75'] == cluster_id]
    
    vec = TfidfVectorizer(max_features=5, stop_words='english', ngram_range=(1,2))
    titles_combined = ' '.join(cluster_df['project_title'].head(100).tolist())
    
    try:
        vec.fit([titles_combined])
        keywords = ' & '.join([k.title() for k in vec.get_feature_names_out()[:3]])
    except:
        keywords = 'Cluster ' + str(cluster_id)
    
    cluster_labels.append({
        'cluster_id': cluster_id,
        'label': keywords,
        'n_awards': len(cluster_df),
        'funding_b': cluster_df['total_lifetime_funding'].sum()/1e9,
        'lead_ic': cluster_df['ic_name'].mode()[0] if len(cluster_df) > 0 else 'Unknown'
    })

labels_df = pd.DataFrame(cluster_labels)
labels_df.to_csv('award_cluster_labels_semantic.csv', index=False)
print("   ✅ Saved: award_cluster_labels_semantic.csv")

# Create summary report
print("\n" + "="*70)
print("TOP 15 SEMANTIC CLUSTERS BY FUNDING")
print("="*70)

top15 = labels_df.nlargest(15, 'funding_b')
for i, row in top15.iterrows():
    print(f"\n{i+1:2d}. Cluster {row['cluster_id']:2d}: {row['label']}")
    print(f"    Awards: {row['n_awards']:,} | Funding: ${row['funding_b']:.2f}B")
    print(f"    Lead IC: {row['lead_ic'][:60]}")

print("\n" + "="*70)
print("VISUALIZATION COMPLETE!")
print("="*70)
print("\nFiles created:")
print("  • award_semantic_map_103k.png")
print("  • award_cluster_sizes_semantic.png")
print("  • award_funding_distribution_semantic.png")
print("  • award_cluster_labels_semantic.csv")
print("\n✅ Award-level clustering and visualization complete!")
