#!/usr/bin/env python3
"""
Identify best and worst topic clusters for manual review
"""
import json
import pandas as pd
from collections import defaultdict, Counter

print("Loading viz data...")
with open('viz_data_full.json') as f:
    data = json.load(f)

# Analyze each topic
topics = defaultdict(lambda: {
    'grants': [],
    'ics': Counter(),
    'years': Counter(),
    'funding': []
})

for grant in data:
    topic = grant['topic']
    topics[topic]['grants'].append(grant)
    topics[topic]['ics'][grant['ic']] += 1
    topics[topic]['years'][grant['year']] += 1
    if grant['funding']:
        topics[topic]['funding'].append(grant['funding'])

# Score topics
scored_topics = []
for topic_id, info in topics.items():
    n_grants = len(info['grants'])
    n_ics = len(info['ics'])
    ic_entropy = -sum((c/n_grants) * (c/n_grants) for c in info['ics'].values())
    
    # Calculate metrics
    avg_funding = sum(info['funding']) / len(info['funding']) if info['funding'] else 0
    year_span = max(info['years'].keys()) - min(info['years'].keys()) if info['years'] else 0
    
    # Quality score (lower is better)
    # Penalize: small size, high IC diversity, extreme funding variance
    quality_score = 0
    if n_grants < 100:
        quality_score += 100
    if n_ics > 25:
        quality_score += n_ics
    if n_grants == 1:
        quality_score += 1000
        
    sample_grant = info['grants'][0]
    
    scored_topics.append({
        'topic': topic_id,
        'label': sample_grant['topic_label'],
        'n_grants': n_grants,
        'n_ics': n_ics,
        'ic_entropy': ic_entropy,
        'year_span': year_span,
        'avg_funding': avg_funding,
        'quality_score': quality_score,
        'top_3_ics': ', '.join([ic for ic, _ in info['ics'].most_common(3)])
    })

# Sort by quality (worst first)
scored_topics.sort(key=lambda x: x['quality_score'], reverse=True)

print("\n=== 10 WORST Quality Topics ===")
print(f"{'Topic':<6} {'Grants':<7} {'ICs':<4} {'Label':<30} {'Top ICs'}")
print("-" * 90)
for t in scored_topics[:10]:
    print(f"{t['topic']:<6} {t['n_grants']:<7} {t['n_ics']:<4} {t['label']:<30} {t['top_3_ics']}")

print("\n=== 10 BEST Quality Topics ===")
scored_topics.sort(key=lambda x: x['quality_score'])
print(f"{'Topic':<6} {'Grants':<7} {'ICs':<4} {'Label':<30} {'Top ICs'}")
print("-" * 90)
for t in scored_topics[:10]:
    print(f"{t['topic']:<6} {t['n_grants']:<7} {t['n_ics']:<4} {t['label']:<30} {t['top_3_ics']}")

# Save full report
df = pd.DataFrame(scored_topics)
df.to_csv('topic_quality_report.csv', index=False)
print("\n✓ Full report saved to topic_quality_report.csv")
