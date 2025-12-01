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

def get_top_terms_detailed(point_list, n=20):
    """Get top terms with full context"""
    term_counter = Counter()
    for p in point_list:
        cid = id_to_cluster.get(p['application_id'])
        if cid in cluster_terms:
            term_counter.update(cluster_terms[cid][:8])
    return term_counter.most_common(n)

def find_distinguishing_terms(subtopic_terms, sibling_subtopics_terms):
    """Find terms unique to this subtopic vs siblings"""
    st_set = set([t for t,_ in subtopic_terms[:10]])
    
    # Terms that appear in siblings
    sibling_terms = set()
    for sib_terms in sibling_subtopics_terms:
        sibling_terms.update([t for t,_ in sib_terms[:10]])
    
    # Unique terms
    unique = st_set - sibling_terms
    if unique:
        return list(unique)[:2]
    
    # If no unique terms, take the most common
    return [subtopic_terms[0][0]] if subtopic_terms else []

# Create distinctive labels
print("\n" + "="*80)
print("CREATING DISTINCTIVE SUBTOPIC LABELS")
print("="*80)

label_map = {}

for topic in hier_data['topics']:
    topic_id = topic['id']
    subtopics = [s for s in hier_data['subtopics'] if s['topic'] == topic_id]
    
    print(f"\n📌 Topic {topic_id}: {topic['label']} ({len(subtopics)} subtopics)")
    
    # Get all subtopic term info
    subtopic_info = []
    for subtopic in subtopics:
        pts = [p for p in hier_data['points'] if p['subtopic'] == subtopic['id']]
        top_terms = get_top_terms_detailed(pts, 15)
        subtopic_info.append({
            'id': subtopic['id'],
            'size': len(pts),
            'terms': top_terms,
            'subtopic_obj': subtopic
        })
    
    # Find distinguishing terms for each
    for i, info in enumerate(subtopic_info):
        siblings_terms = [other['terms'] for j, other in enumerate(subtopic_info) if j != i]
        distinctive = find_distinguishing_terms(info['terms'], siblings_terms)
        
        # Create label based on distinctive terms or size ranking
        if distinctive:
            label = " & ".join(distinctive[:2])
        else:
            # Fallback: use size-based description
            if info['size'] > 2000:
                label = "Major Focus"
            elif info['size'] > 1500:
                label = "Primary Research"
            elif info['size'] > 1000:
                label = "Key Area"
            else:
                label = "Specialized"
        
        info['subtopic_obj']['label'] = label.title()
        print(f"   Subtopic {info['id']}: {label.title()} ({info['size']:,})")
        
        # Show top distinctive terms
        print(f"      Terms: {[t for t,_ in info['terms'][:5]]}")

# Save updated hierarchy
with open('viz_data_3level_hierarchy.json', 'w') as f:
    json.dump(hier_data, f)

print("\n" + "="*80)
print("✅ DISTINCTIVE LABELS CREATED")
print("="*80)

# Show final result
print("\nFINAL HIERARCHY WITH DISTINCTIVE LABELS:")
for domain in sorted(hier_data['domains'], key=lambda x: x['id']):
    print(f"\n📊 {domain['label']}")
    for topic in sorted([t for t in hier_data['topics'] if t['domain']==domain['id']], key=lambda x: x['id']):
        print(f"   └─ {topic['label']}")
        for subtopic in sorted([s for s in hier_data['subtopics'] if s['topic']==topic['id']], key=lambda x: x['id']):
            print(f"       └─ {subtopic['label']} ({subtopic['size']:,})")

