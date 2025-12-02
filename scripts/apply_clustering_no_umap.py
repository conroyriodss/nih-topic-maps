#!/usr/bin/env python3
"""
Apply clustering WITHOUT UMAP (we'll add that later or use existing coords)
"""
import pandas as pd
import numpy as np
from google.cloud import bigquery
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.preprocessing import StandardScaler, MultiLabelBinarizer, OneHotEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
import json
import nltk
from nltk.stem import WordNetLemmatizer

try:
    nltk.data.find('corpora/wordnet')
except:
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)

PROJECT_ID = 'od-cl-odss-conroyri-f75a'
K = 50

WEIGHT_EMBEDDING = 0.50
WEIGHT_RCDC = 0.15
WEIGHT_IC = 0.10
WEIGHT_TERMS = 0.25

STOP_TERMS = {
    'project', 'research', 'study', 'grant', 'core', 'program', 'center',
    'development', 'training', 'support', 'service', 'year', 'years',
    'aim', 'specific', 'aims', 'proposed', 'proposal', 'application',
    'data', 'analysis', 'method', 'approach', 'technique', 'tool',
    'system', 'model', 'process', 'investigation', 'evaluation',
    'health', 'disease', 'patient', 'clinical', 'treatment', 'therapy',
    'human', 'tissue', 'cell', 'cells', 'protein', 'proteins', 'gene'
}

lemmatizer = WordNetLemmatizer()

print("=" * 70)
print(f"APPLYING K={K} CLUSTERING (UMAP SEPARATE)")
print("=" * 70)

print("\n[1/4] Loading data...")
df = pd.read_parquet('embeddings_25k_subsample.parquet')
embeddings = np.stack(df['embedding'].values)
df['APPLICATION_ID'] = df['APPLICATION_ID'].astype('int64')
print(f"  {len(df):,} grants")

print("\n[2/4] Fetching metadata...")
client = bigquery.Client(project=PROJECT_ID)
app_ids = df['APPLICATION_ID'].tolist()

query = """
SELECT 
  CAST(APPLICATION_ID AS INT64) as APPLICATION_ID,
  NIH_SPENDING_CATS,
  PROJECT_TERMS,
  IC_NAME,
  PROJECT_TITLE,
  FY,
  TOTAL_COST
FROM `od-cl-odss-conroyri-f75a.nih_exporter.projects`
WHERE CAST(APPLICATION_ID AS INT64) IN UNNEST(@app_ids)
"""
job_config = bigquery.QueryJobConfig(
    query_parameters=[bigquery.ArrayQueryParameter("app_ids", "INT64", app_ids)]
)
metadata_df = client.query(query, job_config=job_config).to_dataframe()
metadata_df['APPLICATION_ID'] = metadata_df['APPLICATION_ID'].astype('int64')

cols_to_drop = [c for c in metadata_df.columns if c in df.columns and c != 'APPLICATION_ID']
if cols_to_drop:
    df = df.drop(columns=cols_to_drop)
df = df.merge(metadata_df, on='APPLICATION_ID', how='left')

print("\n[3/4] Creating hybrid features with lemmatization...")

def parse_categories(cat_string):
    if pd.isna(cat_string) or cat_string == '':
        return []
    return [c.strip() for c in str(cat_string).split(';') if c.strip()]

df['rcdc_list'] = df['NIH_SPENDING_CATS'].apply(parse_categories)
all_rcdc = set()
for cats in df['rcdc_list']:
    all_rcdc.update(cats)

mlb_rcdc = MultiLabelBinarizer(classes=sorted(all_rcdc))
rcdc_encoded = mlb_rcdc.fit_transform(df['rcdc_list']) if len(all_rcdc) > 0 else np.zeros((len(df), 1))

df['IC_NAME'] = df['IC_NAME'].fillna('UNKNOWN')
ic_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
ic_encoded = ic_encoder.fit_transform(df[['IC_NAME']])

def clean_lemmatize_terms(terms_string):
    if pd.isna(terms_string) or terms_string == '':
        return ''
    terms = [t.strip().lower() for t in str(terms_string).split(';') if t.strip()]
    lemmatized = [' '.join([lemmatizer.lemmatize(w, pos='n') for w in t.split()]) for t in terms]
    filtered = [t for t in lemmatized if t not in STOP_TERMS and len(t) > 3]
    return ' '.join(filtered)

df['terms_cleaned'] = df['PROJECT_TERMS'].apply(clean_lemmatize_terms)

tfidf = TfidfVectorizer(max_features=500, min_df=5, max_df=0.4, ngram_range=(1, 3))
try:
    terms_tfidf = tfidf.fit_transform(df['terms_cleaned']).toarray()
except:
    terms_tfidf = np.zeros((len(df), 1))

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

print(f"  Hybrid features: {hybrid_features.shape}")

# Save hybrid features for UMAP later
np.save('hybrid_features_k50.npy', hybrid_features)
print(f"  Saved: hybrid_features_k50.npy (for UMAP later)")

print(f"\n[4/4] Clustering with K={K}...")
Z = linkage(hybrid_features, method='ward')
df['cluster'] = fcluster(Z, K, criterion='maxclust')

cluster_counts = df['cluster'].value_counts().sort_index()
print(f"  Sizes: {cluster_counts.min()}-{cluster_counts.max()} (mean: {cluster_counts.mean():.0f})")

def generate_topic_label(cluster_df):
    rcdc_counts = {}
    for rcdc_list in cluster_df['rcdc_list']:
        for cat in rcdc_list:
            rcdc_counts[cat] = rcdc_counts.get(cat, 0) + 1
    
    ic_mode = cluster_df['IC_NAME'].mode()
    ic = ic_mode.iloc[0] if len(ic_mode) > 0 else 'Mixed'
    
    if rcdc_counts:
        top_rcdc = max(rcdc_counts.items(), key=lambda x: x[1])[0]
        if len(top_rcdc) > 35:
            top_rcdc = top_rcdc[:32] + '...'
        return f"{ic}: {top_rcdc}"
    else:
        return f"{ic}: General Research"

cluster_labels = {}
print("\n  Sample topic labels:")
for cluster_id in sorted(df['cluster'].unique()):
    cluster_df = df[df['cluster'] == cluster_id]
    label = generate_topic_label(cluster_df)
    cluster_labels[int(cluster_id)] = label
    if cluster_id <= 15:
        print(f"    Topic {cluster_id:2d}: {label} (n={len(cluster_df)})")

df['topic_label'] = df['cluster'].map(cluster_labels)

# Export (without UMAP for now)
viz_df = df[[
    'APPLICATION_ID', 'PROJECT_TITLE', 'IC_NAME', 'FY', 
    'TOTAL_COST', 'cluster', 'topic_label'
]].copy()

viz_df['title_short'] = viz_df['PROJECT_TITLE'].fillna('').str[:120]
viz_df['funding_millions'] = (viz_df['TOTAL_COST'].fillna(0) / 1e6).round(2)

viz_df.to_csv('clustering_k50_no_umap.csv', index=False)
print(f"\nSaved: clustering_k50_no_umap.csv")

with open('cluster_labels_k50.json', 'w') as f:
    json.dump(cluster_labels, f, indent=2)
print(f"Saved: cluster_labels_k50.json")

print("\n" + "=" * 70)
print("CLUSTERING COMPLETE!")
print("=" * 70)
print(f"Next: Compute UMAP separately with R or standalone Python")
print(f"Or use existing UMAP coordinates from previous runs")
print("=" * 70)
