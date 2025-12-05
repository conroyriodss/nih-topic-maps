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
n_total = len(points)
print(f"Loaded {n_total} grants")

scaler = StandardScaler()
coords_scaled = scaler.fit_transform(coords)

# ============================================================
# LEVEL 1: 5 DOMAINS
# ============================================================
print("\n" + "="*80)
print("LEVEL 1: Creating 5 domains...")
print("="*80)

kmeans_l1 = KMeans(n_clusters=5, random_state=42, n_init=20)
domain_labels = kmeans_l1.fit_predict(coords_scaled)
domain_sizes = Counter(domain_labels)

for d in sorted(domain_sizes.keys()):
    pct = 100*domain_sizes[d]/n_total
    print(f"  Domain {d}: {domain_sizes[d]:,} ({pct:.1f}%)")

# ============================================================
# LEVEL 2: TOPICS within each domain
# ============================================================
print("\n" + "="*80)
print("LEVEL 2: Creating topics within domains...")
print("="*80)

topic_labels = np.zeros(n_total, dtype=int)
topic_id = 0

for domain_id in range(5):
    mask = domain_labels == domain_id
    domain_coords = coords_scaled[mask]
    domain_size = mask.sum()
    
    # Use K-means for more predictable topic counts
    # Number of topics based on domain size
    if domain_size > 5000:
        n_topics = 3
    elif domain_size > 2000:
        n_topics = 2
    else:
        n_topics = 1
    
    if n_topics == 1:
        for idx in np.where(mask)[0]:
            topic_labels[idx] = topic_id
        topic_id += 1
    else:
        kmeans_l2 = KMeans(n_clusters=n_topics, random_state=42, n_init=10)
        subtopic = kmeans_l2.fit_predict(domain_coords)
        for i, idx in enumerate(np.where(mask)[0]):
            topic_labels[idx] = topic_id + subtopic[i]
        topic_id += n_topics
    
    print(f"  Domain {domain_id}: {n_topics} topics")

total_topics = len(set(topic_labels))
print(f"\nTotal Level 2 topics: {total_topics}")

# ============================================================
# LEVEL 3: SUBTOPICS for large topics (>10%)
# ============================================================
print("\n" + "="*80)
print("LEVEL 3: Breaking down large topics (>10%) into subtopics...")
print("="*80)

subtopic_labels = topic_labels.copy()  # Start with topic labels
subtopic_id = total_topics  # Continue numbering

topic_sizes = Counter(topic_labels)
large_topics = [t for t, size in topic_sizes.items() if size/n_total > 0.10]
print(f"\nLarge topics (>10%): {large_topics}")

for large_topic in large_topics:
    mask = topic_labels == large_topic
    topic_coords = coords_scaled[mask]
    topic_size = mask.sum()
    pct = 100*topic_size/n_total
    
    print(f"\n  Breaking down Topic {large_topic} ({topic_size:,} grants, {pct:.1f}%)...")
    
    # Create 3-5 subtopics based on size
    if topic_size > 10000:
        n_subtopics = 5
    elif topic_size > 5000:
        n_subtopics = 4
    else:
        n_subtopics = 3
    
    kmeans_l3 = KMeans(n_clusters=n_subtopics, random_state=42, n_init=10)
    sub_labels = kmeans_l3.fit_predict(topic_coords)
    
    # Assign new subtopic IDs
    for i, idx in enumerate(np.where(mask)[0]):
        subtopic_labels[idx] = subtopic_id + sub_labels[i]
    
    # Show subtopic sizes
    sub_sizes = Counter(sub_labels)
    for s in sorted(sub_sizes.keys()):
        print(f"    Subtopic {subtopic_id + s}: {sub_sizes[s]:,} ({100*sub_sizes[s]/n_total:.1f}%)")
    
    subtopic_id += n_subtopics

total_subtopics = len(set(subtopic_labels))
print(f"\nTotal Level 3 subtopics: {total_subtopics}")

# ============================================================
# BUILD HIERARCHY DATA STRUCTURE
# ============================================================
print("\n" + "="*80)
print("Building hierarchy structure...")
print("="*80)

# Create visualization data with 3 levels
viz_data = {
    'points': [],
    'domains': [],
    'topics': [],
    'subtopics': []
}

# Points with all 3 levels
for i, p in enumerate(points):
    viz_data['points'].append({
        'application_id': p['application_id'],
        'x': p['x'],
        'y': p['y'],
        'domain': int(domain_labels[i]),
        'topic': int(topic_labels[i]),
        'subtopic': int(subtopic_labels[i]),
        'ic': p['ic'],
        'year': p['year'],
        'cost': p['cost'],
        'title': p.get('title', '')
    })

# Domains
for d in range(5):
    viz_data['domains'].append({
        'id': d,
        'size': int(domain_sizes[d]),
        'label': f'Domain {d}'
    })

# Topics
for t in sorted(set(topic_labels)):
    mask = topic_labels == t
    d = domain_labels[mask][0]
    viz_data['topics'].append({
        'id': int(t),
        'domain': int(d),
        'size': int(mask.sum()),
        'label': f'Topic {t}'
    })

# Subtopics
for st in sorted(set(subtopic_labels)):
    mask = subtopic_labels == st
    t = topic_labels[mask][0]
    d = domain_labels[mask][0]
    viz_data['subtopics'].append({
        'id': int(st),
        'topic': int(t),
        'domain': int(d),
        'size': int(mask.sum()),
        'label': f'Subtopic {st}'
    })

# Save
with open('viz_data_3level_hierarchy.json', 'w') as f:
    json.dump(viz_data, f)

print(f"\n✅ 3-Level Hierarchy Created:")
print(f"   Level 1: {len(viz_data['domains'])} domains")
print(f"   Level 2: {len(viz_data['topics'])} topics")
print(f"   Level 3: {len(viz_data['subtopics'])} subtopics")
print(f"\nSaved to: viz_data_3level_hierarchy.json")

# Show final structure
print("\n" + "="*80)
print("FINAL HIERARCHY STRUCTURE")
print("="*80)

for domain in viz_data['domains']:
    d_pct = 100*domain['size']/n_total
    print(f"\n📊 Domain {domain['id']} ({domain['size']:,}, {d_pct:.1f}%)")
    
    domain_topics = [t for t in viz_data['topics'] if t['domain'] == domain['id']]
    for topic in sorted(domain_topics, key=lambda x: x['id']):
        t_pct = 100*topic['size']/n_total
        print(f"   └─ Topic {topic['id']} ({topic['size']:,}, {t_pct:.1f}%)")
        
        topic_subtopics = [s for s in viz_data['subtopics'] if s['topic'] == topic['id']]
        for subtopic in sorted(topic_subtopics, key=lambda x: x['id']):
            s_pct = 100*subtopic['size']/n_total
            print(f"       └─ Subtopic {subtopic['id']} ({subtopic['size']:,}, {s_pct:.1f}%)")

