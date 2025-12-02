#!/usr/bin/env python3
"""
Hybrid Hierarchical Clustering with TF-IDF Term Weighting
Combines: PubMedBERT embeddings + RCDC + IC + weighted PROJECT_TERMS
Filters: Non-biomedical administrative terms
"""
import pandas as pd
import numpy as np
from google.cloud import bigquery
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer, StandardScaler, OneHotEncoder
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import json
import time
from collections import Counter

# Configuration
PROJECT_ID = 'od-cl-odss-conroyri-f75a'

# Component weights (must sum to 1.0)
WEIGHT_EMBEDDING = 0.50   # Semantic understanding
WEIGHT_RCDC = 0.15        # NIH categories
WEIGHT_IC = 0.10          # Organizational structure
WEIGHT_TERMS = 0.25       # Distinctive project terms (TF-IDF weighted)

# Clustering parameters
K_VALUES = [50, 75, 100, 125, 150]

# Non-biomedical terms to filter out (administrative noise)
STOP_TERMS = {
    # Administrative
    'project', 'research', 'study', 'grant', 'core', 'program', 'center',
    'development', 'training', 'support', 'service', 'year', 'years',
    'aim', 'specific', 'aims', 'proposed', 'proposal', 'application',
    # Generic methods
    'data', 'analysis', 'method', 'approach', 'technique', 'tool',
    'system', 'model', 'process', 'investigation', 'evaluation',
    # Overly broad
    'health', 'disease', 'patient', 'clinical', 'treatment', 'therapy',
    'human', 'tissue', 'cell', 'protein', 'gene', 'molecular'
}

print("=" * 70)
print("HYBRID HIERARCHICAL CLUSTERING WITH TF-IDF WEIGHTING")
print("=" * 70)
print(f"\nComponent weights:")
print(f"  Embedding:     {WEIGHT_EMBEDDING:.2f}")
print(f"  RCDC:          {WEIGHT_RCDC:.2f}")
print(f"  IC:            {WEIGHT_IC:.2f}")
print(f"  Terms (TF-IDF): {WEIGHT_TERMS:.2f}")
print(f"  Total:         {sum([WEIGHT_EMBEDDING, WEIGHT_RCDC, WEIGHT_IC, WEIGHT_TERMS]):.2f}")

# Step 1: Load embeddings
print("\n[1/7] Loading embeddings...")
start = time.time()
df = pd.read_parquet('embeddings_25k_subsample.parquet')
embeddings = np.stack(df['embedding'].values)
print(f"  Loaded {len(df):,} grants with {embeddings.shape[1]}-dim embeddings")
print(f"  Time: {time.time() - start:.1f}s")

# Ensure APPLICATION_ID is int64
df['APPLICATION_ID'] = df['APPLICATION_ID'].astype('int64')

# Step 2: Fetch RCDC, IC, and PROJECT_TERMS from BigQuery
print("\n[2/7] Fetching metadata from BigQuery...")
start = time.time()
client = bigquery.Client(project=PROJECT_ID)
app_ids = df['APPLICATION_ID'].tolist()

query = """
SELECT 
  CAST(APPLICATION_ID AS INT64) as APPLICATION_ID,
  NIH_SPENDING_CATS,
  PROJECT_TERMS,
  IC_NAME
FROM `od-cl-odss-conroyri-f75a.nih_exporter.projects`
WHERE CAST(APPLICATION_ID AS INT64) IN UNNEST(@app_ids)
"""
job_config = bigquery.QueryJobConfig(
    query_parameters=[bigquery.ArrayQueryParameter("app_ids", "INT64", app_ids)]
)
metadata_df = client.query(query, job_config=job_config).to_dataframe()

# Ensure matching types
metadata_df['APPLICATION_ID'] = metadata_df['APPLICATION_ID'].astype('int64')

df = df.merge(metadata_df, on='APPLICATION_ID', how='left')
print(f"  Fetched metadata for {len(df):,} grants")
print(f"  RCDC coverage: {df['NIH_SPENDING_CATS'].notna().mean()*100:.1f}%")
print(f"  Terms coverage: {df['PROJECT_TERMS'].notna().mean()*100:.1f}%")
print(f"  Time: {time.time() - start:.1f}s")

# Step 3: Process RCDC categories
print("\n[3/7] Processing RCDC categories...")
def parse_categories(cat_string):
    if pd.isna(cat_string) or cat_string == '':
        return []
    return [c.strip() for c in str(cat_string).split(';') if c.strip()]

df['rcdc_list'] = df['NIH_SPENDING_CATS'].apply(parse_categories)
all_rcdc = set()
for cats in df['rcdc_list']:
    all_rcdc.update(cats)
print(f"  Found {len(all_rcdc)} unique RCDC categories")

if len(all_rcdc) > 0:
    mlb_rcdc = MultiLabelBinarizer(classes=sorted(all_rcdc))
    rcdc_encoded = mlb_rcdc.fit_transform(df['rcdc_list'])
    print(f"  RCDC matrix shape: {rcdc_encoded.shape}")
else:
    rcdc_encoded = np.zeros((len(df), 1))
    print(f"  WARNING: No RCDC categories found")

# Step 4: Process IC codes
print("\n[4/7] Processing IC codes...")
df['IC_NAME'] = df['IC_NAME'].fillna('UNKNOWN')
unique_ics = df['IC_NAME'].unique()
print(f"  Found {len(unique_ics)} unique ICs")

ic_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
ic_encoded = ic_encoder.fit_transform(df[['IC_NAME']])
print(f"  IC matrix shape: {ic_encoded.shape}")

# Step 5: Process PROJECT_TERMS with TF-IDF and filtering
print("\n[5/7] Processing PROJECT_TERMS with TF-IDF weighting...")

def clean_project_terms(terms_string):
    """Clean and filter project terms"""
    if pd.isna(terms_string) or terms_string == '':
        return ''
    
    # Split on semicolons, clean, filter
    terms = [t.strip().lower() for t in str(terms_string).split(';') if t.strip()]
    
    # Remove stop terms
    terms = [t for t in terms if t not in STOP_TERMS]
    
    # Remove very short terms (likely acronyms or noise)
    terms = [t for t in terms if len(t) > 3]
    
    return ' '.join(terms)

df['terms_cleaned'] = df['PROJECT_TERMS'].apply(clean_project_terms)

# Count term coverage
has_terms = df['terms_cleaned'].str.len() > 0
print(f"  Grants with terms after filtering: {has_terms.sum():,} ({has_terms.mean()*100:.1f}%)")

# TF-IDF vectorization (emphasizes rare/distinctive terms)
tfidf = TfidfVectorizer(
    max_features=500,      # Top 500 most distinctive terms
    min_df=5,              # Term must appear in at least 5 documents
    max_df=0.5,            # Term must appear in less than 50% of documents
    ngram_range=(1, 2),    # Unigrams and bigrams
    token_pattern=r'(?u)\b[a-z]{4,}\b'  # Words 4+ chars
)

try:
    terms_tfidf = tfidf.fit_transform(df['terms_cleaned']).toarray()
    print(f"  TF-IDF matrix shape: {terms_tfidf.shape}")
    
    # Show top terms by average TF-IDF score
    term_scores = terms_tfidf.mean(axis=0)
    feature_names = tfidf.get_feature_names_out()
    top_indices = term_scores.argsort()[-20:][::-1]
    print(f"  Top 20 distinctive biomedical terms:")
    for idx in top_indices:
        print(f"    {feature_names[idx]}: {term_scores[idx]:.4f}")
except Exception as e:
    print(f"  WARNING: TF-IDF failed ({e}), using zero matrix")
    terms_tfidf = np.zeros((len(df), 1))

# Step 6: Create hybrid feature matrix
print("\n[6/7] Creating hybrid feature matrix...")

# Normalize each component
scaler = StandardScaler()
embeddings_scaled = scaler.fit_transform(embeddings)

# Scale other features to similar magnitude as embeddings
rcdc_scaled = rcdc_encoded * np.sqrt(embeddings.shape[1] / max(rcdc_encoded.shape[1], 1))
ic_scaled = ic_encoded * np.sqrt(embeddings.shape[1] / max(ic_encoded.shape[1], 1))
terms_scaled = terms_tfidf * np.sqrt(embeddings.shape[1] / max(terms_tfidf.shape[1], 1))

# Combine with weights
hybrid_features = np.hstack([
    WEIGHT_EMBEDDING * embeddings_scaled,
    WEIGHT_RCDC * rcdc_scaled,
    WEIGHT_IC * ic_scaled,
    WEIGHT_TERMS * terms_scaled
])

print(f"  Hybrid feature matrix shape: {hybrid_features.shape}")
print(f"  Memory: {hybrid_features.nbytes / 1e9:.2f} GB")

# Step 7: Hierarchical clustering with multiple K values
print("\n[7/7] Hierarchical clustering parameter sweep...")
print(f"  Computing Ward linkage hierarchy...")
start = time.time()
Z = linkage(hybrid_features, method='ward')
print(f"  Linkage computed in {time.time() - start:.1f}s")

results = []
for K in K_VALUES:
    print(f"\n  Testing K={K}...")
    start = time.time()
    
    labels = fcluster(Z, K, criterion='maxclust')
    unique, counts = np.unique(labels, return_counts=True)
    
    # Compute quality metrics
    sample_size = min(3000, len(hybrid_features))
    sample_idx = np.random.choice(len(hybrid_features), sample_size, replace=False)
    
    silhouette = silhouette_score(hybrid_features[sample_idx], labels[sample_idx])
    calinski = calinski_harabasz_score(hybrid_features, labels)
    davies_bouldin = davies_bouldin_score(hybrid_features, labels)
    
    results.append({
        'K': K,
        'silhouette': float(silhouette),
        'calinski_harabasz': float(calinski),
        'davies_bouldin': float(davies_bouldin),
        'min_size': int(counts.min()),
        'max_size': int(counts.max()),
        'mean_size': float(counts.mean()),
        'tiny_clusters_pct': float((counts < 50).sum() / len(unique) * 100),
        'time': time.time() - start
    })
    
    print(f"    Silhouette: {silhouette:.4f}")
    print(f"    Calinski-Harabasz: {calinski:.0f}")
    print(f"    Davies-Bouldin: {davies_bouldin:.3f}")
    print(f"    Cluster sizes: {counts.min()}-{counts.max()} (mean: {counts.mean():.0f})")

# Results summary
results_df = pd.DataFrame(results)

print("\n" + "=" * 70)
print("RESULTS SUMMARY")
print("=" * 70)

# Composite score
results_df['silhouette_norm'] = (results_df['silhouette'] - results_df['silhouette'].min()) / \
                                 (results_df['silhouette'].max() - results_df['silhouette'].min() + 1e-10)
results_df['ch_norm'] = (results_df['calinski_harabasz'] - results_df['calinski_harabasz'].min()) / \
                        (results_df['calinski_harabasz'].max() - results_df['calinski_harabasz'].min() + 1e-10)
results_df['db_norm'] = 1 - (results_df['davies_bouldin'] - results_df['davies_bouldin'].min()) / \
                            (results_df['davies_bouldin'].max() - results_df['davies_bouldin'].min() + 1e-10)
results_df['composite_score'] = (results_df['silhouette_norm'] + 
                                  results_df['ch_norm'] + 
                                  results_df['db_norm']) / 3

best_idx = results_df['composite_score'].idxmax()
best = results_df.loc[best_idx]

print(f"\n🎯 RECOMMENDED CONFIGURATION:")
print(f"  K: {int(best['K'])}")
print(f"  Silhouette: {best['silhouette']:.4f}")
print(f"  Calinski-Harabasz: {best['calinski_harabasz']:.0f}")
print(f"  Davies-Bouldin: {best['davies_bouldin']:.3f}")
print(f"  Composite Score: {best['composite_score']:.4f}")

# Comparison to pure embeddings
print(f"\n📊 COMPARISON TO PURE EMBEDDINGS:")
print(f"  Pure embeddings (K=75):     Silhouette = -0.0003")
print(f"  Hybrid weighted (K={int(best['K'])}):     Silhouette = {best['silhouette']:.4f}")
if best['silhouette'] > -0.0003:
    improvement = ((best['silhouette'] - (-0.0003)) / abs(-0.0003) * 100)
    print(f"  ✅ Improvement: +{improvement:.0f}%")
else:
    print(f"  ℹ️  Note: Still weak but expected for biomedical continuum")

# Save results
results_df.to_csv('hybrid_hierarchical_results.csv', index=False)
print(f"\nSaved: hybrid_hierarchical_results.csv")

# Save best configuration
best_config = {
    'method': 'hybrid_hierarchical_tfidf',
    'K': int(best['K']),
    'weights': {
        'embedding': WEIGHT_EMBEDDING,
        'rcdc': WEIGHT_RCDC,
        'ic': WEIGHT_IC,
        'terms_tfidf': WEIGHT_TERMS
    },
    'metrics': {
        'silhouette': float(best['silhouette']),
        'calinski_harabasz': float(best['calinski_harabasz']),
        'davies_bouldin': float(best['davies_bouldin']),
        'composite_score': float(best['composite_score'])
    },
    'sample_size': len(df),
    'feature_dimensions': int(hybrid_features.shape[1])
}

with open('hybrid_hierarchical_config.json', 'w') as f:
    json.dump(best_config, f, indent=2)
print(f"Saved: hybrid_hierarchical_config.json")

# Visualization
print(f"\nCreating visualization...")
sns.set_style('whitegrid')
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Silhouette
ax = axes[0, 0]
ax.plot(results_df['K'], results_df['silhouette'], marker='o', linewidth=2, markersize=8)
ax.axhline(y=-0.0003, color='red', linestyle='--', alpha=0.5, label='Pure embeddings baseline')
ax.set_xlabel('K (Number of Clusters)', fontsize=11)
ax.set_ylabel('Silhouette Score', fontsize=11)
ax.set_title('Cluster Separation Quality', fontsize=13, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)

# Calinski-Harabasz
ax = axes[0, 1]
ax.plot(results_df['K'], results_df['calinski_harabasz'], marker='s', linewidth=2, markersize=8, color='orange')
ax.set_xlabel('K (Number of Clusters)', fontsize=11)
ax.set_ylabel('Calinski-Harabasz Index', fontsize=11)
ax.set_title('Variance Ratio', fontsize=13, fontweight='bold')
ax.grid(True, alpha=0.3)

# Davies-Bouldin
ax = axes[1, 0]
ax.plot(results_df['K'], results_df['davies_bouldin'], marker='^', linewidth=2, markersize=8, color='green')
ax.set_xlabel('K (Number of Clusters)', fontsize=11)
ax.set_ylabel('Davies-Bouldin Index', fontsize=11)
ax.set_title('Cluster Similarity (Lower = Better)', fontsize=13, fontweight='bold')
ax.grid(True, alpha=0.3)

# Composite
ax = axes[1, 1]
ax.plot(results_df['K'], results_df['composite_score'], marker='D', linewidth=2, markersize=8, color='purple')
ax.axvline(best['K'], color='red', linestyle='--', alpha=0.5, label=f'Best K={int(best["K"])}')
ax.set_xlabel('K (Number of Clusters)', fontsize=11)
ax.set_ylabel('Composite Score', fontsize=11)
ax.set_title('Overall Quality (Normalized)', fontsize=13, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('hybrid_hierarchical_results.png', dpi=200, bbox_inches='tight')
print(f"Saved: hybrid_hierarchical_results.png")

print("\n" + "=" * 70)
print("HYBRID HIERARCHICAL CLUSTERING COMPLETE!")
print("=" * 70)
print(f"\nNext: View hybrid_hierarchical_results.png and hybrid_hierarchical_config.json")
