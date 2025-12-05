#!/usr/bin/env python3
"""
Hybrid Hierarchical Clustering with Lemmatization
Groups related terms: cell/cells, protein/proteins, etc.
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
import nltk
from nltk.stem import WordNetLemmatizer

# Download NLTK data (only needed once)
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    print("Downloading NLTK WordNet data...")
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)

# Configuration
PROJECT_ID = 'od-cl-odss-conroyri-f75a'
WEIGHT_EMBEDDING = 0.50
WEIGHT_RCDC = 0.15
WEIGHT_IC = 0.10
WEIGHT_TERMS = 0.25
K_VALUES = [50, 75, 100, 125, 150]

# Enhanced stop terms (more aggressive filtering)
STOP_TERMS = {
    # Administrative
    'project', 'research', 'study', 'grant', 'core', 'program', 'center',
    'development', 'training', 'support', 'service', 'year', 'years',
    'aim', 'specific', 'aims', 'proposed', 'proposal', 'application',
    # Generic methods
    'data', 'analysis', 'method', 'approach', 'technique', 'tool',
    'system', 'model', 'process', 'investigation', 'evaluation',
    # Overly broad biomedical (these appeared in top terms but aren't distinctive)
    'health', 'disease', 'patient', 'clinical', 'treatment', 'therapy',
    'human', 'tissue', 'cell', 'cells', 'protein', 'proteins', 'gene', 
    'genes', 'molecular', 'biology', 'structure', 'function', 'medicine',
    # Also remove common adjectives
    'new', 'novel', 'important', 'major', 'basic', 'translational'
}

print("=" * 70)
print("HYBRID HIERARCHICAL CLUSTERING (WITH LEMMATIZATION)")
print("=" * 70)

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

# Load embeddings
print("\n[1/7] Loading embeddings...")
df = pd.read_parquet('embeddings_25k_subsample.parquet')
embeddings = np.stack(df['embedding'].values)
df['APPLICATION_ID'] = df['APPLICATION_ID'].astype('int64')
print(f"  Loaded {len(df):,} grants")

# Fetch metadata
print("\n[2/7] Fetching metadata from BigQuery...")
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
metadata_df['APPLICATION_ID'] = metadata_df['APPLICATION_ID'].astype('int64')

# Drop conflicting columns
cols_to_drop = [c for c in ['NIH_SPENDING_CATS', 'PROJECT_TERMS', 'IC_NAME'] if c in df.columns]
if cols_to_drop:
    df = df.drop(columns=cols_to_drop)

df = df.merge(metadata_df, on='APPLICATION_ID', how='left')
print(f"  Merged. RCDC: {df['NIH_SPENDING_CATS'].notna().mean()*100:.1f}%")

# Process RCDC
print("\n[3/7] Processing RCDC categories...")
def parse_categories(cat_string):
    if pd.isna(cat_string) or cat_string == '':
        return []
    return [c.strip() for c in str(cat_string).split(';') if c.strip()]

df['rcdc_list'] = df['NIH_SPENDING_CATS'].apply(parse_categories)
all_rcdc = set()
for cats in df['rcdc_list']:
    all_rcdc.update(cats)

if len(all_rcdc) > 0:
    mlb_rcdc = MultiLabelBinarizer(classes=sorted(all_rcdc))
    rcdc_encoded = mlb_rcdc.fit_transform(df['rcdc_list'])
    print(f"  RCDC matrix: {rcdc_encoded.shape}")
else:
    rcdc_encoded = np.zeros((len(df), 1))

# Process IC
print("\n[4/7] Processing IC codes...")
df['IC_NAME'] = df['IC_NAME'].fillna('UNKNOWN')
ic_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
ic_encoded = ic_encoder.fit_transform(df[['IC_NAME']])
print(f"  IC matrix: {ic_encoded.shape}")

# Process terms with LEMMATIZATION
print("\n[5/7] Processing PROJECT_TERMS with lemmatization + TF-IDF...")
print("  Lemmatizing terms to group cell/cells, protein/proteins, etc...")

def clean_and_lemmatize_terms(terms_string):
    """Clean, lemmatize, and filter project terms"""
    if pd.isna(terms_string) or terms_string == '':
        return ''
    
    # Split on semicolons
    terms = [t.strip().lower() for t in str(terms_string).split(';') if t.strip()]
    
    # Lemmatize (converts plurals to singular, verb forms to base)
    lemmatized = []
    for term in terms:
        # Lemmatize each word in multi-word terms
        words = term.split()
        lemmatized_words = [lemmatizer.lemmatize(w, pos='n') for w in words]  # pos='n' for nouns
        lemmatized_term = ' '.join(lemmatized_words)
        lemmatized.append(lemmatized_term)
    
    # Remove stop terms AFTER lemmatization
    filtered = [t for t in lemmatized if t not in STOP_TERMS and len(t) > 3]
    
    return ' '.join(filtered)

df['terms_cleaned'] = df['PROJECT_TERMS'].apply(clean_and_lemmatize_terms)
has_terms = df['terms_cleaned'].str.len() > 0
print(f"  {has_terms.sum():,} grants with terms after lemmatization ({has_terms.mean()*100:.1f}%)")

tfidf = TfidfVectorizer(
    max_features=500,
    min_df=5,              # Must appear in at least 5 documents
    max_df=0.4,            # Must appear in less than 40% (more restrictive)
    ngram_range=(1, 3),    # Include trigrams for phrases like "Alzheimer disease"
    token_pattern=r'(?u)\b[a-z]{4,}\b'
)

try:
    terms_tfidf = tfidf.fit_transform(df['terms_cleaned']).toarray()
    print(f"  TF-IDF matrix: {terms_tfidf.shape}")
    
    # Top terms (should now be more distinctive)
    term_scores = terms_tfidf.mean(axis=0)
    feature_names = tfidf.get_feature_names_out()
    top_indices = term_scores.argsort()[-20:][::-1]
    print(f"  Top 20 distinctive biomedical terms (after lemmatization):")
    for idx in top_indices:
        print(f"    {feature_names[idx]}: {term_scores[idx]:.4f}")
except Exception as e:
    print(f"  TF-IDF failed: {e}")
    terms_tfidf = np.zeros((len(df), 1))

# Create hybrid features
print("\n[6/7] Creating hybrid features...")
scaler = StandardScaler()
embeddings_scaled = scaler.fit_transform(embeddings)

rcdc_scaled = rcdc_encoded * np.sqrt(embeddings.shape[1] / max(rcdc_encoded.shape[1], 1))
ic_scaled = ic_encoded * np.sqrt(embeddings.shape[1] / max(ic_encoded.shape[1], 1))
terms_scaled = terms_tfidf * np.sqrt(embeddings.shape[1] / max(terms_tfidf.shape[1], 1))

hybrid_features = np.hstack([
    WEIGHT_EMBEDDING * embeddings_scaled,
    WEIGHT_RCDC * rcdc_scaled,
    WEIGHT_IC * ic_scaled,
    WEIGHT_TERMS * terms_scaled
])

print(f"  Hybrid matrix: {hybrid_features.shape}, {hybrid_features.nbytes/1e9:.2f} GB")

# Hierarchical clustering
print("\n[7/7] Hierarchical clustering...")
start = time.time()
Z = linkage(hybrid_features, method='ward')
print(f"  Ward linkage computed in {time.time()-start:.1f}s")

results = []
for K in K_VALUES:
    print(f"\n  K={K}...")
    labels = fcluster(Z, K, criterion='maxclust')
    unique, counts = np.unique(labels, return_counts=True)
    
    sample_idx = np.random.choice(len(hybrid_features), min(3000, len(hybrid_features)), replace=False)
    sil = silhouette_score(hybrid_features[sample_idx], labels[sample_idx])
    ch = calinski_harabasz_score(hybrid_features, labels)
    db = davies_bouldin_score(hybrid_features, labels)
    
    results.append({
        'K': K,
        'silhouette': float(sil),
        'calinski_harabasz': float(ch),
        'davies_bouldin': float(db),
        'mean_size': float(counts.mean()),
        'tiny_pct': float((counts < 50).sum() / len(unique) * 100)
    })
    
    print(f"    Sil: {sil:.4f}, CH: {ch:.0f}, DB: {db:.3f}, Tiny: {results[-1]['tiny_pct']:.1f}%")

results_df = pd.DataFrame(results)

# Composite score
results_df['composite'] = (
    (results_df['silhouette'] - results_df['silhouette'].min()) / (results_df['silhouette'].max() - results_df['silhouette'].min() + 1e-10) +
    (results_df['calinski_harabasz'] - results_df['calinski_harabasz'].min()) / (results_df['calinski_harabasz'].max() - results_df['calinski_harabasz'].min() + 1e-10) +
    (1 - (results_df['davies_bouldin'] - results_df['davies_bouldin'].min()) / (results_df['davies_bouldin'].max() - results_df['davies_bouldin'].min() + 1e-10))
) / 3

best = results_df.loc[results_df['composite'].idxmax()]

print("\n" + "=" * 70)
print("🎯 RECOMMENDED CONFIGURATION (LEMMATIZED)")
print("=" * 70)
print(f"  K: {int(best['K'])}")
print(f"  Silhouette: {best['silhouette']:.4f}")
print(f"  Calinski-Harabasz: {best['calinski_harabasz']:.0f}")
print(f"  Davies-Bouldin: {best['davies_bouldin']:.3f}")
print(f"  Tiny clusters: {best['tiny_pct']:.1f}%")
print(f"\n📊 COMPARISON:")
print(f"  Pure embeddings (K=75):  Sil = -0.0003")
print(f"  Hybrid lemmatized (K={int(best['K'])}): Sil = {best['silhouette']:.4f}")
if best['silhouette'] > 0:
    print(f"  ✅ Achieved POSITIVE clustering!")
print("=" * 70)

# Save
results_df.to_csv('hybrid_lemmatized_results.csv', index=False)
with open('hybrid_lemmatized_config.json', 'w') as f:
    json.dump({
        'method': 'hybrid_hierarchical_lemmatized',
        'K': int(best['K']),
        'silhouette': float(best['silhouette']),
        'calinski_harabasz': float(best['calinski_harabasz']),
        'davies_bouldin': float(best['davies_bouldin']),
        'weights': {
            'embedding': WEIGHT_EMBEDDING,
            'rcdc': WEIGHT_RCDC,
            'ic': WEIGHT_IC,
            'terms_tfidf': WEIGHT_TERMS
        }
    }, f, indent=2)

print(f"\nSaved: hybrid_lemmatized_results.csv, hybrid_lemmatized_config.json")
