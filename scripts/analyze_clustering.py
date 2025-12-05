#!/usr/bin/env python3
"""
Analyze clustering quality and identify issues
"""
import json
import numpy as np
from collections import Counter, defaultdict

# Load viz data
print("Loading viz_data.json...")
with open('sample_viz.txt', 'r') as f:
    # Read first valid JSON (truncated file)
    content = f.read()
    # Find the complete JSON array
    import re
    match = re.search(r'\[.*\]', content, re.DOTALL)
    if match:
        data = json.loads(match.group(0))
    else:
        # Download fresh copy
        import subprocess
        subprocess.run(['gsutil', 'cat', 
                       'gs://od-cl-odss-conroyri-nih-embeddings/sample/viz_data.json'],
                      stdout=open('viz_data_full.json', 'w'))
        with open('viz_data_full.json') as f2:
            data = json.load(f2)

print(f"Loaded {len(data):,} grants")

# Analyze cluster sizes
topic_counts = Counter(d['topic'] for d in data)
print(f"\n=== Cluster Size Distribution ===")
print(f"Number of topics: {len(topic_counts)}")
print(f"Smallest cluster: {min(topic_counts.values())} grants")
print(f"Largest cluster: {max(topic_counts.values())} grants")
print(f"Mean cluster size: {np.mean(list(topic_counts.values())):.0f} grants")
print(f"Median cluster size: {np.median(list(topic_counts.values())):.0f} grants")

# Find problematic clusters
print(f"\n=== Very Small Clusters (<200 grants) ===")
small_clusters = [(topic, count) for topic, count in topic_counts.most_common()[::-1] if count < 200]
for topic, count in small_clusters[:10]:
    sample = [d for d in data if d['topic'] == topic][0]
    print(f"Topic {topic}: {count} grants - {sample['topic_label']}")

# Find very large clusters
print(f"\n=== Very Large Clusters (>1500 grants) ===")
large_clusters = [(topic, count) for topic, count in topic_counts.most_common() if count > 1500]
for topic, count in large_clusters:
    sample = [d for d in data if d['topic'] == topic][0]
    print(f"Topic {topic}: {count} grants - {sample['topic_label']}")

# Analyze spatial distribution
print(f"\n=== Spatial Distribution Analysis ===")
coords = np.array([[d['x'], d['y']] for d in data])
print(f"X range: [{coords[:, 0].min():.2f}, {coords[:, 0].max():.2f}]")
print(f"Y range: [{coords[:, 1].min():.2f}, {coords[:, 1].max():.2f}]")

# Find outlier clusters (far from center)
center = coords.mean(axis=0)
for topic in topic_counts:
    topic_coords = np.array([[d['x'], d['y']] for d in data if d['topic'] == topic])
    topic_center = topic_coords.mean(axis=0)
    dist_from_center = np.linalg.norm(topic_center - center)
    
    if dist_from_center > 10:  # Arbitrary threshold
        sample = [d for d in data if d['topic'] == topic][0]
        print(f"Outlier Topic {topic}: distance={dist_from_center:.1f}, size={len(topic_coords)}, label={sample['topic_label']}")

# IC distribution per topic
print(f"\n=== Topics with Multiple ICs (potential mixing) ===")
topic_ics = defaultdict(set)
for d in data:
    topic_ics[d['topic']].add(d['ic'])

mixed_topics = [(topic, len(ics)) for topic, ics in topic_ics.items() if len(ics) > 15]
mixed_topics.sort(key=lambda x: x[1], reverse=True)
for topic, ic_count in mixed_topics[:10]:
    sample = [d for d in data if d['topic'] == topic][0]
    print(f"Topic {topic}: {ic_count} different ICs - {sample['topic_label']}")

print("\n=== Analysis Complete ===")
