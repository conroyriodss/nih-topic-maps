#!/usr/bin/env python3
"""
Apply hierarchical clustering to 50k sample
Same approach as 12k: Domain → Topic → Subtopic
"""
import pandas as pd
import numpy as np
from google.cloud import bigquery
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.preprocessing import StandardScaler, MultiLabelBinarizer
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import json
import nltk
from nltk.stem import WordNetLemmatizer

try:
    nltk.data.find('corpora/wordnet')
except:
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)

PROJECT_ID = 'od-cl-odss-conroyri-f75a'

# Same configuration as 12k for consistency
K_DOMAINS = 10
K_TOPICS_PER = 6
K_SUBTOPICS_PER = 4

WEIGHT_EMBEDDING = 0.60
WEIGHT_RCDC = 0.25
WEIGHT_TERMS = 0.15

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

print("=" * 80)
print("HIERARCHICAL CLUSTERING: 50K GRANTS")
print("=" * 80)
print(f"\nConfiguration:")
print(f"  Level 1: {K_DOMAINS} Scientific Domains")
print(f"  Level 2: ~{K_TOPICS_PER} Topics per Domain")
print(f"  Level 3: ~{K_SUBTOPICS_PER} Subtopics per Topic")

# Load embeddings
print("\n[1/6] Loading embeddings...")
df = pd.read_parquet('embeddings_50k_sample.parquet')
embeddings = np.stack(df['embedding'].values)
df['APPLICATION_ID'] = df['APPLICATION_ID'].astype('int64')
print(f"  {len(df):,} grants with {embeddings.shape[1]}-dim embeddings")

# Fetch metadata
print("\n[2/6] Fetching metadata from BigQuery...")
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
metadata_df['APPLICATION_ID'] = metadata_df['APPLICATION_ID'].astype('int64')

cols_to_drop = [c for c in metadata_df.columns if c in df.columns and c != 'APPLICATION_ID']
if cols_to_drop:
    df = df.drop(columns=cols_to_drop)
df = df.merge(metadata_df, on='APPLICATION_ID', how='left')
print(f"  Metadata merged")

# Create features (NO IC - science-based only)
print("\n[3/6] Creating hybrid features...")

# RCDC
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

# Lemmatized terms
def clean_lemmatize_terms(terms_string):
    if pd.isna(terms_string) or terms_string == '':
        return ''
    terms = [t.strip().lower() for t in str(terms_string).split(';') if t.strip()]
    lemmatized = [' '.join([lemmatizer.lemmatize(w, pos='n') for w in t.split()]) for t in terms]
    filtered = [t for t in lemmatized if t not in STOP_TERMS and len(t) > 3]
    return ' '.join(filtered)

df['terms_cleaned'] = df['PROJECT_TERMS'].apply(clean_lemmatize_terms)

tfidf = TfidfVectorizer(max_features=400, min_df=10, max_df=0.4, ngram_range=(1, 3))
try:
    terms_tfidf = tfidf.fit_transform(df['terms_cleaned']).toarray()
except:
    terms_tfidf = np.zeros((len(df), 1))

# Scale and combine
scaler = StandardScaler()
embeddings_scaled = scaler.fit_transform(embeddings)
rcdc_scaled = rcdc_encoded * np.sqrt(embeddings.shape[1] / max(rcdc_encoded.shape[1], 1))
terms_scaled = terms_tfidf * np.sqrt(embeddings.shape[1] / max(terms_tfidf.shape[1], 1))

science_features = np.hstack([
    WEIGHT_EMBEDDING * embeddings_scaled,
    WEIGHT_RCDC * rcdc_scaled,
    WEIGHT_TERMS * terms_scaled
])

print(f"  Hybrid features: {science_features.shape}")

# Save for UMAP later
np.save('science_features_50k.npy', science_features)
print(f"  Saved: science_features_50k.npy")

# LEVEL 1: Domains
print(f"\n[4/6] LEVEL 1: Clustering into {K_DOMAINS} domains...")
Z_domains = linkage(science_features, method='ward')
df['domain'] = fcluster(Z_domains, K_DOMAINS, criterion='maxclust')

# Manual domain labels (same as 12k)
manual_domain_labels = {
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

df['domain_label'] = df['domain'].map(manual_domain_labels)

print("  Domain distribution:")
for domain_id in sorted(df['domain'].unique()):
    count = len(df[df['domain'] == domain_id])
    label = manual_domain_labels.get(domain_id, f"Domain {domain_id}")
    print(f"    {domain_id:2d}. {label:45s}: {count:,}")

# LEVEL 2: Topics
print(f"\n[5/6] LEVEL 2: Clustering domains into topics...")
df['topic'] = 0
topic_counter = 1

for domain_id in sorted(df['domain'].unique()):
    domain_mask = df['domain'] == domain_id
    domain_features = science_features[domain_mask]
    
    if len(domain_features) < K_TOPICS_PER * 20:
        k_topics = max(2, len(domain_features) // 50)
    else:
        k_topics = K_TOPICS_PER
    
    Z_topics = linkage(domain_features, method='ward')
    topic_ids = fcluster(Z_topics, k_topics, criterion='maxclust')
    
    domain_indices = df[domain_mask].index
    for local_topic_id in range(1, k_topics + 1):
        topic_mask = topic_ids == local_topic_id
        df.loc[domain_indices[topic_mask], 'topic'] = topic_counter
        topic_counter += 1

print(f"  Created {topic_counter - 1} topics")

# LEVEL 3: Subtopics
print(f"\n[6/6] LEVEL 3: Clustering topics into subtopics...")
df['subtopic'] = 0
subtopic_counter = 1

for topic_id in sorted(df['topic'].unique()):
    if topic_id == 0:
        continue
    
    topic_mask = df['topic'] == topic_id
    topic_features = science_features[topic_mask]
    
    if len(topic_features) < K_SUBTOPICS_PER * 10:
        k_subtopics = max(2, len(topic_features) // 20)
    else:
        k_subtopics = K_SUBTOPICS_PER
    
    Z_subtopics = linkage(topic_features, method='ward')
    subtopic_ids = fcluster(Z_subtopics, k_subtopics, criterion='maxclust')
    
    topic_indices = df[topic_mask].index
    for local_subtopic_id in range(1, k_subtopics + 1):
        subtopic_mask = subtopic_ids == local_subtopic_id
        df.loc[topic_indices[subtopic_mask], 'subtopic'] = subtopic_counter
        subtopic_counter += 1

print(f"  Created {subtopic_counter - 1} subtopics")

# Save
print(f"\n[7/7] Saving hierarchical clustering...")
output_df = df[['APPLICATION_ID', 'PROJECT_TITLE', 'IC_NAME', 'FY', 'TOTAL_COST',
                'domain', 'domain_label', 'topic', 'subtopic']].copy()

output_df.to_csv('hierarchical_50k_base.csv', index=False)
print(f"  Saved: hierarchical_50k_base.csv")

print("\n" + "=" * 80)
print("HIERARCHICAL CLUSTERING COMPLETE")
print("=" * 80)
print(f"\nStructure:")
print(f"  Grants: {len(df):,}")
print(f"  Domains: {df['domain'].nunique()}")
print(f"  Topics: {df['topic'].nunique()}")
print(f"  Subtopics: {df['subtopic'].nunique()}")
print(f"\nNext: Generate topic labels and UMAP coordinates")
print("=" * 80)
