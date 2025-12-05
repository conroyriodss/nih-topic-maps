# NIH Topic Clustering Methods Comparison

## Methods Tested (November 28, 2025)

### 1. Original PubMedBERT Embeddings + K-Means

Approach:
- PubMedBERT embeddings on full PROJECT_TERMS
- K-means clustering with K=100
- UMAP for visualization

Results:
- Clusters: 100
- Largest: 1,249 grants (2.9%)
- Smallest: 35 grants
- Issue: Generic catch-all clusters dominated by common terms

### 2. TF-IDF with Generic Term Filtering

Approach:
- Remove 50 generic terms (testing, goals, data, etc.)
- TF-IDF vectorization (weights rare terms higher)
- K-means clustering with K=100

Results:
- Clusters: 100
- Largest: 1,296 grants (3.0%)
- Smallest: 73 grants
- Improvement: Better labels, fewer tiny clusters

### 3. IC-Based Hierarchical Clustering

Approach:
- First cluster by IC (26 institutes)
- Then cluster within each IC (5-20 topics)
- Total: 300 IC-specific topics

Results:
- Topics: 300
- Natural alignment with NIH structure
- Best for navigation and drill-down
- Interpretable hierarchy

### 4. MeSH-Filtered Clustering (In Progress)

Approach:
- Filter PROJECT_TERMS with 746-term MeSH whitelist
- Keep only scientific vocabulary
- TF-IDF + K-means

Expected:
- Cleaner scientific clustering
- Removes grant-speak entirely
- Most interpretable labels

## Recommendation

For NIH stakeholders: IC Hierarchical
- Natural organizational alignment
- Clear drill-down navigation
- 300 specific topics

For scientific analysis: MeSH Filtered
- Pure scientific vocabulary
- Best for research trend analysis
- Most accurate topic labels

For quick iteration: TF-IDF Filtered
- Fast to generate
- No GPU required
- Good enough for prototyping
