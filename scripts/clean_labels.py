#!/usr/bin/env python3
import json

print("Loading data...")
with open('viz_data_hierarchical_5_dbscan_final.json') as f:
    data = json.load(f)

# Cleaner domain labels
domain_names = {
    0: "Molecular & Cell Biology",
    1: "Research Infrastructure", 
    2: "Cellular Mechanisms",
    3: "In Vivo & Translational",
    4: "Biomedical Research"
}

# Clean topic labels - take first meaningful phrase only
def clean_topic_label(label, domain_name):
    # Split on "And" and take first 2-3 meaningful parts
    parts = label.split(' And ')
    clean_parts = []
    for p in parts[:3]:
        p = p.strip().title()
        # Skip generic words
        if p.lower() not in ['role', 'testing', 'cells', 'base', 'work', 'goals', 'human', 'research']:
            clean_parts.append(p)
    
    if clean_parts:
        return ' / '.join(clean_parts[:2])
    else:
        return domain_name  # Fallback

# Update domains
for domain in data['domains']:
    domain['label'] = domain_names.get(domain['id'], f"Domain {domain['id']}")

# Update topics with cleaner labels
for topic in data['topics']:
    domain_name = domain_names.get(topic['domain'], "Research")
    old_label = topic['label']
    topic['label'] = clean_topic_label(old_label, domain_name)

# Print summary
print("\nCleaned labels:")
for domain in sorted(data['domains'], key=lambda x: x['id']):
    print(f"\n📊 {domain['label']} ({domain['size']:,} grants)")
    domain_topics = [t for t in data['topics'] if t['domain'] == domain['id']]
    for topic in sorted(domain_topics, key=lambda x: x['id']):
        print(f"   Topic {topic['id']}: {topic['label']} ({topic['size']:,})")

# Save
with open('viz_data_hierarchical_5_dbscan_final.json', 'w') as f:
    json.dump(data, f)

print("\n✅ Labels cleaned and saved")

