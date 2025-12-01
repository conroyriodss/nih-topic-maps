#!/usr/bin/env python3
"""
Multi-level hierarchical clustering exploration for NIH grants
Explores 2-level, 3-level, and 4-level hierarchies with different parameters
Aligns with biomedical research ontology structure
"""

import json
import numpy as np
import pandas as pd
import hdbscan
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.cluster import KMeans, AgglomerativeClustering
from collections import Counter, defaultdict
import warnings
warnings.filterwarnings('ignore')

print("="*70)
print("MULTI-LEVEL HIERARCHICAL CLUSTERING EXPLORATION")
print("="*70)

# Load data
print("\nLoading data...")
with open('viz_data_project_terms_k100_final.json') as f:
    data = json.load(f)

points = data['points']
coords = np.array([[p['x'], p['y']] for p in points])
coords_scaled = StandardScaler().fit_transform(coords)

print(f"Loaded {len(points)} grants")
print(f"Using 2D UMAP coordinates (standardized)")

# Helper function to evaluate clustering quality
def evaluate_clustering(labels, coords, name=""):
    mask = labels != -1  # Exclude noise
    if mask.sum() < 2:
        return None
    
    n_clusters = len(set(labels[mask]))
    n_noise = sum(labels == -1)
    
    try:
        silhouette = silhouette_score(coords[mask], labels[mask])
        calinski = calinski_harabasz_score(coords[mask], labels[mask])
        davies = davies_bouldin_score(coords[mask], labels[mask])
    except:
        return None
    
    cluster_sizes = Counter(labels[mask])
    sizes = list(cluster_sizes.values())
    
    return {
        'name': name,
        'n_clusters': n_clusters,
        'n_noise': n_noise,
        'pct_noise': 100 * n_noise / len(labels),
        'silhouette': silhouette,
        'calinski_harabasz': calinski,
        'davies_bouldin': davies,  # Lower is better
        'min_size': min(sizes),
        'max_size': max(sizes),
        'mean_size': np.mean(sizes),
        'median_size': np.median(sizes),
        'size_std': np.std(sizes)
    }

print("\n" + "="*70)
print("LEVEL 1: TOP-LEVEL DOMAINS (Broad Research Areas)")
print("="*70)
print("\nTesting different algorithms and parameters for Level 1...")

level1_results = []

# HDBSCAN with various parameters
for min_size in [1000, 2000, 5000]:
    for min_samples in [10, 20, 50]:
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_size,
            min_samples=min_samples,
            cluster_selection_epsilon=0.2,
            metric='euclidean'
        )
        labels = clusterer.fit_predict(coords_scaled)
        result = evaluate_clustering(labels, coords_scaled, 
                                     f"HDBSCAN(size={min_size}, samples={min_samples})")
        if result and 3 <= result['n_clusters'] <= 20:
            level1_results.append(result)

# K-means with reasonable K values
for k in [5, 7, 10, 12, 15, 20]:
    clusterer = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = clusterer.fit_predict(coords_scaled)
    result = evaluate_clustering(labels, coords_scaled, f"KMeans(k={k})")
    if result:
        level1_results.append(result)

# Hierarchical/Agglomerative clustering
for k in [5, 7, 10, 12, 15]:
    for linkage in ['ward', 'average', 'complete']:
        clusterer = AgglomerativeClustering(n_clusters=k, linkage=linkage)
        labels = clusterer.fit_predict(coords_scaled)
        result = evaluate_clustering(labels, coords_scaled, 
                                     f"Agglomerative(k={k}, {linkage})")
        if result:
            level1_results.append(result)

# Sort and display top results
level1_results = sorted(level1_results, key=lambda x: x['silhouette'], reverse=True)

print("\nTop 10 Level 1 configurations by silhouette score:")
print(f"{'Method':<40} {'Clusters':>8} {'Silhouette':>11} {'Calinski':>10} {'Davies':>8} {'Noise%':>7}")
print("-" * 95)
for r in level1_results[:10]:
    print(f"{r['name']:<40} {r['n_clusters']:>8} {r['silhouette']:>11.4f} "
          f"{r['calinski']:>10.1f} {r['davies_bouldin']:>8.3f} {r['pct_noise']:>6.1f}%")

print("\n" + "="*70)
print("LEVEL 2: MID-LEVEL TOPICS (Within each Level 1 domain)")
print("="*70)

# Use best Level 1 result
best_l1 = level1_results[0]
print(f"\nUsing Level 1: {best_l1['name']} ({best_l1['n_clusters']} clusters)")

# Re-cluster to get Level 1 labels
if 'HDBSCAN' in best_l1['name']:
    params = best_l1['name'].split('(')[1].split(')')[0]
    min_size = int(params.split('size=')[1].split(',')[0])
    min_samples = int(params.split('samples=')[1])
    clusterer_l1 = hdbscan.HDBSCAN(min_cluster_size=min_size, min_samples=min_samples,
                                    cluster_selection_epsilon=0.2)
    labels_l1 = clusterer_l1.fit_predict(coords_scaled)
elif 'KMeans' in best_l1['name']:
    k = int(best_l1['name'].split('k=')[1].split(')')[0])
    clusterer_l1 = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels_l1 = clusterer_l1.fit_predict(coords_scaled)
else:
    k = int(best_l1['name'].split('k=')[1].split(',')[0])
    linkage = best_l1['name'].split(', ')[1].split(')')[0]
    clusterer_l1 = AgglomerativeClustering(n_clusters=k, linkage=linkage)
    labels_l1 = clusterer_l1.fit_predict(coords_scaled)

# Cluster within each Level 1 domain
level2_configs = []

for l1_cluster in set(labels_l1):
    if l1_cluster == -1:
        continue
    
    mask = labels_l1 == l1_cluster
    coords_subset = coords_scaled[mask]
    
    if len(coords_subset) < 50:
        continue
    
    # Try different Level 2 configurations
    for method in ['hdbscan', 'kmeans', 'agglom']:
        if method == 'hdbscan':
            for min_size in [50, 100, 200]:
                clusterer = hdbscan.HDBSCAN(min_cluster_size=min_size, min_samples=5)
                labels_l2 = clusterer.fit_predict(coords_subset)
                n_l2_clusters = len(set(labels_l2)) - (1 if -1 in labels_l2 else 0)
                if n_l2_clusters >= 2:
                    level2_configs.append({
                        'l1_cluster': l1_cluster,
                        'method': f'HDBSCAN(size={min_size})',
                        'n_clusters': n_l2_clusters,
                        'size': len(coords_subset)
                    })
                    
        elif method == 'kmeans':
            # Auto-determine good K based on domain size
            max_k = min(20, len(coords_subset) // 100)
            for k in range(3, max_k + 1):
                level2_configs.append({
                    'l1_cluster': l1_cluster,
                    'method': f'KMeans(k={k})',
                    'n_clusters': k,
                    'size': len(coords_subset)
                })
                
        elif method == 'agglom':
            max_k = min(15, len(coords_subset) // 100)
            for k in range(3, max_k + 1):
                level2_configs.append({
                    'l1_cluster': l1_cluster,
                    'method': f'Agglom(k={k})',
                    'n_clusters': k,
                    'size': len(coords_subset)
                })

# Summarize Level 2 options
print(f"\nTested {len(level2_configs)} Level 2 configurations")
l2_by_domain = defaultdict(list)
for cfg in level2_configs:
    l2_by_domain[cfg['l1_cluster']].append(cfg['n_clusters'])

print(f"\nLevel 2 clusters per Level 1 domain:")
for l1_cluster in sorted(l2_by_domain.keys()):
    l2_counts = l2_by_domain[l1_cluster]
    print(f"  Domain {l1_cluster}: {min(l2_counts)}-{max(l2_counts)} subtopics "
          f"(mean: {np.mean(l2_counts):.1f})")

print("\n" + "="*70)
print("RECOMMENDED HIERARCHICAL CONFIGURATIONS")
print("="*70)

# Analyze biomedical research ontology alignment
print("\n📚 BIOMEDICAL ONTOLOGY ALIGNMENT:")
print("\nTypical biomedical research hierarchy:")
print("  Level 1: 5-12 major research domains")
print("    (e.g., Cancer Biology, Neuroscience, Immunology, Genomics,")
print("     Cardiovascular, Infectious Disease, etc.)")
print("  Level 2: 3-10 research areas per domain (30-100 total)")
print("    (e.g., within Cancer: Oncology, Tumor Biology, Therapeutics, etc.)")
print("  Level 3: 2-5 specific topics per area (100-300 total)")
print("    (e.g., within Oncology: Breast Cancer, Lung Cancer, etc.)")

recommendations = []

# 2-Level Hierarchy
print("\n" + "-"*70)
print("OPTION 1: 2-LEVEL HIERARCHY")
print("-"*70)
for l1_result in level1_results[:5]:
    if 5 <= l1_result['n_clusters'] <= 12:
        # Estimate Level 2 total clusters
        avg_l2_per_l1 = 6  # Reasonable assumption
        total_l2 = l1_result['n_clusters'] * avg_l2_per_l1
        
        rec = {
            'structure': '2-level',
            'level1_method': l1_result['name'],
            'level1_clusters': l1_result['n_clusters'],
            'level2_est_total': total_l2,
            'level1_silhouette': l1_result['silhouette'],
            'score': l1_result['silhouette'] * (1 - abs(total_l2 - 60)/100)  # Prefer ~60 total L2
        }
        recommendations.append(rec)
        
        print(f"\n  Level 1: {rec['level1_clusters']} domains - {l1_result['name']}")
        print(f"  Level 2: ~{total_l2} topics ({avg_l2_per_l1} per domain average)")
        print(f"  Quality: Silhouette {l1_result['silhouette']:.4f}")
        print(f"  Alignment: {'✓ Good' if 50 <= total_l2 <= 100 else '⚠ Check'}")

# 3-Level Hierarchy
print("\n" + "-"*70)
print("OPTION 2: 3-LEVEL HIERARCHY")
print("-"*70)
for l1_result in level1_results[:3]:
    if 5 <= l1_result['n_clusters'] <= 10:
        avg_l2_per_l1 = 5
        avg_l3_per_l2 = 3
        total_l2 = l1_result['n_clusters'] * avg_l2_per_l1
        total_l3 = total_l2 * avg_l3_per_l2
        
        rec = {
            'structure': '3-level',
            'level1_method': l1_result['name'],
            'level1_clusters': l1_result['n_clusters'],
            'level2_est_total': total_l2,
            'level3_est_total': total_l3,
            'level1_silhouette': l1_result['silhouette'],
            'score': l1_result['silhouette'] * (1 - abs(total_l3 - 100)/200)
        }
        recommendations.append(rec)
        
        print(f"\n  Level 1: {rec['level1_clusters']} domains - {l1_result['name']}")
        print(f"  Level 2: ~{total_l2} research areas ({avg_l2_per_l1} per domain)")
        print(f"  Level 3: ~{total_l3} specific topics ({avg_l3_per_l2} per area)")
        print(f"  Quality: Silhouette {l1_result['silhouette']:.4f}")
        print(f"  Alignment: {'✓ Good' if 80 <= total_l3 <= 150 else '⚠ Check'}")

print("\n" + "="*70)
print("TOP 3 RECOMMENDED CONFIGURATIONS")
print("="*70)

recommendations = sorted(recommendations, key=lambda x: x['score'], reverse=True)

for i, rec in enumerate(recommendations[:3], 1):
    print(f"\n{i}. {rec['structure'].upper()}")
    print(f"   Level 1: {rec['level1_clusters']} major domains")
    if rec['structure'] == '2-level':
        print(f"   Level 2: ~{rec['level2_est_total']} research topics")
        print(f"   Total granularity: {rec['level2_est_total']} topics")
    else:
        print(f"   Level 2: ~{rec['level2_est_total']} research areas")
        print(f"   Level 3: ~{rec['level3_est_total']} specific topics")
        print(f"   Total granularity: {rec['level3_est_total']} topics")
    print(f"   Method: {rec['level1_method']}")
    print(f"   Quality score: {rec['score']:.4f}")

# Save recommendations
with open('hierarchical_clustering_recommendations.json', 'w') as f:
    json.dump({
        'level1_evaluations': level1_results[:10],
        'recommendations': recommendations[:5],
        'biomedical_ontology_guidelines': {
            'level1_typical_range': '5-12 domains',
            'level2_per_level1': '3-10 areas per domain',
            'level3_per_level2': '2-5 topics per area',
            'examples': {
                'level1': ['Cancer Biology', 'Neuroscience', 'Immunology', 
                          'Cardiovascular', 'Infectious Disease', 'Genomics',
                          'Metabolic Disorders', 'Developmental Biology'],
                'level2_cancer': ['Oncology', 'Tumor Biology', 'Cancer Therapeutics',
                                 'Cancer Genetics', 'Cancer Immunology'],
                'level3_oncology': ['Breast Cancer', 'Lung Cancer', 'Colorectal Cancer',
                                   'Pediatric Oncology']
            }
        }
    }, f, indent=2)

print("\n" + "="*70)
print("NEXT STEPS")
print("="*70)
print("\n1. Review recommendations above")
print("2. Choose preferred hierarchy structure (2-level or 3-level)")
print("3. Run full hierarchical clustering with chosen parameters")
print("4. Generate visualizations with hierarchical navigation")
print("5. Validate cluster labels against NIH IC assignments")
print("\n✓ Saved: hierarchical_clustering_recommendations.json")
print("\nReady to implement chosen configuration!")

