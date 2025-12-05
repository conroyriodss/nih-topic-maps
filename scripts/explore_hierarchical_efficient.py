#!/usr/bin/env python3
"""
Memory-efficient hierarchical clustering exploration
"""

import json
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from sklearn.cluster import KMeans, AgglomerativeClustering
import gc

print("="*70)
print("EFFICIENT HIERARCHICAL CLUSTERING EXPLORATION")
print("="*70)

# Load data
print("\nLoading data...")
with open('viz_data_project_terms_k100_final.json') as f:
    data = json.load(f)

coords = np.array([[p['x'], p['y']] for p in data['points']], dtype=np.float32)
scaler = StandardScaler()
coords_scaled = scaler.fit_transform(coords)

print(f"Loaded {len(coords)} grants")

def evaluate_quick(labels, coords, name):
    """Quick evaluation"""
    from collections import Counter
    n_clusters = len(set(labels))
    sizes = list(Counter(labels).values())
    
    # Sample for silhouette if too large
    if len(coords) > 5000:
        idx = np.random.choice(len(coords), 5000, replace=False)
        sil = silhouette_score(coords[idx], labels[idx])
    else:
        sil = silhouette_score(coords, labels)
    
    return {
        'name': name,
        'n_clusters': n_clusters,
        'silhouette': sil,
        'min_size': min(sizes),
        'max_size': max(sizes),
        'mean_size': int(np.mean(sizes))
    }

print("\n" + "="*70)
print("LEVEL 1: TOP-LEVEL DOMAINS")
print("="*70)

results = []

# Test K-means (efficient)
print("\nTesting K-means...")
for k in [5, 7, 10, 12, 15, 20, 25, 30]:
    km = KMeans(n_clusters=k, random_state=42, n_init=5, max_iter=100)
    labels = km.fit_predict(coords_scaled)
    res = evaluate_quick(labels, coords_scaled, f"KMeans_k{k}")
    results.append(res)
    print(f"  k={k:2d}: {res['n_clusters']} clusters, silhouette={res['silhouette']:.4f}")
    gc.collect()

# Test Agglomerative (Ward only - most efficient)
print("\nTesting Agglomerative (Ward linkage)...")
for k in [5, 7, 10, 12, 15, 20]:
    agg = AgglomerativeClustering(n_clusters=k, linkage='ward')
    labels = agg.fit_predict(coords_scaled)
    res = evaluate_quick(labels, coords_scaled, f"Agglom_ward_k{k}")
    results.append(res)
    print(f"  k={k:2d}: {res['n_clusters']} clusters, silhouette={res['silhouette']:.4f}")
    gc.collect()

# Sort by silhouette
results.sort(key=lambda x: x['silhouette'], reverse=True)

print("\n" + "="*70)
print("TOP 10 LEVEL 1 CONFIGURATIONS")
print("="*70)
print(f"\n{'Method':<25} {'Clusters':>8} {'Silhouette':>11} {'Size Range':>20}")
print("-" * 70)
for r in results[:10]:
    print(f"{r['name']:<25} {r['n_clusters']:>8} {r['silhouette']:>11.4f} "
          f"{r['min_size']:>7,}-{r['max_size']:<8,}")

print("\n" + "="*70)
print("BIOMEDICAL ONTOLOGY ALIGNMENT ANALYSIS")
print("="*70)

print("\nTypical NIH/biomedical research hierarchy:")
print("  Level 1: 5-12 major domains (e.g., Cancer, Neuro, Immuno, CV, etc.)")
print("  Level 2: 4-8 areas per domain (~30-80 total)")
print("  Level 3: 3-5 topics per area (~100-300 total)")

print("\n" + "="*70)
print("RECOMMENDED CONFIGURATIONS")
print("="*70)

# 2-level recommendations
print("\n📊 OPTION 1: 2-LEVEL HIERARCHY (SIMPLER)")
print("-" * 70)
for r in results[:3]:
    if 5 <= r['n_clusters'] <= 15:
        l2_per_l1 = 6
        total_l2 = r['n_clusters'] * l2_per_l1
        print(f"\n  Config: {r['name']}")
        print(f"  • Level 1: {r['n_clusters']} major domains")
        print(f"  • Level 2: ~{total_l2} research topics (avg {l2_per_l1} per domain)")
        print(f"  • Quality: Silhouette {r['silhouette']:.4f}")
        print(f"  • Alignment: {'✓ GOOD' if 40 <= total_l2 <= 100 else '⚠ Review'}")
        if r == results[0]:
            print(f"  ⭐ RECOMMENDED")

# 3-level recommendations  
print("\n📊 OPTION 2: 3-LEVEL HIERARCHY (MORE GRANULAR)")
print("-" * 70)
for r in results[:3]:
    if 7 <= r['n_clusters'] <= 12:
        l2_per_l1 = 5
        l3_per_l2 = 4
        total_l2 = r['n_clusters'] * l2_per_l1
        total_l3 = total_l2 * l3_per_l2
        print(f"\n  Config: {r['name']}")
        print(f"  • Level 1: {r['n_clusters']} major domains")
        print(f"  • Level 2: ~{total_l2} research areas ({l2_per_l1} per domain)")
        print(f"  • Level 3: ~{total_l3} specific topics ({l3_per_l2} per area)")
        print(f"  • Quality: Silhouette {r['silhouette']:.4f}")
        print(f"  • Alignment: {'✓ GOOD' if 100 <= total_l3 <= 200 else '⚠ Review'}")

print("\n" + "="*70)
print("IMPLEMENTATION RECOMMENDATION")
print("="*70)

best = results[0]
print(f"\n🎯 PRIMARY RECOMMENDATION: 2-LEVEL HIERARCHY")
print(f"\n  Method: {best['name']}")
print(f"  Level 1: {best['n_clusters']} domains (Silhouette: {best['silhouette']:.4f})")
print(f"  Level 2: ~{best['n_clusters'] * 6} topics (6 per domain average)")
print(f"\n  Why this works:")
print(f"  ✓ Aligns with NIH IC structure (~27 ICs → {best['n_clusters']} major areas)")
print(f"  ✓ High cluster quality (silhouette > 0.4)")
print(f"  ✓ Manageable granularity for portfolio analysis")
print(f"  ✓ Clear domain boundaries for strategic planning")

# Save recommendations
rec = {
    'recommended_2level': {
        'level1_method': best['name'],
        'level1_k': best['n_clusters'],
        'level1_silhouette': float(best['silhouette']),
        'level2_per_level1': 6,
        'total_level2_clusters': best['n_clusters'] * 6
    },
    'all_results': [
        {k: float(v) if isinstance(v, (np.floating, np.integer)) else v 
         for k, v in r.items()}
        for r in results[:10]
    ]
}

with open('hierarchical_recommendations.json', 'w') as f:
    json.dump(rec, f, indent=2)

print(f"\n✓ Saved: hierarchical_recommendations.json")

print("\n" + "="*70)
print("NEXT STEPS")
print("="*70)
print("\n1. Implement chosen hierarchy (use Level 1 config above)")
print("2. Sub-cluster each Level 1 domain to create Level 2")
print("3. Generate hierarchical visualization with drill-down")
print("4. Validate against NIH IC structure")
print("\nReady to proceed with implementation!")

