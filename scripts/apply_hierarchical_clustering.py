#!/usr/bin/env python3
"""
Apply Best Hierarchical Clustering Configuration
Reads recommendations from parameter sweep and generates final clusters
"""
import pandas as pd
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
import json
import time
from collections import Counter

print("=" * 70)
print("APPLYING BEST HIERARCHICAL CLUSTERING CONFIGURATION")
print("=" * 70)

# Load recommendations
print("\n[1/5] Loading recommendations...")
try:
    with open('hierarchical_recommendations.json', 'r') as f:
        recommendations = json.load(f)
    best_config = recommendations['best_overall']
    print(f"  Best configuration:")
    print(f"    Linkage: {best_config['linkage_method']}")
    print(f"    Clusters: {best_config['n_clusters_actual']}")
    print(f"    Silhouette: {best_config['silhouette_score']:.4f}")
except FileNotFoundError:
    print("  ERROR: hierarchical_recommendations.json not found")
    print("  Run hierarchical_param_sweep.py first")
    exit(1)

# Load data
print("\n[2/5] Loading embeddings and metadata...")
df = pd.read_parquet('embeddings_100k_pubmedbert.parquet')
embeddings = np.stack(df['embedding'].values)
print(f"  Loaded {len(df):,} grants with {embeddings.shape[1]}-dim embeddings")

# Apply clustering
print(f"\n[3/5] Applying {best_config['linkage_method']} linkage clustering...")
start = time.time()

linkage_method = best_config['linkage_method']
n_clusters = best_config['n_clusters_actual']

if linkage_method == 'ward':
    Z = linkage(embeddings, method='ward')
else:
    from scipy.spatial.distance import pdist
    dist_matrix = pdist(embeddings, metric='euclidean')
    Z = linkage(dist_matrix, method=linkage_method)

labels = fcluster(Z, n_clusters, criterion='maxclust')
df['cluster'] = labels

print(f"  Clustering completed in {time.time() - start:.1f}s")
print(f"  Generated {len(np.unique(labels))} clusters")

# Generate topic labels
print("\n[4/5] Generating topic labels...")

# Try RCDC categories first
if 'NIH_SPENDING_CATS' in df.columns:
    print("  Using RCDC categories for labels...")
    
    def parse_rcdc(cat_string):
        if pd.isna(cat_string) or cat_string == '':
            return []
        return [c.strip() for c in str(cat_string).split(';') if c.strip()]
    
    df['rcdc_list'] = df['NIH_SPENDING_CATS'].apply(parse_rcdc)
    
    topic_labels = {}
    topic_stats = {}
    
    for cluster_id in range(1, n_clusters + 1):
        cluster_mask = labels == cluster_id
        cluster_size = cluster_mask.sum()
        
        # Get RCDC categories
        cluster_rcdc = df.loc[cluster_mask, 'rcdc_list'].tolist()
        all_terms = []
        for terms in cluster_rcdc:
            all_terms.extend(terms)
        
        if all_terms:
            top_terms = Counter(all_terms).most_common(3)
            label = ' | '.join([t[0] for t in top_terms])
        else:
            # Fallback to top project terms
            if 'PROJECT_TERMS' in df.columns:
                cluster_terms = df.loc[cluster_mask, 'PROJECT_TERMS'].dropna()
                if len(cluster_terms) > 0:
                    # Sample terms from multiple grants
                    sample = cluster_terms.sample(min(10, len(cluster_terms)))
                    all_terms = ' '.join(sample.values).split(';')
                    all_terms = [t.strip() for t in all_terms if t.strip()]
                    if all_terms:
                        top_terms = Counter(all_terms).most_common(3)
                        label = ' | '.join([t[0] for t in top_terms])
                    else:
                        label = f'Topic {cluster_id}'
                else:
                    label = f'Topic {cluster_id}'
            else:
                label = f'Topic {cluster_id}'
        
        topic_labels[cluster_id] = label
        
        # Collect statistics
        cluster_df = df[cluster_mask]
        topic_stats[cluster_id] = {
            'size': int(cluster_size),
            'fiscal_years': f"{cluster_df['FY'].min()}-{cluster_df['FY'].max()}",
            'n_ics': int(cluster_df['IC_NAME'].nunique()),
            'top_ic': cluster_df['IC_NAME'].value_counts().index[0] if len(cluster_df) > 0 else 'N/A',
            'total_funding': float(cluster_df['TOTAL_COST'].sum()) if 'TOTAL_COST' in cluster_df.columns else 0
        }
    
    df['topic_label'] = df['cluster'].map(topic_labels)

else:
    print("  WARNING: No RCDC categories available, using generic labels")
    topic_labels = {i: f'Topic {i}' for i in range(1, n_clusters + 1)}
    df['topic_label'] = df['cluster'].map(topic_labels)
    topic_stats = {}

# Display sample labels
print("\nSample topic labels (top 10 by size):")
cluster_sizes = df['cluster'].value_counts().head(10)
for cluster_id, count in cluster_sizes.items():
    label = topic_labels.get(cluster_id, f'Topic {cluster_id}')
    print(f"  Cluster {cluster_id:3d} ({count:5,} grants): {label[:70]}")

# Step 5: Save results
print("\n[5/5] Saving results...")

# Save cluster assignments
output_cols = ['APPLICATION_ID', 'CORE_PROJECT_NUM', 'PROJECT_TITLE', 
               'cluster', 'topic_label', 'IC_NAME', 'FY']
available_cols = [col for col in output_cols if col in df.columns]
df[available_cols].to_csv('hierarchical_best_clustering.csv', index=False)
print("  Saved: hierarchical_best_clustering.csv")

# Save topic labels
with open('hierarchical_topic_labels.json', 'w') as f:
    json.dump(topic_labels, f, indent=2)
print("  Saved: hierarchical_topic_labels.json")

# Save topic statistics
if topic_stats:
    with open('hierarchical_topic_stats.json', 'w') as f:
        json.dump(topic_stats, f, indent=2)
    print("  Saved: hierarchical_topic_stats.json")

# Save configuration metadata
metadata = {
    'clustering_method': 'hierarchical',
    'linkage_method': linkage_method,
    'n_clusters': n_clusters,
    'silhouette_score': float(best_config['silhouette_score']),
    'calinski_harabasz': float(best_config['calinski_harabasz']),
    'davies_bouldin': float(best_config['davies_bouldin']),
    'sample_size': len(df),
    'cluster_size_min': int(cluster_sizes.min()),
    'cluster_size_max': int(cluster_sizes.max()),
    'cluster_size_mean': float(cluster_sizes.mean()),
    'timestamp': pd.Timestamp.now().isoformat()
}

with open('hierarchical_clustering_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)
print("  Saved: hierarchical_clustering_metadata.json")

print("\n" + "=" * 70)
print("CLUSTERING APPLIED SUCCESSFULLY!")
print("=" * 70)

print(f"\nSummary:")
print(f"  Method: {linkage_method}")
print(f"  Clusters: {n_clusters}")
print(f"  Grants: {len(df):,}")
print(f"  Cluster sizes: {cluster_sizes.min():,} - {cluster_sizes.max():,} (mean: {cluster_sizes.mean():.0f})")

if topic_stats:
    # Funding summary
    total_funding = sum(s['total_funding'] for s in topic_stats.values())
    print(f"  Total funding represented: ${total_funding/1e9:.1f}B")

print("\nNext step: Run UMAP parameter sweep for visualization optimization")
print("  python3 scripts/umap_param_sweep.py")
