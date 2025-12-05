#!/usr/bin/env python3
import json
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from collections import Counter

print("Loading data...")
with open('viz_data_project_terms_k100_final.json') as f:
    data = json.load(f)

points = data['points']
coords = np.array([[p['x'], p['y']] for p in points])

print(f"Loaded {len(points)} grants")

# Level 1: 5 domains
print("\nClustering into 5 major domains...")
scaler = StandardScaler()
coords_scaled = scaler.fit_transform(coords)

kmeans_l1 = KMeans(n_clusters=5, random_state=42, n_init=10)
domain_labels = kmeans_l1.fit_predict(coords_scaled)

# Count domain sizes
domain_sizes = Counter(domain_labels)
print("\nDomain sizes:")
for domain_id, size in sorted(domain_sizes.items()):
    print(f"  Domain {domain_id}: {size:,} grants")

# Level 2: 6 topics per domain
print("\nClustering each domain into 6 topics...")
topic_labels = np.zeros(len(points), dtype=int)
topic_id = 0

for domain_id in range(5):
    mask = domain_labels == domain_id
    domain_coords = coords_scaled[mask]
    
    if len(domain_coords) < 6:
        # Too small, assign as single topic
        topic_labels[mask] = topic_id
        topic_id += 1
    else:
        kmeans_l2 = KMeans(n_clusters=6, random_state=42, n_init=10)
        subtopic_labels = kmeans_l2.fit_predict(domain_coords)
        
        # Map to global topic IDs
        for i, idx in enumerate(np.where(mask)[0]):
            topic_labels[idx] = topic_id + subtopic_labels[i]
        
        topic_id += 6

print(f"\nTotal topics created: {len(set(topic_labels))}")

# Create new visualization data
print("\nCreating visualization data...")
viz_hierarchical = {
    'points': [
        {
            'application_id': p['application_id'],
            'x': p['x'],
            'y': p['y'],
            'domain': int(domain_labels[i]),
            'topic': int(topic_labels[i]),
            'cluster_old': p['cluster'],
            'ic': p['ic'],
            'year': p['year'],
            'cost': p['cost'],
            'title': p.get('title', '')
        }
        for i, p in enumerate(points)
    ],
    'domains': [],
    'topics': []
}

# Domain summaries
for domain_id in range(5):
    mask = domain_labels == domain_id
    viz_hierarchical['domains'].append({
        'id': domain_id,
        'size': int(mask.sum()),
        'label': f'Domain {domain_id}'
    })

# Topic summaries
for topic_id in set(topic_labels):
    mask = topic_labels == topic_id
    domain_id = domain_labels[mask][0]
    viz_hierarchical['topics'].append({
        'id': int(topic_id),
        'domain': int(domain_id),
        'size': int(mask.sum()),
        'label': f'Topic {topic_id}'
    })

# Save
with open('viz_data_hierarchical_5_30.json', 'w') as f:
    json.dump(viz_hierarchical, f)

print("\n" + "="*60)
print("HIERARCHICAL CLUSTERING COMPLETE")
print("="*60)
print(f"\nStructure: 5 domains → {len(set(topic_labels))} topics")
print(f"File: viz_data_hierarchical_5_30.json ({len(viz_hierarchical['points'])} grants)")
print("\nNext: Create visualization with this data")

