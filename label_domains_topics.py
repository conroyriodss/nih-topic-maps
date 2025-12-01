#!/usr/bin/env python3
import json
from collections import Counter
import re

print("Loading hierarchical data...")
with open('viz_data_hierarchical_5_dbscan.json') as f:
    data = json.load(f)

print("Loading original data with PROJECT_TERMS...")
with open('viz_data_project_terms_k100_final.json') as f:
    original = json.load(f)

# Extract PROJECT_TERMS from cluster labels in original data
print("\nExtracting PROJECT_TERMS from original clustering...")
id_to_cluster = {}
cluster_terms = {}

for point in original['points']:
    id_to_cluster[point['application_id']] = point['cluster']

for cluster in original['clusters']:
    # Parse terms from label like "cell; protein; gene; expression; ..."
    terms = [t.strip() for t in cluster['label'].split(';') if t.strip()]
    cluster_terms[cluster['id']] = terms

print(f"Extracted terms for {len(cluster_terms)} original clusters")

# Generic/common terms to filter out (too broad)
FILTER_TERMS = {
    'cell', 'cells', 'protein', 'proteins', 'gene', 'genes', 
    'expression', 'function', 'regulation', 'activity', 'level',
    'development', 'role', 'mechanism', 'process', 'system',
    'study', 'studies', 'research', 'analysis', 'method',
    'data', 'model', 'disease', 'human', 'patient', 'clinical'
}

def get_terms_for_points(point_list):
    """Extract and count terms from a list of points"""
    term_counter = Counter()
    
    for point in point_list:
        app_id = point['application_id']
        old_cluster = id_to_cluster.get(app_id)
        if old_cluster is not None and old_cluster in cluster_terms:
            terms = cluster_terms[old_cluster]
            # Filter out generic terms
            specific_terms = [t for t in terms if t.lower() not in FILTER_TERMS]
            term_counter.update(specific_terms[:5])  # Top 5 terms per grant
    
    return term_counter

def create_label(term_counter, max_terms=4):
    """Create a descriptive label from top terms"""
    if not term_counter:
        return "Unclassified"
    
    top_terms = [term for term, count in term_counter.most_common(max_terms)]
    return '; '.join(top_terms)

print("\n" + "="*80)
print("LABELING DOMAINS")
print("="*80)

domain_labels = {}
for domain in data['domains']:
    domain_id = domain['id']
    domain_points = [p for p in data['points'] if p['domain'] == domain_id]
    
    print(f"\nDomain {domain_id} ({len(domain_points):,} grants):")
    
    # Get term frequencies
    term_counter = get_terms_for_points(domain_points)
    
    # Show top 10 terms with counts
    print("  Top terms:")
    for term, count in term_counter.most_common(10):
        pct = (count / len(domain_points)) * 100
        print(f"    {term}: {count} ({pct:.1f}%)")
    
    # Create label
    label = create_label(term_counter, max_terms=3)
    domain_labels[domain_id] = label
    print(f"  📋 Label: {label}")

print("\n" + "="*80)
print("LABELING TOPICS")
print("="*80)

topic_labels = {}
topics_by_domain = {}

for topic in data['topics']:
    topic_id = topic['id']
    domain_id = topic['domain']
    
    if domain_id not in topics_by_domain:
        topics_by_domain[domain_id] = []
    topics_by_domain[domain_id].append(topic_id)

for domain_id in sorted(topics_by_domain.keys()):
    print(f"\n🔷 Domain {domain_id}: {domain_labels[domain_id]}")
    
    for topic_id in sorted(topics_by_domain[domain_id]):
        topic = next(t for t in data['topics'] if t['id'] == topic_id)
        topic_points = [p for p in data['points'] if p['topic'] == topic_id]
        
        print(f"\n  Topic {topic_id} ({len(topic_points):,} grants):")
        
        # Get term frequencies
        term_counter = get_terms_for_points(topic_points)
        
        # Show top 8 terms
        print("    Top terms:")
        for term, count in term_counter.most_common(8):
            pct = (count / len(topic_points)) * 100
            print(f"      {term}: {count} ({pct:.1f}%)")
        
        # Create label
        label = create_label(term_counter, max_terms=4)
        topic_labels[topic_id] = label
        print(f"    📌 Label: {label}")

# Update data with labels
for domain in data['domains']:
    domain['label'] = domain_labels[domain['id']]

for topic in data['topics']:
    topic['label'] = topic_labels[topic['id']]

# Save labeled data
with open('viz_data_hierarchical_5_dbscan_labeled.json', 'w') as f:
    json.dump(data, f)

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"\n5 Domains:")
for domain_id, label in sorted(domain_labels.items()):
    size = next(d['size'] for d in data['domains'] if d['id'] == domain_id)
    print(f"  Domain {domain_id} ({size:,} grants): {label}")

print(f"\n15 Topics (grouped by domain):")
for domain_id in sorted(topics_by_domain.keys()):
    print(f"\n  {domain_labels[domain_id]}:")
    for topic_id in sorted(topics_by_domain[domain_id]):
        size = next(t['size'] for t in data['topics'] if t['id'] == topic_id)
        print(f"    Topic {topic_id} ({size:,}): {topic_labels[topic_id]}")

print(f"\n✅ Saved to: viz_data_hierarchical_5_dbscan_labeled.json")

