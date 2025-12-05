#!/usr/bin/env python3
"""
Option 3: IC-based Hierarchical Clustering
- First level: 27 ICs
- Second level: 10-20 topics within each IC
- Result: Natural hierarchy matching NIH structure
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from umap import UMAP
import json
import subprocess
from collections import Counter

print("="*70)
print("IC-BASED HIERARCHICAL CLUSTERING")
print("="*70 + "\n")

# Load data
df = pd.read_parquet('data/processed/embeddings_project_terms_clustered_k100.parquet')
print(f"Total grants: {len(df):,}")

# Generic stopwords
generic_terms = [
    'testing', 'goals', 'data', 'development', 'research', 'base', 'role', 
    'novel', 'disease', 'human', 'modeling', 'cells', 'work', 'improved', 
    'address', 'time', 'patients', 'response', 'process', 'clinical', 
    'mediating', 'molecular', 'affect', 'individual', 'design', 'programs', 
    'methods', 'system', 'measures', 'proteins', 'pathway interactions', 
    'in vivo', 'signal transduction', 'outcome', 'research personnel', 
    'health', 'lead', 'population', 'genes', 'knowledge', 'complex', 
    'insight', 'play', 'structure', 'link', 'prevent', 'future', 
    'innovation', 'experience', 'tissues'
]

def clean_terms(terms_str):
    if pd.isna(terms_str):
        return ""
    terms = str(terms_str).split(';')
    filtered = [t.strip() for t in terms 
                if t.strip().lower() not in generic_terms 
                and len(t.strip()) > 3]
    return ' '.join(filtered)

df['clean_terms'] = df['PROJECT_TERMS'].apply(clean_terms)

# IC distribution
ic_counts = df['IC_NAME'].value_counts()
print(f"\nICs: {len(ic_counts)}")
print(f"Top 5 ICs:")
for ic, count in ic_counts.head(5).items():
    print(f"  {ic}: {count:,} grants")

# Cluster WITHIN each IC
print("\n" + "-"*70)
print("CLUSTERING WITHIN EACH IC")
print("-"*70)

all_results = []
ic_summaries = []

for ic_name in ic_counts.index:
    ic_data = df[df['IC_NAME'] == ic_name].copy()
    n_grants = len(ic_data)
    
    if n_grants < 50:
        print(f"  {ic_name}: {n_grants} grants (skipping - too few)")
        continue
    
    # Determine K for this IC
    k = min(max(5, n_grants // 100), 20)
    
    print(f"  {ic_name}: {n_grants:,} grants → K={k} topics")
    
    # TF-IDF for this IC
    tfidf = TfidfVectorizer(max_features=2000, min_df=2, max_df=0.8)
    try:
        tfidf_matrix = tfidf.fit_transform(ic_data['clean_terms'])
    except:
        print(f"    Skipping {ic_name} - TF-IDF failed")
        continue
    
    # K-means
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    ic_data['ic_cluster'] = kmeans.fit_predict(tfidf_matrix)
    
    # Create global cluster ID
    for local_cluster in range(k):
        cluster_data = ic_data[ic_data['ic_cluster'] == local_cluster]
        
        # Get top terms for label
        all_terms = []
        for t in cluster_data['clean_terms'].head(30):
            all_terms.extend(t.split()[:5])
        top = [term for term, _ in Counter(all_terms).most_common(3)]
        label = ' / '.join(top) if top else f'{ic_name}-{local_cluster}'
        
        ic_summaries.append({
            'ic': ic_name,
            'local_cluster': local_cluster,
            'label': label,
            'size': len(cluster_data)
        })
    
    # Store results
    ic_data['global_label'] = ic_data.apply(
        lambda r: f"{ic_name}-{r['ic_cluster']}", axis=1
    )
    all_results.append(ic_data)

# Combine all results
df_clustered = pd.concat(all_results, ignore_index=True)
print(f"\nTotal clustered: {len(df_clustered):,} grants")
print(f"Total IC-topics: {len(ic_summaries)}")

# Generate UMAP for visualization
print("\nGenerating UMAP...")

tfidf_global = TfidfVectorizer(max_features=3000, min_df=3, max_df=0.7)
tfidf_matrix = tfidf_global.fit_transform(df_clustered['clean_terms'])

umap_model = UMAP(
    n_components=2,
    n_neighbors=30,
    min_dist=0.1,
    metric='cosine',
    random_state=42,
    verbose=False
)

umap_coords = umap_model.fit_transform(tfidf_matrix.toarray())

# Create viz data
print("\nCreating visualization data...")
import random
random.seed(42)
sample_idx = random.sample(range(len(df_clustered)), min(5000, len(df_clustered)))

viz_data = {'points': [], 'clusters': ic_summaries}

for idx in sample_idx:
    row = df_clustered.iloc[idx]
    viz_data['points'].append({
        'x': float(umap_coords[idx, 0]),
        'y': float(umap_coords[idx, 1]),
        'ic': str(row['IC_NAME']),
        'c': str(row['global_label']),
        'yr': int(row['FISCAL_YEAR'])
    })

with open('data/processed/viz_ic_hierarchical.json', 'w') as f:
    json.dump(viz_data, f)

subprocess.run(['gsutil', 'cp', 'data/processed/viz_ic_hierarchical.json', 
                'gs://od-cl-odss-conroyri-nih-embeddings/sample/'], 
               check=True, capture_output=True)

print("\n" + "="*70)
print("IC HIERARCHICAL CLUSTERING COMPLETE")
print("="*70)
print(f"\nTotal grants: {len(df_clustered):,}")
print(f"Total ICs: {df_clustered['IC_NAME'].nunique()}")
print(f"Total IC-topics: {len(ic_summaries)}")
print(f"\nIC-topics per IC (sample):")
for ic in ic_counts.head(5).index:
    count = sum(1 for s in ic_summaries if s['ic'] == ic)
    print(f"  {ic}: {count} topics")

print(f"\nSaved: viz_ic_hierarchical.json")
