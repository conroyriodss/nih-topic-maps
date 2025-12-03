#!/usr/bin/env python3
"""
Generate representative labels for 75 clusters
Uses TF-IDF on project titles
"""
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import re

print("="*70)
print("GENERATING LABELS FOR 75 CLUSTERS")
print("="*70)

# Load data
df = pd.read_csv('hierarchical_250k_clustered_k75.csv')
print(f"\nLoaded {len(df):,} grants in {df['cluster_k75'].nunique()} clusters")

# Clean titles
def clean_title(text):
    text = str(text).lower()
    text = re.sub(r'[^a-z\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

df['title_clean'] = df['PROJECT_TITLE'].apply(clean_title)

# Generate labels for each cluster
cluster_labels = {}

print("\n🏷️  Generating cluster labels...")

for cluster_id in sorted(df['cluster_k75'].unique()):
    cluster_df = df[df['cluster_k75'] == cluster_id]
    
    # Get top keywords via TF-IDF
    vectorizer = TfidfVectorizer(max_features=10, stop_words='english', ngram_range=(1,2))
    try:
        tfidf = vectorizer.fit_transform(cluster_df['title_clean'].head(500))
        keywords = vectorizer.get_feature_names_out()[:5]
        
        # Create label
        label = ' & '.join(keywords[:3]).title()
        
        # Get metadata
        lead_ic = cluster_df['IC_NAME'].mode()[0] if len(cluster_df) > 0 else 'Unknown'
        n_grants = len(cluster_df)
        total_funding = cluster_df['TOTAL_COST'].sum() / 1e6
        
        cluster_labels[cluster_id] = {
            'label': label,
            'keywords': ', '.join(keywords),
            'lead_ic': lead_ic,
            'n_grants': n_grants,
            'funding_millions': total_funding
        }
        
        print(f"   Cluster {cluster_id:2d}: {label:50s} ({n_grants:,} grants)")
        
    except:
        cluster_labels[cluster_id] = {
            'label': f'Cluster {cluster_id}',
            'keywords': '',
            'lead_ic': '',
            'n_grants': len(cluster_df),
            'funding_millions': 0
        }

# Save
labels_df = pd.DataFrame.from_dict(cluster_labels, orient='index')
labels_df.index.name = 'cluster_id'
labels_df.to_csv('cluster_75_labels.csv')

print(f"\n✅ Saved: cluster_75_labels.csv")
print(f"   Labels for all 75 clusters with keywords and metadata")

# Show top 10 by funding
print(f"\n💰 TOP 10 CLUSTERS BY FUNDING:")
top10 = labels_df.nlargest(10, 'funding_millions')
for idx, row in top10.iterrows():
    print(f"   {idx:2d}. {row['label']:45s} ${row['funding_millions']:,.0f}M ({row['n_grants']:,} grants)")

print("\n" + "="*70)
