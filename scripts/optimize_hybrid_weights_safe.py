#!/usr/bin/env python3
"""
OPTION D: Hybrid Weight Optimization - Memory Safe Version
Uses smaller sample and incremental processing to prevent crashes
"""
import pandas as pd
import numpy as np
from sklearn.cluster import MiniBatchKMeans, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
import json
import matplotlib.pyplot as plt
import sys
import os
import gc

print("=" * 70)
print("OPTION D: HYBRID WEIGHT OPTIMIZATION (SAFE MODE)")
print("=" * 70)

# Find files
sample_files = ['grants_100k_stratified.parquet', 'grants_50k_stratified.parquet']
sample_file = next((f for f in sample_files if os.path.exists(f)), None)

embedding_files = ['embeddings_100k_pubmedbert.parquet', 'embeddings_50k_pubmedbert.parquet']
embedding_file = next((f for f in embedding_files if os.path.exists(f)), None)

if not sample_file or not embedding_file:
    print("\n✗ Missing required files")
    sys.exit(1)

print(f"\nSample: {sample_file}")
print(f"Embeddings: {embedding_file}")

# Load with memory optimization
print("\n[1/6] Loading data (memory-optimized)...")
df_sample = pd.read_parquet(sample_file)
df_embeddings = pd.read_parquet(embedding_file)

# Use smaller sample to prevent crashes
MAX_SAMPLE = 20000  # Safe limit for clustering
if len(df_sample) > MAX_SAMPLE:
    print(f"  Original size: {len(df_sample):,}")
    print(f"  Sampling {MAX_SAMPLE:,} for optimization (prevents crashes)")
    df_sample = df_sample.sample(n=MAX_SAMPLE, random_state=42)

df = df_sample.merge(df_embeddings, on='APPLICATION_ID', how='inner')
print(f"  Working with: {len(df):,} grants")

# Free memory
del df_sample, df_embeddings
gc.collect()

# Extract features
print("\n[2/6] Extracting features...")
if isinstance(df['embedding'].iloc[0], str):
    embeddings = np.vstack(df['embedding'].apply(eval).values)
else:
    embeddings = np.vstack(df['embedding'].values)

embeddings = StandardScaler().fit_transform(embeddings)
print(f"  Embeddings: {embeddings.shape}")

# RCDC features
if 'NIH_SPENDING_CATS' in df.columns:
    rcdc_lists = df['NIH_SPENDING_CATS'].fillna('').str.split('|')
    all_cats = sorted(set([c for cats in rcdc_lists for c in cats if c]))[:100]  # Limit categories
    
    rcdc_matrix = np.zeros((len(df), len(all_cats)))
    for i, cats in enumerate(rcdc_lists):
        for cat in cats:
            if cat in all_cats:
                rcdc_matrix[i, all_cats.index(cat)] = 1
    
    rcdc_matrix = StandardScaler().fit_transform(rcdc_matrix)
    print(f"  RCDC: {rcdc_matrix.shape} (top 100 categories)")
else:
    rcdc_matrix = np.zeros((len(df), 1))
    print("  RCDC: Not available")

# IC features
if 'IC_NAME' in df.columns:
    ic_encoder = OneHotEncoder(sparse_output=False)
    ic_matrix = ic_encoder.fit_transform(df[['IC_NAME']])
    ic_matrix = StandardScaler().fit_transform(ic_matrix)
    print(f"  IC: {ic_matrix.shape}")
else:
    ic_matrix = np.zeros((len(df), 1))
    print("  IC: Not available")

# Simplified weight grid (fewer tests to prevent crashes)
print("\n[3/6] Defining weights...")
embedding_weights = [0.6, 0.7, 0.8, 0.9, 1.0]  # Reduced
rcdc_weights = [0.0, 0.1, 0.2]  # Reduced
ic_weights = [0.0, 0.1]  # Reduced

combos = []
for w_emb in embedding_weights:
    for w_rcdc in rcdc_weights:
        for w_ic in ic_weights:
            if abs((w_emb + w_rcdc + w_ic) - 1.0) < 0.01:
                combos.append((w_emb, w_rcdc, w_ic))

# Fewer K values
K_values = [50, 75]  # Reduced from [50, 75, 100]
total_tests = len(combos) * len(K_values)
print(f"  {len(combos)} weight combos × {len(K_values)} K values = {total_tests} tests")
print(f"  Estimated time: {total_tests * 3 / 60:.0f} minutes")

# Run optimization with progress tracking
print("\n[4/6] Running optimization...")
results = []
count = 0

for k in K_values:
    print(f"\n  K={k}:")
    
    for w_emb, w_rcdc, w_ic in combos:
        count += 1
        
        try:
            # Combine features
            combined = np.hstack([
                embeddings * w_emb,
                rcdc_matrix * w_rcdc,
                ic_matrix * w_ic
            ])
            
            # Cluster with memory-safe settings
            clustering = AgglomerativeClustering(
                n_clusters=k,
                linkage='ward',
                compute_distances=False  # Save memory
            )
            labels = clustering.fit_predict(combined)
            
            # Evaluate with sampling to save memory
            sample_size = min(5000, len(df))
            sample_idx = np.random.choice(len(df), sample_size, replace=False)
            
            sil_comb = silhouette_score(
                combined[sample_idx], 
                labels[sample_idx], 
                metric='euclidean'
            )
            ch_comb = calinski_harabasz_score(combined, labels)
            db_comb = davies_bouldin_score(combined, labels)
            
            sil_sem = silhouette_score(
                embeddings[sample_idx], 
                labels[sample_idx], 
                metric='cosine'
            )
            
            # IC homogeneity
            ic_hom = 0
            if 'IC_NAME' in df.columns:
                for cid in np.unique(labels):
                    mask = labels == cid
                    ics = df.loc[mask, 'IC_NAME']
                    purity = ics.value_counts().iloc[0] / len(ics) if len(ics) > 0 else 0
                    ic_hom += purity
                ic_hom /= len(np.unique(labels))
            
            # Composite score
            composite = (
                0.3 * (sil_comb + 1) / 2 +
                0.2 * (sil_sem + 1) / 2 +
                0.2 * min(ch_comb / 1000, 1.0) +
                0.15 * ic_hom +
                0.15 * (1 - min(db_comb / 5, 1.0))
            )
            
            results.append({
                'k': k,
                'w_embedding': w_emb,
                'w_rcdc': w_rcdc,
                'w_ic': w_ic,
                'silhouette_combined': sil_comb,
                'silhouette_semantic': sil_sem,
                'calinski_harabasz': ch_comb,
                'davies_bouldin': db_comb,
                'ic_homogeneity': ic_hom,
                'composite_score': composite
            })
            
            # Free memory
            del combined, clustering, labels
            gc.collect()
            
            if count % 5 == 0:
                print(f"    {count}/{total_tests} ({count/total_tests*100:.0f}%) - Last score: {composite:.3f}")
                
        except Exception as e:
            print(f"    ✗ Error at test {count}: {e}")
            continue

print(f"\n  Completed {len(results)}/{total_tests} tests successfully")

if len(results) == 0:
    print("\n✗ ERROR: All tests failed. Check memory and data.")
    sys.exit(1)

# Analyze
print("\n[5/6] Analyzing results...")
results_df = pd.DataFrame(results)
best = results_df.loc[results_df['composite_score'].idxmax()]

print("\n" + "=" * 70)
print("RESULTS")
print("=" * 70)

print("\n🏆 Best Configuration:")
print(f"  K: {int(best['k'])}")
print(f"  Weights: Emb={best['w_embedding']:.2f}, RCDC={best['w_rcdc']:.2f}, IC={best['w_ic']:.2f}")
print(f"\n  Metrics:")
print(f"    Silhouette (combined): {best['silhouette_combined']:+.4f}")
print(f"    Silhouette (semantic): {best['silhouette_semantic']:+.4f}")
print(f"    Calinski-Harabasz: {best['calinski_harabasz']:.2f}")
print(f"    Davies-Bouldin: {best['davies_bouldin']:.2f}")
print(f"    IC homogeneity: {best['ic_homogeneity']:.1%}")
print(f"    Composite: {best['composite_score']:.4f}")

print("\n📊 Best for each K:")
for k in K_values:
    k_data = results_df[results_df['k'] == k]
    if len(k_data) > 0:
        k_best = k_data.loc[k_data['composite_score'].idxmax()]
        print(f"  K={k}: Emb={k_best['w_embedding']:.2f}, RCDC={k_best['w_rcdc']:.2f}, IC={k_best['w_ic']:.2f} → {k_best['composite_score']:.4f}")

# Compare to pure embedding
pure = results_df[(results_df['w_embedding'] == 1.0) & (results_df['w_rcdc'] == 0.0) & (results_df['w_ic'] == 0.0)]
if len(pure) > 0:
    pure_best = pure.loc[pure['composite_score'].idxmax()]
    imp = (best['composite_score'] - pure_best['composite_score']) / pure_best['composite_score'] * 100
    print(f"\n📈 Hybrid vs Pure Embedding:")
    print(f"  Hybrid: {best['composite_score']:.4f}")
    print(f"  Pure: {pure_best['composite_score']:.4f}")
    print(f"  Improvement: {imp:+.1f}%")
    
    if imp < 0:
        print("\n  💡 Pure embedding performs better - use semantic clustering only")
    elif imp < 5:
        print("\n  💡 Marginal improvement - hybrid may not be worth complexity")
    else:
        print("\n  💡 Significant improvement - hybrid approach recommended")

# Save
print("\n[6/6] Saving results...")
results_df.to_csv('hybrid_weight_optimization_results_safe.csv', index=False)
print("  ✓ hybrid_weight_optimization_results_safe.csv")

config = {
    'sample_size': len(df),
    'k': int(best['k']),
    'weights': {
        'embedding': float(best['w_embedding']),
        'rcdc': float(best['w_rcdc']),
        'ic': float(best['w_ic'])
    },
    'metrics': {
        'silhouette_combined': float(best['silhouette_combined']),
        'silhouette_semantic': float(best['silhouette_semantic']),
        'calinski_harabasz': float(best['calinski_harabasz']),
        'davies_bouldin': float(best['davies_bouldin']),
        'ic_homogeneity': float(best['ic_homogeneity']),
        'composite_score': float(best['composite_score'])
    },
    'interpretation': (
        'Pure semantic' if best['w_embedding'] >= 0.95
        else 'Semantic-dominant' if best['w_embedding'] >= 0.7
        else 'Balanced hybrid'
    )
}

with open('best_hybrid_config_safe.json', 'w') as f:
    json.dump(config, f, indent=2)
print("  ✓ best_hybrid_config_safe.json")

# Simple visualization
try:
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    
    # Scatter plot of all configs
    scatter = ax.scatter(
        results_df['w_embedding'], 
        results_df['composite_score'],
        c=results_df['k'],
        cmap='viridis',
        s=100,
        alpha=0.6
    )
    
    # Highlight best
    ax.scatter(
        best['w_embedding'],
        best['composite_score'],
        color='red',
        s=300,
        marker='*',
        label=f"Best: {best['w_embedding']:.2f}"
    )
    
    ax.set_xlabel('Embedding Weight')
    ax.set_ylabel('Composite Score')
    ax.set_title('Hybrid Weight Optimization Results')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.colorbar(scatter, label='K clusters')
    
    plt.tight_layout()
    plt.savefig('hybrid_optimization_results_safe.png', dpi=150)
    print("  ✓ hybrid_optimization_results_safe.png")
except Exception as e:
    print(f"  ⚠ Could not create plot: {e}")

print("\n" + "=" * 70)
print("OPTIMIZATION COMPLETE!")
print("=" * 70)
print(f"\nRecommendation: {config['interpretation']}")
print(f"Best weights: Emb={best['w_embedding']:.2f}, RCDC={best['w_rcdc']:.2f}, IC={best['w_ic']:.2f}")
