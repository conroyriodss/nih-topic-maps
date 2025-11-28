#!/usr/bin/env python3
"""
Generate multiple UMAP visualizations with different parameters for comparison
"""

import pandas as pd
import numpy as np
from umap import UMAP
import json
import subprocess
from collections import Counter

print("\n" + "="*70)
print("Generating Multiple UMAP Visualizations for Comparison")
print("="*70 + "\n")

# Load embeddings
print("Loading embeddings...")
subprocess.run(['gsutil', 'cp', 'gs://od-cl-odss-conroyri-nih-embeddings/sample/embeddings_project_terms_clustered_k100.parquet', 'data/processed/'], check=True, capture_output=True)
df = pd.read_parquet('data/processed/embeddings_project_terms_clustered_k100.parquet')
embeddings = np.array([np.array(emb) for emb in df['embedding']])

print(f"Loaded {len(embeddings):,} embeddings")

# Define UMAP configurations
configs = {
    'tight_clustering': {
        'n_neighbors': 10,
        'min_dist': 0.01,
        'spread': 1.0,
        'desc': 'Tight for clustering: n_neighbors=10, min_dist=0.01'
    },
    'balanced': {
        'n_neighbors': 15,
        'min_dist': 0.1,
        'spread': 1.0,
        'desc': 'Balanced: n_neighbors=15, min_dist=0.1'
    },
    'loose_visualization': {
        'n_neighbors': 40,
        'min_dist': 0.15,
        'spread': 1.2,
        'desc': 'Loose for visualization: n_neighbors=40, min_dist=0.15'
    },
    'very_tight': {
        'n_neighbors': 8,
        'min_dist': 0.01,
        'spread': 0.5,
        'desc': 'Very tight: n_neighbors=8, min_dist=0.01, spread=0.5'
    }
}

results = {}

# Generate each UMAP variant
for name, config in configs.items():
    print(f"\nGenerating {name}...")
    print(f"  {config['desc']}")
    
    umap_model = UMAP(
        n_components=2,
        n_neighbors=config['n_neighbors'],
        min_dist=config['min_dist'],
        spread=config['spread'],
        metric='cosine',
        random_state=42,
        verbose=False,
        n_epochs=200
    )
    
    coords = umap_model.fit_transform(embeddings)
    results[name] = coords
    
    print(f"  ✓ Complete")

# Create sample viz data for each config
import random
random.seed(42)
sample_idx = random.sample(range(len(df)), 3000)

for name, coords in results.items():
    print(f"\nCreating viz data for {name}...")
    
    sample_coords = coords[sample_idx]
    sample_df = df.iloc[sample_idx].copy()
    
    viz_data = {'points': [], 'clusters': [], 'config': configs[name]['desc']}
    
    for i, idx in enumerate(sample_idx):
        row = df.iloc[idx]
        viz_data['points'].append({
            'x': float(coords[idx, 0]),
            'y': float(coords[idx, 1]),
            'c': int(row['cluster']),
            'i': str(row['APPLICATION_ID'])[:8],
            'ic': str(row['IC_NAME'])[:3],
            'y': int(row['FISCAL_YEAR'])
        })
    
    # Add cluster info
    for cid in range(100):
        cdata = df[df['cluster'] == cid]
        if len(cdata) > 0:
            viz_data['clusters'].append({
                'id': cid,
                's': len(cdata)
            })
    
    # Save
    output = f'data/processed/viz_umap_{name}.json'
    with open(output, 'w') as f:
        json.dump(viz_data, f)
    
    size_mb = len(json.dumps(viz_data)) / 1024 / 1024
    print(f"  ✓ {output} ({size_mb:.1f} MB)")
    
    # Upload
    subprocess.run(['gsutil', 'cp', output, 'gs://od-cl-odss-conroyri-nih-embeddings/sample/'], check=True, capture_output=True)

print("\n" + "="*70)
print("UMAP Variants Generated")
print("="*70)
print("\nFiles created:")
for name in configs.keys():
    print(f"  - viz_umap_{name}.json")
print("\nComparison visualizations next...")
