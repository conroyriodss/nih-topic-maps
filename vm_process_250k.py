#!/usr/bin/env python3
"""
Full 250k pipeline: embeddings + clustering + UMAP
"""
from google.cloud import storage
import pandas as pd
import numpy as np
import vertexai
from vertexai.language_models import TextEmbeddingModel
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.preprocessing import StandardScaler, MultiLabelBinarizer
from sklearn.feature_extraction.text import TfidfVectorizer
import umap.umap_ as umap
import nltk
from nltk.stem import WordNetLemmatizer
import time

PROJECT_ID = 'od-cl-odss-conroyri-f75a'
BUCKET = 'od-cl-odss-conroyri-nih-embeddings'

print("=" * 80)
print("250K GRANT PROCESSING PIPELINE")
print("=" * 80)
print(f"\nStarted: {time.strftime('%Y-%m-%d %H:%M:%S')}")

# Setup
print("\n[SETUP] Downloading NLTK data...")
try:
    nltk.data.find('corpora/wordnet')
except:
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)

# Step 1: Download from GCS
print("\n[1/6] Downloading 250k sample from GCS...")
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET)

blob = bucket.blob('sample_250k.csv')
blob.download_to_filename('sample_250k.csv')

df = pd.read_csv('sample_250k.csv')
print(f"  Loaded: {len(df):,} grants")

# Step 2: Generate embeddings
print("\n[2/6] Generating embeddings via Vertex AI...")
print(f"  Started: {time.strftime('%H:%M:%S')}")

vertexai.init(project=PROJECT_ID, location='us-central1')
model = TextEmbeddingModel.from_pretrained("text-embedding-005")

texts = df['PROJECT_TITLE'].fillna('').astype(str).tolist()
embeddings = []

batch_size = 250
total_batches = (len(texts) + batch_size - 1) // batch_size

for i in range(0, len(texts), batch_size):
    batch = texts[i:i+batch_size]
    batch_num = i // batch_size + 1
    
    try:
        batch_embs = model.get_embeddings(batch)
        embeddings.extend([e.values for e in batch_embs])
        
        if batch_num % 10 == 0:
            pct = 100 * batch_num / total_batches
            print(f"    Batch {batch_num}/{total_batches} ({pct:.1f}%) - {len(embeddings):,} done")
            
    except Exception as e:
        print(f"    Batch {batch_num} failed, retrying individually...")
        for text in batch:
            try:
                emb = model.get_embeddings([text])[0]
                embeddings.append(emb.values)
            except:
                embeddings.append([0.0] * 768)
    
    if batch_num % 20 == 0:
        time.sleep(2)

df['embedding'] = embeddings
print(f"  Completed: {time.strftime('%H:%M:%S')}")
print(f"  Total embeddings: {len(embeddings):,}")

# Step 3: Features
print("\n[3/6] Creating hybrid features...")
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
print(f"  RCDC categories: {rcdc_encoded.shape[1]}")

stop_terms = {'project', 'research', 'study', 'grant', 'health', 'disease'}

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
print(f"  TF-IDF terms: {terms_tfidf.shape[1]}")

embeddings_array = np.array(embeddings)
scaler = StandardScaler()
emb_scaled = scaler.fit_transform(embeddings_array)
rcdc_scaled = rcdc_encoded * np.sqrt(768 / rcdc_encoded.shape[1])
terms_scaled = terms_tfidf * np.sqrt(768 / terms_tfidf.shape[1])

features = np.hstack([
    0.60 * emb_scaled,
    0.25 * rcdc_scaled,
    0.15 * terms_scaled
])
print(f"  Combined features: {features.shape}")

# Step 4: Clustering
print("\n[4/6] Hierarchical clustering...")
print("  [4a] Creating 10 domains...")
start = time.time()

Z = linkage(features, method='ward')
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
print(f"  Completed in {time.time()-start:.1f}s")

for d in sorted(df['domain'].unique()):
    print(f"    {d:2d}. {domain_labels[d]:40s}: {len(df[df['domain']==d]):,}")

print("\n  [4b] Creating topics...")
df['topic'] = 0
topic_counter = 1

for domain_id in sorted(df['domain'].unique()):
    domain_mask = df['domain'] == domain_id
    domain_indices = df.index[domain_mask].tolist()
    domain_features = features[domain_mask]
    
    n_topics = min(6, max(2, len(domain_features) // 500))
    Z_dom = linkage(domain_features, method='ward')
    topics = fcluster(Z_dom, n_topics, criterion='maxclust')
    
    for local_id in range(1, n_topics + 1):
        local_mask = topics == local_id
        actual_indices = [domain_indices[i] for i, m in enumerate(local_mask) if m]
        df.loc[actual_indices, 'topic'] = topic_counter
        topic_counter += 1

print(f"  Created {topic_counter - 1} topics")

print("\n  [4c] Creating subtopics...")
df['subtopic'] = 0
subtopic_counter = 1

for topic_id in sorted(df['topic'].unique()):
    if topic_id == 0:
        continue
    
    topic_mask = df['topic'] == topic_id
    topic_indices = df.index[topic_mask].tolist()
    topic_features = features[topic_mask]
    
    n_sub = min(4, max(2, len(topic_features) // 100))
    Z_topic = linkage(topic_features, method='ward')
    subs = fcluster(Z_topic, n_sub, criterion='maxclust')
    
    for local_id in range(1, n_sub + 1):
        local_mask = subs == local_id
        actual_indices = [topic_indices[i] for i, m in enumerate(local_mask) if m]
        df.loc[actual_indices, 'subtopic'] = subtopic_counter
        subtopic_counter += 1

print(f"  Created {subtopic_counter - 1} subtopics")

# Step 5: UMAP
print("\n[5/6] Running UMAP...")
print(f"  Started: {time.strftime('%H:%M:%S')}")
print("  This will take 45-60 minutes...")

start = time.time()

reducer = umap.UMAP(
    n_neighbors=15,
    n_components=2,
    min_dist=0.1,
    metric='cosine',
    random_state=42,
    verbose=True,
    low_memory=True
)

coords = reducer.fit_transform(embeddings_array)

elapsed = time.time() - start
print(f"\n  UMAP complete in {elapsed/60:.1f} minutes")
print(f"  X range: [{coords[:, 0].min():.2f}, {coords[:, 0].max():.2f}]")
print(f"  Y range: [{coords[:, 1].min():.2f}, {coords[:, 1].max():.2f}]")

df['umap_x'] = coords[:, 0]
df['umap_y'] = coords[:, 1]

# Step 6: Save
print("\n[6/6] Saving and uploading...")

output = df[['APPLICATION_ID', 'PROJECT_TITLE', 'IC_NAME', 'FY', 'TOTAL_COST',
             'domain', 'domain_label', 'topic', 'subtopic', 'umap_x', 'umap_y']].copy()

output.to_csv('hierarchical_250k_with_umap.csv', index=False)

blob = bucket.blob('hierarchical_250k_with_umap.csv')
blob.upload_from_filename('hierarchical_250k_with_umap.csv')

emb_df = df[['APPLICATION_ID', 'embedding']].copy()
emb_df.to_parquet('embeddings_250k.parquet', index=False)
blob = bucket.blob('embeddings_250k.parquet')
blob.upload_from_filename('embeddings_250k.parquet')

print("\n" + "=" * 80)
print("250K PIPELINE COMPLETE!")
print("=" * 80)
print(f"\nCompleted: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"\nResults:")
print(f"  Grants: {len(df):,}")
print(f"  Domains: {df['domain'].nunique()}")
print(f"  Topics: {df['topic'].nunique()}")
print(f"  Subtopics: {df['subtopic'].nunique()}")
print("\n✅ Uploaded to GCS")
print("=" * 80)
