#!/usr/bin/env python3
"""
Generate embeddings using pure scikit-learn
"""
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD, PCA
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import silhouette_score

print("="*70)
print("GENERATING SEMANTIC EMBEDDINGS FOR AWARDS")
print("="*70)

# Load awards
print("\n[1/5] Loading award data...")
df = pd.read_csv('awards_110k_clustered_k75.csv')
print(f"Loaded {len(df):,} awards")

# Handle missing titles
df['project_title'] = df['project_title'].fillna('Unknown Project')

# Generate TF-IDF features
print("\n[2/5] Generating TF-IDF embeddings...")
vectorizer = TfidfVectorizer(
    max_features=5000,
    ngram_range=(1, 2),
    stop_words='english',
    min_df=2,
    max_df=0.8
)

tfidf_matrix = vectorizer.fit_transform(df['project_title'])
print(f"   TF-IDF matrix: {tfidf_matrix.shape}")

# Reduce dimensionality with SVD
print("\n[3/5] Reducing to 100 dimensions with SVD...")
svd = TruncatedSVD(n_components=100, random_state=42)
embeddings = svd.fit_transform(tfidf_matrix)
print(f"   Embeddings shape: {embeddings.shape}")
print(f"   Variance explained: {svd.explained_variance_ratio_.sum():.2%}")

# Save embeddings
np.save('award_embeddings_tfidf_103k.npy', embeddings)
print("   ✅ Saved: award_embeddings_tfidf_103k.npy")

# Generate 2D projection with PCA (fast and reliable)
print("\n[4/5] Generating 2D visualization coordinates with PCA...")
pca = PCA(n_components=2, random_state=42)
coords = pca.fit_transform(embeddings)

df['umap_x'] = coords[:, 0]
df['umap_y'] = coords[:, 1]

print(f"   Variance explained: {pca.explained_variance_ratio_.sum():.2%}")
print(f"   X range: [{df['umap_x'].min():.2f}, {df['umap_x'].max():.2f}]")
print(f"   Y range: [{df['umap_y'].min():.2f}, {df['umap_y'].max():.2f}]")

# Re-cluster using semantic embeddings
print("\n[5/5] Clustering using semantic embeddings...")

kmeans = MiniBatchKMeans(
    n_clusters=75,
    batch_size=1000,
    random_state=42,
    n_init=10,
    verbose=1
)

df['cluster_semantic_k75'] = kmeans.fit_predict(embeddings)

# Evaluate
sample_size_eval = min(10000, len(df))
silhouette = silhouette_score(embeddings, df['cluster_semantic_k75'], sample_size=sample_size_eval)

print(f"\n✅ Semantic Clustering Results:")
print(f"   Silhouette score: {silhouette:.4f}")
print(f"   Number of clusters: {df['cluster_semantic_k75'].nunique()}")

# Compare to old clustering
from sklearn.metrics import adjusted_rand_score
ari = adjusted_rand_score(df['cluster_k75'], df['cluster_semantic_k75'])
print(f"\n   Comparison to IC/activity clusters:")
print(f"   Adjusted Rand Index: {ari:.4f}")
if ari < 0.3:
    print(f"   → Semantic clusters are DIFFERENT from IC groupings ✅")
else:
    print(f"   → Semantic clusters overlap with IC groupings")

# Save
df.to_csv('awards_110k_with_semantic_clusters.csv', index=False)
print("\n✅ Saved: awards_110k_with_semantic_clusters.csv")

# Analyze top clusters
print("\n" + "="*70)
print("SEMANTIC CLUSTER ANALYSIS")
print("="*70)

# Extract keywords for each cluster
for cluster_id in sorted(df['cluster_semantic_k75'].unique())[:10]:
    cluster_df = df[df['cluster_semantic_k75'] == cluster_id]
    
    vec = TfidfVectorizer(max_features=5, stop_words='english', ngram_range=(1,2))
    titles_combined = ' '.join(cluster_df['project_title'].head(100).tolist())
    
    try:
        vec.fit([titles_combined])
        keywords = ', '.join(vec.get_feature_names_out())
        
        print(f"\nCluster {cluster_id:2d}: {len(cluster_df):,} awards | ${cluster_df['total_lifetime_funding'].sum()/1e9:.1f}B")
        print(f"  Keywords: {keywords[:80]}")
        print(f"  Lead IC: {cluster_df['ic_name'].mode()[0][:55]}")
        print(f"  Top activity: {cluster_df['activity'].mode()[0]}")
    except:
        pass

print("\n" + "="*70)
print("EMBEDDINGS COMPLETE!")
print("="*70)
print("\nFiles created:")
print("  • award_embeddings_tfidf_103k.npy")
print("  • awards_110k_with_semantic_clusters.csv")
print("\nReady for visualization!")
