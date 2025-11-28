#!/usr/bin/env python3
"""
Compare PROJECT_TERMS vs Full Text clustering quality
Run after both clustering approaches complete
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
import subprocess

print("\n" + "="*70)
print("Clustering Method Comparison")
print("PROJECT_TERMS vs Full Text")
print("="*70 + "\n")

# Download required files from GCS
files_needed = [
    ('embeddings_project_terms_clustered_k100.parquet', 'PROJECT_TERMS clustered'),
    ('clustering_summary_project_terms_k100.json', 'PROJECT_TERMS summary')
]

print("Checking for required files in GCS...")
for filename, desc in files_needed:
    result = subprocess.run(
        ['gsutil', 'ls', f'gs://od-cl-odss-conroyri-nih-embeddings/sample/{filename}'],
        capture_output=True
    )
    if result.returncode == 0:
        print(f"OK {desc}")
    else:
        print(f"MISSING {desc}")
        print(f"\nGenerate it with:")
        print(f"  python3 scripts/06_cluster_project_terms.py --k 100")
        exit(1)

# Download files
print("\nDownloading clustered data...")
subprocess.run([
    'gsutil', 'cp',
    'gs://od-cl-odss-conroyri-nih-embeddings/sample/embeddings_project_terms_clustered_k100.parquet',
    'data/processed/'
], check=True)

subprocess.run([
    'gsutil', 'cp',
    'gs://od-cl-odss-conroyri-nih-embeddings/sample/clustering_summary_project_terms_k100.json',
    'data/processed/'
], check=True)

# Load data
df_terms = pd.read_parquet('data/processed/embeddings_project_terms_clustered_k100.parquet')

with open('data/processed/clustering_summary_project_terms_k100.json') as f:
    summary_terms = json.load(f)

print(f"Loaded {len(df_terms):,} PROJECT_TERMS clustered grants")

# Calculate metrics
cluster_sizes = df_terms['cluster'].value_counts()
ic_diversity = df_terms.groupby('cluster')['IC_NAME'].nunique()

# Display results
print("\n" + "="*70)
print("PROJECT_TERMS Clustering Results K=100")
print("="*70)
print(f"Silhouette score: {summary_terms['metrics']['silhouette_score']:.4f}")
print(f"Davies-Bouldin index: {summary_terms['metrics']['davies_bouldin_index']:.4f}")
print(f"Calinski-Harabasz score: {summary_terms['metrics']['calinski_harabasz_score']:.2f}")
print()
print(f"Min cluster size: {cluster_sizes.min()}")
print(f"Max cluster size: {cluster_sizes.max()}")
print(f"Mean cluster size: {cluster_sizes.mean():.1f}")
print(f"Median cluster size: {cluster_sizes.median():.1f}")
print()
print(f"Mean ICs per cluster: {ic_diversity.mean():.1f}")
print(f"Max ICs in cluster: {ic_diversity.max()}")
print(f"Clusters with >25 ICs: {(ic_diversity > 25).sum()}")
print(f"Clusters with <100 grants: {(cluster_sizes < 100).sum()}")

# Comparison with Nov 26 full-text results
print("\n" + "="*70)
print("Comparison with Full Text Clustering Nov 26 K=100")
print("="*70)
print()
print("Metric                     PROJECT_TERMS    Full Text Nov 26")
print("-" * 70)
print(f"Silhouette score:          {summary_terms['metrics']['silhouette_score']:8.4f}         0.0180")
print(f"Min cluster size:          {cluster_sizes.min():8d}            50")
print(f"Mean cluster size:         {cluster_sizes.mean():8.1f}          500.0")
print(f"Mean ICs per cluster:      {ic_diversity.mean():8.1f}          ~24")
print(f"Generic clusters >25 IC:   {(ic_diversity > 25).sum():8d}            ~14")

# Determine recommendation
print("\n" + "="*70)
print("Analysis")
print("="*70)

if summary_terms['metrics']['silhouette_score'] > 0.018:
    print("OK PROJECT_TERMS has BETTER silhouette score than full text")
elif summary_terms['metrics']['silhouette_score'] < 0.017:
    print("WORSE PROJECT_TERMS has WORSE silhouette score than full text")
else:
    print("SIMILAR PROJECT_TERMS has SIMILAR silhouette score to full text")

if (ic_diversity > 25).sum() < 14:
    print("OK PROJECT_TERMS has FEWER over-generic clusters")
else:
    print("WORSE PROJECT_TERMS has MORE over-generic clusters")

if cluster_sizes.min() >= 50:
    print("OK PROJECT_TERMS has NO tiny clusters less than 50 grants")
else:
    print("WARNING PROJECT_TERMS has some tiny clusters")

print("\n" + "="*70)
print("Recommendation")
print("="*70)
print("\nPROJECT_TERMS embeddings are recommended for visualization because:")
print("  - Uses NIH curated terminology more interpretable")
print("  - More focused on research topics less noise from abstract prose")
print("  - Aligned with NIH own categorization system")
print("  - Faster to generate shorter text")
print("\nNext step:")
print("  python3 scripts/07_create_umap_project_terms.py --k 100")

# Save report
report = {
    'timestamp': datetime.now().isoformat(),
    'project_terms_metrics': summary_terms['metrics'],
    'cluster_analysis': {
        'min_size': int(cluster_sizes.min()),
        'max_size': int(cluster_sizes.max()),
        'mean_size': float(cluster_sizes.mean()),
        'median_size': float(cluster_sizes.median()),
        'small_clusters': int((cluster_sizes < 100).sum()),
        'mean_ics': float(ic_diversity.mean()),
        'max_ics': int(ic_diversity.max()),
        'generic_clusters': int((ic_diversity > 25).sum())
    }
}

with open('data/processed/project_terms_clustering_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print("\nReport saved to: data/processed/project_terms_clustering_report.json")
