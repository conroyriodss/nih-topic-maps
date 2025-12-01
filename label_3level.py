#!/usr/bin/env python3
import json
from collections import Counter

print("Loading data...")
with open('viz_data_project_terms_k100_final.json') as f:
    orig_data = json.load(f)
with open('viz_data_3level_hierarchy.json') as f:
    hier_data = json.load(f)

# Build term index
id_to_cluster = {p['application_id']: p['cluster'] for p in orig_data['points']}
cluster_terms = {}
for c in orig_data['clusters']:
    cluster_terms[c['id']] = [t.strip() for t in c['label'].split(';') if t.strip()]

def get_top_terms(point_list):
    term_counter = Counter()
    for p in point_list:
        cid = id_to_cluster.get(p['application_id'])
        if cid in cluster_terms:
            term_counter.update(cluster_terms[cid][:5])
    return term_counter

# Generic terms to filter
GENERIC = {'cell','cells','protein','proteins','gene','genes','expression','function',
           'regulation','activity','level','development','role','mechanism','process',
           'system','study','studies','research','analysis','method','data','model',
           'disease','human','patient','clinical','work','testing','base','goals','test'}

def create_label(term_counter, fallback="Research"):
    if not term_counter:
        return fallback
    # Get specific terms
    specific = [(t,c) for t,c in term_counter.most_common(15) if t.lower() not in GENERIC]
    if specific:
        top = [t for t,_ in specific[:2]]
    else:
        top = [t for t,_ in term_counter.most_common(2)]
    if not top:
        return fallback
    result = " / ".join(top)
    return result.replace(' / /','/').title()[:50]

def categorize_domain(terms):
    s = "; ".join([t for t,_ in terms.most_common(10)]).lower()
    if any(x in s for x in ['xenograft','wound','obesity','in vivo']):
        return "In Vivo & Translational"
    elif any(x in s for x in ['laboratory mouse','gene expression','protein structure']):
        return "Molecular & Cell Biology"
    elif any(x in s for x in ['program','faculty','university','training']):
        return "Research Infrastructure"
    elif any(x in s for x in ['imaging','tomography','x-ray']):
        return "Biomedical Imaging"
    elif any(x in s for x in ['intervention','adolescent','behavioral']):
        return "Clinical & Behavioral"
    else:
        return "Cellular Mechanisms"

n_total = len(hier_data['points'])

# Label domains
print("\n" + "="*80)
print("LABELING DOMAINS")
print("="*80)
for domain in hier_data['domains']:
    pts = [p for p in hier_data['points'] if p['domain'] == domain['id']]
    terms = get_top_terms(pts)
    domain['label'] = categorize_domain(terms)
    domain['category'] = domain['label']
    print(f"Domain {domain['id']}: {domain['label']} ({domain['size']:,})")

# Label topics
print("\n" + "="*80)
print("LABELING TOPICS")
print("="*80)
for topic in hier_data['topics']:
    pts = [p for p in hier_data['points'] if p['topic'] == topic['id']]
    terms = get_top_terms(pts)
    parent_domain = next(d for d in hier_data['domains'] if d['id'] == topic['domain'])
    topic['label'] = create_label(terms, parent_domain['label'])
    print(f"  Topic {topic['id']}: {topic['label']} ({topic['size']:,})")

# Label subtopics
print("\n" + "="*80)
print("LABELING SUBTOPICS")
print("="*80)
for subtopic in hier_data['subtopics']:
    pts = [p for p in hier_data['points'] if p['subtopic'] == subtopic['id']]
    terms = get_top_terms(pts)
    parent_topic = next(t for t in hier_data['topics'] if t['id'] == subtopic['topic'])
    subtopic['label'] = create_label(terms, parent_topic['label'])
    pct = 100*subtopic['size']/n_total
    print(f"    Subtopic {subtopic['id']}: {subtopic['label']} ({subtopic['size']:,}, {pct:.1f}%)")

# Save
with open('viz_data_3level_hierarchy.json', 'w') as f:
    json.dump(hier_data, f)

print("\n" + "="*80)
print("✅ LABELED 3-LEVEL HIERARCHY")
print("="*80)
print(f"Domains: {len(hier_data['domains'])}")
print(f"Topics: {len(hier_data['topics'])}")
print(f"Subtopics: {len(hier_data['subtopics'])}")

# Print final tree
print("\n" + "="*80)
print("FINAL LABELED HIERARCHY")
print("="*80)
for domain in sorted(hier_data['domains'], key=lambda x: x['id']):
    print(f"\n📊 {domain['label']} ({domain['size']:,})")
    for topic in sorted([t for t in hier_data['topics'] if t['domain']==domain['id']], key=lambda x: x['id']):
        print(f"   └─ {topic['label']} ({topic['size']:,})")
        for subtopic in sorted([s for s in hier_data['subtopics'] if s['topic']==topic['id']], key=lambda x: x['id']):
            print(f"       └─ {subtopic['label']} ({subtopic['size']:,})")

