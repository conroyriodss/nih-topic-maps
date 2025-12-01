#!/usr/bin/env python3
import json
import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from collections import Counter

print("Loading data...")
with open('viz_data_project_terms_k100_final.json') as f:
    data = json.load(f)

points = data['points']
coords = np.array([[p['x'], p['y']] for p in points])
print(f"Loaded {len(points)} grants")

# Level 1: 5 domains (good balance)
print("\nLevel 1: Clustering into 5 major domains...")
scaler = StandardScaler()
coords_scaled = scaler.fit_transform(coords)

kmeans_l1 = KMeans(n_clusters=5, random_state=42, n_init=20)
domain_labels = kmeans_l1.fit_predict(coords_scaled)

domain_sizes = Counter(domain_labels)
print("\nDomain sizes:")
for domain_id in sorted(domain_sizes.keys()):
    size = domain_sizes[domain_id]
    pct = (size/len(points))*100
    print(f"  Domain {domain_id}: {size:,} grants ({pct:.1f}%)")

# Level 2: DBSCAN within each domain for natural topic flow
print("\nLevel 2: Using DBSCAN for natural topic boundaries...")
topic_labels = np.zeros(len(points), dtype=int)
topic_id = 0

for domain_id in range(5):
    mask = domain_labels == domain_id
    domain_coords = coords_scaled[mask]
    
    print(f"\n  Domain {domain_id}:")
    
    # DBSCAN with tuned parameters for natural clustering
    # eps controls neighborhood size, min_samples controls core point threshold
    dbscan = DBSCAN(eps=0.3, min_samples=50)
    subtopic_labels = dbscan.fit_predict(domain_coords)
    
    # Count clusters (excluding noise points labeled -1)
    n_clusters = len(set(subtopic_labels)) - (1 if -1 in subtopic_labels else 0)
    n_noise = list(subtopic_labels).count(-1)
    
    print(f"    Found {n_clusters} natural topics")
    print(f"    Noise points: {n_noise} ({100*n_noise/len(subtopic_labels):.1f}%)")
    
    # Assign noise points to nearest cluster
    noise_mask = subtopic_labels == -1
    if noise_mask.any():
        # For each noise point, find nearest cluster
        noise_coords = domain_coords[noise_mask]
        cluster_centers = {}
        for label in set(subtopic_labels):
            if label != -1:
                cluster_centers[label] = domain_coords[subtopic_labels == label].mean(axis=0)
        
        for i, noise_coord in enumerate(noise_coords):
            # Find nearest cluster center
            min_dist = float('inf')
            nearest_cluster = 0
            for label, center in cluster_centers.items():
                dist = np.linalg.norm(noise_coord - center)
                if dist < min_dist:
                    min_dist = dist
                    nearest_cluster = label
            
            # Assign to nearest cluster
            noise_indices = np.where(mask)[0][np.where(noise_mask)[0]]
            subtopic_labels[list(noise_mask).index(True) + i] = nearest_cluster
    
    # Map to global topic IDs
    unique_labels = sorted(set(subtopic_labels))
    label_mapping = {old_label: topic_id + i for i, old_label in enumerate(unique_labels)}
    
    for i, idx in enumerate(np.where(mask)[0]):
        topic_labels[idx] = label_mapping[subtopic_labels[i]]
    
    topic_id += len(unique_labels)

total_topics = len(set(topic_labels))
print(f"\n{'='*70}")
print(f"Total topics across all domains: {total_topics}")

# Calculate silhouette
from sklearn.metrics import silhouette_score
sil_domains = silhouette_score(coords_scaled, domain_labels, sample_size=10000)
print(f"Silhouette score (domains): {sil_domains:.3f}")

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
for topic_id in set(topic_labels):
    mask = topic_labels == topic_id
    domain_id = domain_labels[mask][0]
    viz_hierarchical['topics'].append({
        'id': int(topic_id),
        'domain': int(domain_id),
        'size': int(mask.sum()),
        'label': f'Topic {topic_id}'
    })

with open('viz_data_hierarchical_5_dbscan.json', 'w') as f:
    json.dump(viz_hierarchical, f)

print("\n" + "="*70)
print("HIERARCHICAL CLUSTERING COMPLETE (5 domains + DBSCAN topics)")
print("="*70)
print(f"\nStructure: 5 domains → {total_topics} natural topics")
print(f"File: viz_data_hierarchical_5_dbscan.json")
print(f"Silhouette score: {sil_domains:.3f}")
print("\nDBSCAN creates natural topic flow without forcing hard boundaries!")

