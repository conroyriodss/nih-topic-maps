#!/usr/bin/env python3
import json
from collections import Counter

def clean_label(phrase_str):
    """Clean and format a phrase for display"""
    parts = [p.strip() for p in phrase_str.split('/')]
    parts = [p for p in parts if p and p.lower() not in FILTER_TERMS]
    if len(parts) <= 1:
        return parts[0] if parts else "Unclassified"
    elif len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    else:
        return ", ".join(parts[:-1]) + f" and {parts[-1]}"

def get_top_terms(point_list, max_terms=4):
    """Extract top specific terms from points"""
    term_counter = Counter()
    for point in point_list:
        app_id = point['application_id']
        old_cluster = id_to_cluster.get(app_id)
        if old_cluster is not None and old_cluster in cluster_terms:
            terms = cluster_terms[old_cluster]
            specific_terms = [t for t in terms if t.lower() not in FILTER_TERMS]
            term_counter.update(specific_terms[:5])
    return term_counter

def create_short_label(term_counter, max_terms=3):
    """Create a concise, readable label"""
    if not term_counter:
        return "Unclassified Research"
    top_terms = [term for term, _ in term_counter.most_common(max_terms)]
    return " and ".join([clean_label(t) for t in top_terms])

def categorize_domain(domain_id, term_counter):
    """Assign recognizable category to domain"""
    top_terms_str = "; ".join([t for t, _ in term_counter.most_common(5)])
    
    if any(x in top_terms_str.lower() for x in ['xenograft', 'in vivo', 'wound', 'obesity']):
        return "In Vivo & Translational"
    elif any(x in top_terms_str.lower() for x in ['laboratory mouse', 'gene expression', 'protein structure']):
        return "Molecular and Cell Biology"
    elif any(x in top_terms_str.lower() for x in ['program', 'faculty', 'university', 'training']):
        return "Research Infrastructure"
    elif any(x in top_terms_str.lower() for x in ['imaging', 'tomography', 'x-ray']):
        return "Biomedical Imaging"
    elif any(x in top_terms_str.lower() for x in ['world health', 'global', 'epidemiology']):
        return "Epidemiology and Global Health"
    else:
        return "Cellular and Molecular Mechanisms"

print("Loading data...")
with open('viz_data_project_terms_k100_final.json') as f:
    data = json.load(f)
with open('viz_data_hierarchical_5_dbscan.json') as f:
    hier_data = json.load(f)

print("Extracting terms...")
id_to_cluster = {}
cluster_terms = {}
for point in data['points']:
    id_to_cluster[point['application_id']] = point['cluster']
for cluster in data['clusters']:
    terms = [t.strip() for t in cluster['label'].split(';') if t.strip()]
    cluster_terms[cluster['id']] = terms

FILTER_TERMS = {
    'cell', 'cells', 'protein', 'proteins', 'gene', 'genes', 
    'expression', 'function', 'regulation', 'activity', 'level',
    'development', 'role', 'mechanism', 'process', 'system',
    'study', 'studies', 'research', 'analysis', 'method',
    'data', 'model', 'disease', 'human', 'patient', 'clinical',
    'work', 'testing', 'base', 'goals', 'test', 'measure'
}

print("\n" + "="*80)
print("DOMAIN CATEGORIES AND LABELS")
print("="*80)

domain_labels = {}
domain_categories = {}

for domain in hier_data['domains']:
    domain_id = domain['id']
    domain_points = [p for p in hier_data['points'] if p['domain'] == domain_id]
    term_counter = get_top_terms(domain_points)
    
    short_label = create_short_label(term_counter, max_terms=3)
    category = categorize_domain(domain_id, term_counter)
    
    domain_labels[domain_id] = short_label
    domain_categories[domain_id] = category
    
    print(f"\n🔷 Domain {domain_id}: {category}")
    print(f"   {len(domain_points):,} grants ({100*len(domain_points)/43320:.1f}%)")
    print(f"   Topics: {len([t for t in hier_data['topics'] if t['domain']==domain_id])}")

print("\n" + "="*80)
print("TOPICS BY DOMAIN")
print("="*80)

topic_labels = {}
topics_by_domain = {}

for topic in hier_data['topics']:
    topic_id = topic['id']
    domain_id = topic['domain']
    if domain_id not in topics_by_domain:
        topics_by_domain[domain_id] = []
    topics_by_domain[domain_id].append(topic_id)

for domain_id in sorted(topics_by_domain.keys()):
    print(f"\n📊 {domain_categories[domain_id]}")
    for topic_id in sorted(topics_by_domain[domain_id]):
        topic_points = [p for p in hier_data['points'] if p['topic'] == topic_id]
        term_counter = get_top_terms(topic_points)
        label = create_short_label(term_counter, max_terms=3)
        topic_labels[topic_id] = label
        print(f"  Topic {topic_id:2d} ({len(topic_points):5,}): {label}")

# Update and save
for domain in hier_data['domains']:
    domain['label'] = domain_labels[domain['id']]
    domain['category'] = domain_categories[domain['id']]

for topic in hier_data['topics']:
    topic['label'] = topic_labels[topic['id']]

with open('viz_data_hierarchical_5_dbscan_final.json', 'w') as f:
    json.dump(hier_data, f)

print("\n" + "="*80)
print("✅ SAVED: viz_data_hierarchical_5_dbscan_final.json")
print("="*80)

