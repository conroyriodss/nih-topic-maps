#!/usr/bin/env python3
import json
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

print("Loading data...")
with open('viz_data_project_terms_k100_final.json') as f:
    data = json.load(f)

points = data['points']
coords = np.array([[p['x'], p['y']] for p in points])
print(f"Loaded {len(points)} grants")

# Level 1: Try K=3 for broader domains
print("\nClustering into 3 major domains...")
scaler = StandardScaler()
coords_scaled = scaler.fit_transform(coords)

kmeans_l1 = KMeans(n_clusters=3, random_state=42, n_init=20)
domain_labels = kmeans_l1.fit_predict(coords_scaled)

# Count sizes
from collections import Counter
domain_sizes = Counter(domain_labels)
print("\nDomain sizes:")
for domain_id in sorted(domain_sizes.keys()):
    size = domain_sizes[domain_id]
    pct = (size/len(points))*100
    print(f"  Domain {domain_id}: {size:,} grants ({pct:.1f}%)")

# Level 2: 10 topics per domain (total 30)
print("\nClustering each domain into 10 topics...")
topic_labels = np.zeros(len(points), dtype=int)
topic_id = 0

for domain_id in range(3):
    mask = domain_labels == domain_id
    domain_coords = coords_scaled[mask]
    
    if len(domain_coords) < 10:
        topic_labels[mask] = topic_id
        topic_id += 1
    else:
        kmeans_l2 = KMeans(n_clusters=10, random_state=42, n_init=10)
        subtopic_labels = kmeans_l2.fit_predict(domain_coords)
        
        for i, idx in enumerate(np.where(mask)[0]):
            topic_labels[idx] = topic_id + subtopic_labels[i]
        
        topic_id += 10

print(f"\nTotal topics: {len(set(topic_labels))}")

# Calculate silhouette score
from sklearn.metrics import silhouette_score
sil_domains = silhouette_score(coords_scaled, domain_labels, sample_size=10000)
print(f"\nSilhouette score (domains): {sil_domains:.3f}")

# Create visualization data
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
    'domains': [
        {'id': domain_id, 'size': int(domain_sizes[domain_id]), 'label': f'Domain {domain_id}'}
        for domain_id in range(3)
    ],
    'topics': []
}

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

with open('viz_data_hierarchical_3_30.json', 'w') as f:
    json.dump(viz_hierarchical, f)

print("\n" + "="*70)
print("HIERARCHICAL CLUSTERING COMPLETE (K=3)")
print("="*70)
print(f"\nStructure: 3 domains → {len(set(topic_labels))} topics")
print(f"File: viz_data_hierarchical_3_30.json")
print(f"Silhouette score: {sil_domains:.3f}")
print("\nThis should show broader, more natural domain boundaries!")

