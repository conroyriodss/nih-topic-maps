#!/usr/bin/env python3
"""
Run this on the high-memory VM to cluster 50k grants
"""
import pandas as pd
import numpy as np
from google.cloud import bigquery, storage
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.preprocessing import StandardScaler, MultiLabelBinarizer
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import json
import nltk
from nltk.stem import WordNetLemmatizer
import time

PROJECT_ID = 'od-cl-odss-conroyri-f75a'
BUCKET = 'od-cl-odss-conroyri-nih-embeddings'

print("=" * 80)
print("NIH 50K CLUSTERING ON HIGH-MEMORY VM")
print("=" * 80)

# Download embeddings from GCS
print("\n[1/8] Downloading embeddings from GCS...")
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET)
blob = bucket.blob('embeddings_50k_sample.parquet')
blob.download_to_filename('embeddings_50k_sample.parquet')

df = pd.read_parquet('embeddings_50k_sample.parquet')
embeddings = np.stack(df['embedding'].values)
print(f"  Loaded {len(df):,} grants with {embeddings.shape[1]}-dim embeddings")

# Fetch metadata
print("\n[2/8] Fetching metadata from BigQuery...")
client = bigquery.Client(project=PROJECT_ID)
query = """
SELECT 
  CAST(APPLICATION_ID AS INT64) as APPLICATION_ID,
  NIH_SPENDING_CATS,
  PROJECT_TERMS
FROM `od-cl-odss-conroyri-f75a.nih_exporter.projects`
WHERE CAST(APPLICATION_ID AS INT64) IN UNNEST(@app_ids)
"""
job_config = bigquery.QueryJobConfig(
    query_parameters=[bigquery.ArrayQueryParameter("app_ids", "INT64", 
                                                   df['APPLICATION_ID'].tolist())]
)
metadata_df = client.query(query, job_config=job_config).to_dataframe()
df = df.merge(metadata_df, on='APPLICATION_ID', how='left')

# Create features
print("\n[3/8] Creating hybrid features...")
lemmatizer = WordNetLemmatizer()

def parse_categories(cat_string):
    if pd.isna(cat_string) or cat_string == '':
        return []
    return [c.strip() for c in str(cat_string).split(';') if c.strip()]

df['rcdc_list'] = df['NIH_SPENDING_CATS'].apply(parse_categories)
all_rcdc = set()
for cats in df['rcdc_list']:
    all_rcdc.update(cats)

mlb = MultiLabelBinarizer(classes=sorted(all_rcdc))
rcdc_encoded = mlb.fit_transform(df['rcdc_list'])

# Terms TF-IDF
stop_terms = {'project', 'research', 'study', 'grant', 'health', 'disease', 
              'clinical', 'cell', 'protein', 'gene'}

def clean_terms(terms_string):
    if pd.isna(terms_string):
        return ''
    terms = [t.strip().lower() for t in str(terms_string).split(';') if t.strip()]
    lemmatized = [' '.join([lemmatizer.lemmatize(w, pos='n') for w in t.split()]) 
                  for t in terms]
    return ' '.join([t for t in lemmatized if t not in stop_terms and len(t) > 3])

df['terms_clean'] = df['PROJECT_TERMS'].apply(clean_terms)
tfidf = TfidfVectorizer(max_features=400, min_df=10, max_df=0.4)
terms_tfidf = tfidf.fit_transform(df['terms_clean']).toarray()

# Combine features
scaler = StandardScaler()
emb_scaled = scaler.fit_transform(embeddings)
rcdc_scaled = rcdc_encoded * np.sqrt(768 / rcdc_encoded.shape[1])
terms_scaled = terms_tfidf * np.sqrt(768 / terms_tfidf.shape[1])

features = np.hstack([
    0.60 * emb_scaled,
    0.25 * rcdc_scaled,
    0.15 * terms_scaled
])
print(f"  Features: {features.shape}, {features.nbytes/1e9:.2f} GB")

# Hierarchical clustering
print("\n[4/8] Computing hierarchical clustering...")
print("  This will take 15-20 minutes...")
start = time.time()
Z = linkage(features, method='ward')
print(f"  Linkage computed in {(time.time()-start)/60:.1f} min")

# Domain level
print("\n[5/8] Assigning domains...")
df['domain'] = fcluster(Z, 10, criterion='maxclust')

domain_labels = {
    1: "Clinical Trials & Prevention",
    2: "Behavioral & Social Science",
    3: "Genetics & Biotechnology",
    4: "Rare Diseases & Genomics",
    5: "Neuroscience & Behavior",
    6: "Molecular Biology & Genomics",
    7: "Infectious Disease & Immunology",
    8: "Clinical & Translational Research",
    9: "Cancer Biology & Oncology",
    10: "Bioengineering & Technology"
}
df['domain_label'] = df['domain'].map(domain_labels)

# Topics
print("\n[6/8] Creating topics...")
df['topic'] = 0
topic_counter = 1
for domain_id in range(1, 11):
    mask = df['domain'] == domain_id
    Z_dom = linkage(features[mask], method='ward')
    n_topics = min(6, len(features[mask]) // 100)
    topics = fcluster(Z_dom, n_topics, criterion='maxclust')
    for t in range(1, n_topics + 1):
        df.loc[mask & (topics == t), 'topic'] = topic_counter
        topic_counter += 1

# Subtopics
print("\n[7/8] Creating subtopics...")
df['subtopic'] = 0
subtopic_counter = 1
for topic_id in df['topic'].unique():
    if topic_id == 0:
        continue
    mask = df['topic'] == topic_id
    Z_topic = linkage(features[mask], method='ward')
    n_sub = min(4, len(features[mask]) // 30)
    subs = fcluster(Z_topic, n_sub, criterion='maxclust')
    for s in range(1, n_sub + 1):
        df.loc[mask & (subs == s), 'subtopic'] = subtopic_counter
        subtopic_counter += 1

# Save and upload
print("\n[8/8] Saving and uploading results...")
output = df[['APPLICATION_ID', 'PROJECT_TITLE', 'IC_NAME', 'FY', 'TOTAL_COST',
             'domain', 'domain_label', 'topic', 'subtopic']].copy()
output.to_csv('hierarchical_50k_clustered.csv', index=False)

# Upload to GCS
blob = bucket.blob('hierarchical_50k_clustered.csv')
blob.upload_from_filename('hierarchical_50k_clustered.csv')

print("\n" + "=" * 80)
print("CLUSTERING COMPLETE!")
print("=" * 80)
print(f"  Grants: {len(df):,}")
print(f"  Domains: {df['domain'].nunique()}")
print(f"  Topics: {df['topic'].nunique()}")
print(f"  Subtopics: {df['subtopic'].nunique()}")
print(f"\n✅ Uploaded to: gs://{BUCKET}/hierarchical_50k_clustered.csv")
print("=" * 80)
