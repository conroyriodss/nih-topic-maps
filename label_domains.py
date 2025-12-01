#!/usr/bin/env python3
import json
from collections import Counter

print("Loading hierarchical data...")
with open('viz_data_hierarchical_5_30.json') as f:
    data = json.load(f)

# Load original data with PROJECT_TERMS
print("Loading original data with terms...")
with open('viz_data_project_terms_k100_final.json') as f:
    original = json.load(f)

# Create mapping from application_id to terms
id_to_terms = {}
for p in original['points']:
    # Extract terms from cluster label or use placeholder
    id_to_terms[p['application_id']] = p.get('terms', [])

print("\nAnalyzing top terms per domain...")
print("="*70)

domain_labels = {}
for domain_id in range(5):
    domain_points = [p for p in data['points'] if p['domain'] == domain_id]
    
    # Collect all terms for this domain
    all_terms = []
    for p in domain_points[:1000]:  # Sample first 1000 for speed
        terms = id_to_terms.get(p['application_id'], [])
        if isinstance(terms, str):
            all_terms.extend(terms.split(';'))
        elif isinstance(terms, list):
            all_terms.extend(terms)
    
    # Count term frequency
    term_counts = Counter(all_terms)
    top_terms = [term.strip() for term, _ in term_counts.most_common(8) if term.strip()]
    
    # Create domain label
    domain_label = '; '.join(top_terms[:5])
    domain_labels[domain_id] = domain_label
    
    print(f"\nDomain {domain_id} ({len(domain_points):,} grants)")
    print(f"  Label: {domain_label}")
    print(f"  Top 8 terms:")
    for term, count in term_counts.most_common(8):
        if term.strip():
            print(f"    {term.strip()}: {count}")

# Update visualization data with labels
for domain in data['domains']:
    domain['label'] = domain_labels.get(domain['id'], f"Domain {domain['id']}")

# Save updated data
with open('viz_data_hierarchical_5_30_labeled.json', 'w') as f:
    json.dump(data, f)

print("\n" + "="*70)
print("Domain labels created and saved to:")
print("  viz_data_hierarchical_5_30_labeled.json")

