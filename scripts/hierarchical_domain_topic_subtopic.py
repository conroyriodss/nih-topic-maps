#!/usr/bin/env python3
"""
Three-Level Hierarchical Clustering: Domain → Topic → Subtopic
Clusters by TYPE OF SCIENCE, not by IC
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

# Hierarchical configuration
K_DOMAINS = 10          # Level 1: Broad scientific domains
K_TOPICS_PER = 6        # Level 2: Topics within each domain
K_SUBTOPICS_PER = 4     # Level 3: Subtopics within each topic

# Feature weights (NO IC - pure science clustering)
WEIGHT_EMBEDDING = 0.60   # Increased - semantic understanding
WEIGHT_RCDC = 0.25        # NIH categories are scientifically meaningful
WEIGHT_TERMS = 0.15       # Distinctive scientific terms

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
print("HIERARCHICAL CLUSTERING: DOMAIN → TOPIC → SUBTOPIC")
print("=" * 80)
print(f"\nLevels:")
print(f"  Level 1: {K_DOMAINS} Scientific Domains")
print(f"  Level 2: ~{K_TOPICS_PER} Topics per Domain ({K_DOMAINS * K_TOPICS_PER} total)")
print(f"  Level 3: ~{K_SUBTOPICS_PER} Subtopics per Topic ({K_DOMAINS * K_TOPICS_PER * K_SUBTOPICS_PER} total)")

# Load data
print("\n[1/7] Loading embeddings...")
df = pd.read_parquet('embeddings_25k_subsample.parquet')
embeddings = np.stack(df['embedding'].values)
df['APPLICATION_ID'] = df['APPLICATION_ID'].astype('int64')
print(f"  {len(df):,} grants")

# Fetch metadata
print("\n[2/7] Fetching metadata...")
client = bigquery.Client(project=PROJECT_ID)
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
    query_parameters=[bigquery.ArrayQueryParameter("app_ids", "INT64", 
                                                   df['APPLICATION_ID'].tolist())]
)
metadata_df = client.query(query, job_config=job_config).to_dataframe()
metadata_df['APPLICATION_ID'] = metadata_df['APPLICATION_ID'].astype('int64')

cols_to_drop = [c for c in metadata_df.columns if c in df.columns and c != 'APPLICATION_ID']
if cols_to_drop:
    df = df.drop(columns=cols_to_drop)
df = df.merge(metadata_df, on='APPLICATION_ID', how='left')

# Create features (WITHOUT IC)
print("\n[3/7] Creating science-based features...")

# RCDC categories
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

tfidf = TfidfVectorizer(max_features=400, min_df=5, max_df=0.4, ngram_range=(1, 3))
try:
    terms_tfidf = tfidf.fit_transform(df['terms_cleaned']).toarray()
except:
    terms_tfidf = np.zeros((len(df), 1))

# Scale and combine (NO IC)
scaler = StandardScaler()
embeddings_scaled = scaler.fit_transform(embeddings)
rcdc_scaled = rcdc_encoded * np.sqrt(embeddings.shape[1] / max(rcdc_encoded.shape[1], 1))
terms_scaled = terms_tfidf * np.sqrt(embeddings.shape[1] / max(terms_tfidf.shape[1], 1))

science_features = np.hstack([
    WEIGHT_EMBEDDING * embeddings_scaled,
    WEIGHT_RCDC * rcdc_scaled,
    WEIGHT_TERMS * terms_scaled
])

print(f"  Science features: {science_features.shape}")

# LEVEL 1: Cluster into scientific domains
print(f"\n[4/7] LEVEL 1: Clustering into {K_DOMAINS} scientific domains...")
Z_domains = linkage(science_features, method='ward')
df['domain'] = fcluster(Z_domains, K_DOMAINS, criterion='maxclust')

# Generate domain labels
def generate_domain_label(domain_df):
    """Label based on most common RCDC categories"""
    rcdc_counts = Counter()
    for rcdc_list in domain_df['rcdc_list']:
        rcdc_counts.update(rcdc_list)
    
    if rcdc_counts:
        # Get top 2 categories
        top_cats = [cat for cat, _ in rcdc_counts.most_common(2)]
        if len(top_cats) == 1:
            return top_cats[0][:50]
        else:
            # Combine into meaningful domain name
            return f"{top_cats[0][:25]} & {top_cats[1][:25]}"
    return "General Research"

domain_labels = {}
print("\n  Domain labels:")
for domain_id in sorted(df['domain'].unique()):
    domain_df = df[df['domain'] == domain_id]
    label = generate_domain_label(domain_df)
    domain_labels[int(domain_id)] = label
    print(f"    Domain {domain_id:2d}: {label} (n={len(domain_df):,})")

df['domain_label'] = df['domain'].map(domain_labels)

# LEVEL 2: Cluster each domain into topics
print(f"\n[5/7] LEVEL 2: Clustering each domain into ~{K_TOPICS_PER} topics...")
df['topic'] = 0
topic_counter = 1
topic_labels = {}

for domain_id in sorted(df['domain'].unique()):
    domain_mask = df['domain'] == domain_id
    domain_features = science_features[domain_mask]
    
    if len(domain_features) < K_TOPICS_PER * 20:  # Too small for subclustering
        k_topics = max(2, len(domain_features) // 50)
    else:
        k_topics = K_TOPICS_PER
    
    Z_topics = linkage(domain_features, method='ward')
    topic_ids = fcluster(Z_topics, k_topics, criterion='maxclust')
    
    # Map to global topic IDs
    domain_indices = df[domain_mask].index
    for local_topic_id in range(1, k_topics + 1):
        topic_mask = topic_ids == local_topic_id
        df.loc[domain_indices[topic_mask], 'topic'] = topic_counter
        
        # Label
        topic_df = df.loc[domain_indices[topic_mask]]
        rcdc_counts = Counter()
        for rcdc_list in topic_df['rcdc_list']:
            rcdc_counts.update(rcdc_list)
        
        if rcdc_counts:
            top_cat = rcdc_counts.most_common(1)[0][0][:40]
            topic_labels[topic_counter] = f"{domain_labels[domain_id][:20]} > {top_cat}"
        else:
            topic_labels[topic_counter] = f"{domain_labels[domain_id][:20]} > Topic {local_topic_id}"
        
        topic_counter += 1

df['topic_label'] = df['topic'].map(topic_labels)
print(f"  Created {len(topic_labels)} topics across {K_DOMAINS} domains")

# LEVEL 3: Cluster each topic into subtopics
print(f"\n[6/7] LEVEL 3: Clustering each topic into ~{K_SUBTOPICS_PER} subtopics...")
df['subtopic'] = 0
subtopic_counter = 1
subtopic_labels = {}

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
        
        # Label with distinctive term
        subtopic_df = df.loc[topic_indices[subtopic_mask]]
        rcdc_counts = Counter()
        for rcdc_list in subtopic_df['rcdc_list']:
            rcdc_counts.update(rcdc_list)
        
        if rcdc_counts:
            top_cat = rcdc_counts.most_common(1)[0][0][:30]
            subtopic_labels[subtopic_counter] = f"{topic_labels[topic_id][:30]}... > {top_cat}"
        else:
            subtopic_labels[subtopic_counter] = f"{topic_labels[topic_id][:30]}... > {local_subtopic_id}"
        
        subtopic_counter += 1

df['subtopic_label'] = df['subtopic'].map(subtopic_labels)
print(f"  Created {len(subtopic_labels)} subtopics")

# Save hierarchical structure
print(f"\n[7/7] Saving hierarchical clustering...")

output_df = df[[
    'APPLICATION_ID', 'PROJECT_TITLE', 'IC_NAME', 'FY', 'TOTAL_COST',
    'domain', 'domain_label',
    'topic', 'topic_label',
    'subtopic', 'subtopic_label'
]].copy()

output_df.to_csv('hierarchical_domain_topic_subtopic.csv', index=False)
print(f"  Saved: hierarchical_domain_topic_subtopic.csv")

# Save label dictionaries
hierarchy = {
    'domains': domain_labels,
    'topics': topic_labels,
    'subtopics': subtopic_labels,
    'config': {
        'k_domains': K_DOMAINS,
        'k_topics_per_domain': K_TOPICS_PER,
        'k_subtopics_per_topic': K_SUBTOPICS_PER,
        'total_topics': len(topic_labels),
        'total_subtopics': len(subtopic_labels)
    }
}

with open('hierarchy_labels.json', 'w') as f:
    json.dump(hierarchy, f, indent=2)
print(f"  Saved: hierarchy_labels.json")

# Summary statistics
print("\n" + "=" * 80)
print("HIERARCHICAL CLUSTERING COMPLETE")
print("=" * 80)
print(f"\nStructure:")
print(f"  Level 1: {len(domain_labels)} domains")
print(f"  Level 2: {len(topic_labels)} topics")
print(f"  Level 3: {len(subtopic_labels)} subtopics")
print(f"\nCluster sizes:")
print(f"  Domain: {df.groupby('domain').size().min()}-{df.groupby('domain').size().max()}")
print(f"  Topic: {df.groupby('topic').size().min()}-{df.groupby('topic').size().max()}")
print(f"  Subtopic: {df.groupby('subtopic').size().min()}-{df.groupby('subtopic').size().max()}")
print("=" * 80)
