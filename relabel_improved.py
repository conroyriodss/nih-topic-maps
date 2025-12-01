#!/usr/bin/env python3
import json
from collections import Counter

def get_top_terms(point_list, max_terms=8):
    term_counter = Counter()
    for point in point_list:
        app_id = point['application_id']
        old_cluster = id_to_cluster.get(app_id)
        if old_cluster is not None and old_cluster in cluster_terms:
            terms = cluster_terms[old_cluster]
            term_counter.update(terms[:5])
    return term_counter

def create_smart_label(term_counter, domain_category, max_terms=3):
    if not term_counter:
        return domain_category
    
    generic = {
        'cell', 'cells', 'protein', 'proteins', 'gene', 'genes', 
        'expression', 'function', 'regulation', 'activity', 'level',
        'development', 'role', 'mechanism', 'process', 'system',
        'study', 'studies', 'research', 'analysis', 'method',
        'data', 'model', 'disease', 'human', 'patient', 'clinical',
        'work', 'testing', 'base', 'goals', 'test', 'measure'
    }
    
    specific_terms = [(t, c) for t, c in term_counter.most_common(20) 
                      if t.lower() not in generic]
    
    if specific_terms:
        top_terms = [t for t, _ in specific_terms[:max_terms]]
    else:
        top_terms = [t for t, _ in term_counter.most_common(max_terms)]
    
    if not top_terms:
        return domain_category
    
    result = " and ".join(top_terms)
    result = result.replace(' / ', ' and ').replace('/', ' and ')
    return result.title()

def categorize_domain(term_counter):
    top_terms_str = "; ".join([t for t, _ in term_counter.most_common(8)])
    
    if any(x in top_terms_str.lower() for x in ['xenograft', 'in vivo', 'wound', 'obesity']):
        return "In Vivo and Translational"
    elif any(x in top_terms_str.lower() for x in ['laboratory mouse', 'gene expression', 'protein structure']):
        return "Molecular and Cell Biology"
    elif any(x in top_terms_str.lower() for x in ['program', 'faculty', 'university', 'training']):
        return "Research Infrastructure and Training"
    elif any(x in top_terms_str.lower() for x in ['imaging', 'tomography', 'x-ray']):
        return "Biomedical Imaging and Analysis"
    elif any(x in top_terms_str.lower() for x in ['world health', 'global', 'epidemiology']):
        return "Epidemiology and Global Health"
    else:
        return "Cellular and Molecular Mechanisms"

print("Loading data...")
with open('viz_data_project_terms_k100_final.json') as f:
    data = json.load(f)
with open('viz_data_hierarchical_improved.json') as f:
    hier_data = json.load(f)

id_to_cluster = {}
cluster_terms = {}
for point in data['points']:
    id_to_cluster[point['application_id']] = point['cluster']
for cluster in data['clusters']:
    terms = [t.strip() for t in cluster['label'].split(';') if t.strip()]
    cluster_terms[cluster['id']] = terms

print("\nLabeling domains and topics...")

domain_info = {}
for domain in hier_data['domains']:
    domain_id = domain['id']
    domain_points = [p for p in hier_data['points'] if p['domain'] == domain_id]
    term_counter = get_top_terms(domain_points)
    category = categorize_domain(term_counter)
    domain_info[domain_id] = {'category': category, 'size': len(domain_points), 'terms': term_counter}

topic_labels = {}
for domain_id in sorted(domain_info.keys()):
    domain_topics = sorted([t['id'] for t in hier_data['topics'] if t['domain'] == domain_id])
    for topic_id in domain_topics:
        topic_points = [p for p in hier_data['points'] if p['topic'] == topic_id]
        term_counter = get_top_terms(topic_points)
        label = create_smart_label(term_counter, domain_info[domain_id]['category'], max_terms=3)
        topic_labels[topic_id] = label

for domain in hier_data['domains']:
    domain_id = domain['id']
    domain['label'] = domain_info[domain_id]['category']
    domain['category'] = domain_info[domain_id]['category']

for topic in hier_data['topics']:
    topic['label'] = topic_labels[topic['id']]

with open('viz_data_hierarchical_improved.json', 'w') as f:
    json.dump(hier_data, f)

print("✅ Labels applied")
print(f"Domains: {len(set(d['label'] for d in hier_data['domains']))}")
print(f"Topics: {len(hier_data['topics'])}")

