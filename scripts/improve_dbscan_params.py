#!/usr/bin/env python3
import json
import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler

print("Loading data...")
with open('viz_data_project_terms_k100_final.json') as f:
    data = json.load(f)

points = data['points']
coords = np.array([[p['x'], p['y']] for p in points])
print(f"Loaded {len(points)} grants")

scaler = StandardScaler()
coords_scaled = scaler.fit_transform(coords)

print("\nLevel 1: K-means clustering into 5 domains...")
kmeans_l1 = KMeans(n_clusters=5, random_state=42, n_init=20)
domain_labels = kmeans_l1.fit_predict(coords_scaled)

from collections import Counter
domain_sizes = Counter(domain_labels)
print("Domain sizes:")
for d in sorted(domain_sizes.keys()):
    print(f"  Domain {d}: {domain_sizes[d]:,} ({100*domain_sizes[d]/len(points):.1f}%)")

print("\nLevel 2: DBSCAN with TIGHTER parameters (better coalescence)...")
topic_labels = np.zeros(len(points), dtype=int)
topic_id = 0

for domain_id in range(5):
    mask = domain_labels == domain_id
    domain_coords = coords_scaled[mask]
    domain_size = mask.sum()
    
    # TIGHTER PARAMETERS for better visual coalescence
    # Smaller eps = tighter clusters that don't spread as far
    eps = 0.2  # Reduced from 0.25-0.35
    min_samples = max(15, int(domain_size * 0.005))  # Fewer min_samples = fewer tiny clusters
    
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    subtopic_labels = dbscan.fit_predict(domain_coords)
    
    n_clusters = len(set(subtopic_labels)) - (1 if -1 in subtopic_labels else 0)
    n_noise = list(subtopic_labels).count(-1)
    
    print(f"  Domain {domain_id}: {n_clusters} topics, {n_noise} noise pts ({100*n_noise/domain_size:.1f}%)")
    
    # Assign noise to nearest cluster center
    if n_noise > 0:
        noise_mask = subtopic_labels == -1
        cluster_centers = {}
        for label in set(subtopic_labels):
            if label != -1:
                cluster_centers[label] = domain_coords[subtopic_labels == label].mean(axis=0)
        
        for noise_idx in np.where(noise_mask)[0]:
            noise_coord = domain_coords[noise_idx]
            nearest_label = min(cluster_centers.keys(), 
                              key=lambda l: np.linalg.norm(noise_coord - cluster_centers[l]))
            subtopic_labels[noise_idx] = nearest_label
    
    # Map to global topic IDs
    unique_labels = sorted(set(subtopic_labels))
    for i, idx in enumerate(np.where(mask)[0]):
        topic_labels[idx] = topic_id + subtopic_labels[i]
    
    topic_id += len(unique_labels)

total_topics = len(set(topic_labels))
print(f"\nTotal topics: {total_topics}")

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
        {'id': d, 'size': int(domain_sizes[d]), 'label': f'Domain {d}'}
        for d in range(5)
    ],
    'topics': []
}

# Topic summaries
for topic_id in sorted(set(topic_labels)):
    mask = topic_labels == topic_id
    domain_id = domain_labels[mask][0]
    viz_hierarchical['topics'].append({
        'id': int(topic_id),
        'domain': int(domain_id),
        'size': int(mask.sum()),
        'label': f'Topic {topic_id}'
    })

with open('viz_data_hierarchical_5_dbscan_final.json', 'w') as f:
    json.dump(viz_hierarchical, f)

print("\n" + "="*80)
print("✅ TIGHTENED DBSCAN CLUSTERING")
print("="*80)
print(f"Structure: 5 domains → {total_topics} topics")
print(f"Parameters: eps=0.2, min_samples={int(domain_sizes[0]*0.005)}")
print(f"Result: Tighter, more coalesced topics")

