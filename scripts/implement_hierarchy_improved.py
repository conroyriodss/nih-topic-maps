#!/usr/bin/env python3
import json
import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

print("Loading data...")
with open('viz_data_project_terms_k100_final.json') as f:
    data = json.load(f)

points = data['points']
coords = np.array([[p['x'], p['y']] for p in points])
print(f"Loaded {len(points)} grants")

# Standardize coordinates
scaler = StandardScaler()
coords_scaled = scaler.fit_transform(coords)

print("\n" + "="*80)
print("APPROACH: Agglomerative Hierarchical Clustering (more spatial cohesion)")
print("="*80)

from sklearn.cluster import AgglomerativeClustering

# Level 1: 5 domains using Ward linkage (minimizes within-cluster variance)
print("\nLevel 1: Creating 5 domains with Ward linkage...")
agg_l1 = AgglomerativeClustering(n_clusters=5, linkage='ward')
domain_labels = agg_l1.fit_predict(coords_scaled)

from collections import Counter
domain_sizes = Counter(domain_labels)
print("Domain sizes:")
for domain_id in sorted(domain_sizes.keys()):
    size = domain_sizes[domain_id]
    pct = (size/len(points))*100
    print(f"  Domain {domain_id}: {size:,} ({pct:.1f}%)")

# Level 2: Use DBSCAN within each domain with tighter eps
print("\nLevel 2: Finding natural topics within each domain (DBSCAN)...")
topic_labels = np.zeros(len(points), dtype=int)
topic_id = 0

for domain_id in range(5):
    mask = domain_labels == domain_id
    domain_coords = coords_scaled[mask]
    
    # Adaptive DBSCAN parameters based on domain size
    domain_size = mask.sum()
    
    if domain_size < 100:
        # Very small domain - treat as single topic
        topic_labels[mask] = topic_id
        topic_id += 1
    else:
        # DBSCAN with tighter clustering (smaller eps = tighter clusters)
        eps = 0.25 if domain_size > 1000 else 0.35
        min_samples = max(20, int(domain_size * 0.01))
        
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        subtopic_labels = dbscan.fit_predict(domain_coords)
        
        n_clusters = len(set(subtopic_labels)) - (1 if -1 in subtopic_labels else 0)
        n_noise = list(subtopic_labels).count(-1)
        
        print(f"  Domain {domain_id}: {n_clusters} topics, {n_noise} noise points")
        
        # Assign noise to nearest cluster
        if n_noise > 0:
            noise_mask = subtopic_labels == -1
            cluster_centers = {}
            for label in set(subtopic_labels):
                if label != -1:
                    cluster_centers[label] = domain_coords[subtopic_labels == label].mean(axis=0)
            
            for i, noise_idx in enumerate(np.where(noise_mask)[0]):
                noise_coord = domain_coords[noise_idx]
                min_dist = float('inf')
                nearest = 0
                for label, center in cluster_centers.items():
                    dist = np.linalg.norm(noise_coord - center)
                    if dist < min_dist:
                        min_dist = dist
                        nearest = label
                subtopic_labels[noise_idx] = nearest
        
        # Map to global topic IDs
        unique_labels = sorted(set(subtopic_labels))
        for i, idx in enumerate(np.where(mask)[0]):
            topic_labels[idx] = topic_id + subtopic_labels[i]
        
        topic_id += len(unique_labels)

total_topics = len(set(topic_labels))
print(f"\nTotal topics: {total_topics}")

# Quality metrics
sil_domains = silhouette_score(coords_scaled, domain_labels, sample_size=10000)
sil_topics = silhouette_score(coords_scaled, topic_labels, sample_size=10000)
print(f"\nSilhouette scores:")
print(f"  Domains: {sil_domains:.3f}")
print(f"  Topics: {sil_topics:.3f}")

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
        for domain_id in range(5)
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

with open('viz_data_hierarchical_improved.json', 'w') as f:
    json.dump(viz_hierarchical, f)

print("\n" + "="*80)
print("✅ IMPROVED HIERARCHICAL CLUSTERING")
print("="*80)
print(f"\nStructure: 5 domains → {total_topics} topics")
print(f"Method: Ward linkage (better spatial cohesion)")
print(f"File: viz_data_hierarchical_improved.json")

