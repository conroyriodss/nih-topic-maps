# NIH Topic Maps - Future Directions

## Current State (November 26, 2025)

Working prototype with 50K grant sample, PubMedBERT embeddings, and K-means clustering.

### File Locations

**GCS Bucket:** gs://od-cl-odss-conroyri-nih-embeddings/

    sample/
      embeddings_pubmedbert_50k.parquet   # 50K PubMedBERT embeddings
      viz_data.json                        # Visualization data
      topic_map_interactive.html           # Live visualization

**BigQuery Datasets:**

    nih_exporter     - Raw ExPORTER data (projects table)
    nih_data         - Yearly tables (projects_fyYYYY, abstracts_fyYYYY)
    nih_processed    - Deduplicated data (projects, projects_with_abstracts)
    nih_analytics    - Analytics tables (grant_scorecard_v2, embedding_sample_50k)

**Repository:** ~/nih-topic-maps/

    scripts/
      find_optimal_k.py           # K optimization (running)
      hybrid_clustering.py        # Hybrid PubMedBERT + RCDC clustering
      analyze_clustering.py       # Cluster quality analysis
      check_category_data.py      # Category data availability
    docs/
      HYBRID_CLUSTERING_STRATEGY.md
      FUTURE_DIRECTIONS.md        # This file
    validation_reports/           # Data quality reports

---

## Phase 1: Visualization Enhancements

### 1.1 Color by NIH Funding Category

Add dropdown to color points by:
- RCDC Category (primary)
- NIH Institute/Center
- Funding Mechanism (R01, P01, etc.)
- Fiscal Year
- Grant Size Category

Implementation:
- Add NIH_SPENDING_CATS to viz_data.json
- Create color scale per category
- Add legend with category counts

### 1.2 Align Clusters with Funding Categories

Options to explore:
- Constrained clustering (current hybrid approach)
- Post-hoc mapping: assign each cluster a primary RCDC category
- Hierarchical: RCDC as top level, PubMedBERT sub-clusters

Validation metrics:
- Purity: % of grants in cluster matching primary RCDC
- Normalized Mutual Information (NMI) between clusters and RCDC
- Adjusted Rand Index (ARI)

---

## Phase 2: Embedding Validation

### 2.1 Validate Project Terms via Embeddings

Question: Do PROJECT_TERMS align with PubMedBERT semantic similarity?

Approach:
1. For each grant, get PubMedBERT nearest neighbors (k=10)
2. Compare PROJECT_TERMS overlap between neighbors
3. Calculate Jaccard similarity of terms vs embedding distance
4. Identify grants where terms and embeddings disagree (anomalies)

Code sketch:

    from sklearn.neighbors import NearestNeighbors
    
    nn = NearestNeighbors(n_neighbors=10, metric='cosine')
    nn.fit(embeddings)
    distances, indices = nn.kneighbors(embeddings)
    
    for i, neighbors in enumerate(indices):
        grant_terms = set(df.iloc[i]['PROJECT_TERMS'].split(';'))
        neighbor_terms = [set(df.iloc[j]['PROJECT_TERMS'].split(';')) for j in neighbors[1:]]
        
        # Calculate average Jaccard similarity
        jaccard_scores = [len(grant_terms & nt) / len(grant_terms | nt) for nt in neighbor_terms]
        avg_jaccard = np.mean(jaccard_scores)

Expected findings:
- High Jaccard = PROJECT_TERMS are semantically meaningful
- Low Jaccard = embeddings capture deeper semantics than keywords
- Can identify grants with misassigned terms

### 2.2 Compare Embedding Models

Potential comparisons:
- PubMedBERT vs SciBERT vs BioBERT
- PubMedBERT vs OpenAI text-embedding-3
- PubMedBERT vs BioLinkBERT

Metrics:
- Cluster quality (silhouette, CH score)
- RCDC alignment
- Term coherence within clusters

---

## Phase 3: Publication-to-Grant Alignment

### 3.1 Core Question

How well do publications align with the original proposed goals of the project?

This is a key accountability metric for NIH program officers.

### 3.2 Data Sources

Available in ExPORTER:
- Project abstracts (proposed work)
- Linked publications (PMIDs via link tables)
- Publication abstracts (via PubMed API)

### 3.3 Methodology

Step 1: Embed grant abstracts (already done)
Step 2: Embed publication abstracts (new)
Step 3: Calculate alignment scores

Alignment Score Options:

A. Cosine Similarity
   - Embed grant abstract
   - Embed each linked publication
   - Calculate mean cosine similarity
   - Higher = publications align with proposal

B. Topic Drift Detection
   - Assign grant to topic cluster
   - Assign each publication to topic cluster
   - Calculate % publications in same topic
   - Lower = potential topic drift

C. Semantic Distance Over Time
   - Order publications by year
   - Track cosine similarity to grant over time
   - Detect if research drifts away from original aims

### 3.4 Implementation Steps

1. Get publication PMIDs from link tables
2. Fetch publication abstracts from PubMed API (or MEDLINE)
3. Generate PubMedBERT embeddings for publications
4. Calculate alignment scores
5. Aggregate at grant, PI, IC, and topic levels

### 3.5 Output Products

- Grant Alignment Scorecard (per grant)
- PI Alignment Scorecard (average across grants)
- IC Alignment Scorecard (average across institute)
- Topic Alignment Scorecard (which topics drift most)
- Temporal Analysis (alignment over time)

### 3.6 Policy Applications

- Identify grants with significant topic drift
- Compare alignment by IC, mechanism, funding level
- Inform renewal decisions
- Benchmark expected vs actual research trajectory

---

## Phase 4: Advanced Analytics

### 4.1 Temporal Topic Evolution

Track how topics change over time:
- Topic size trends (growing vs shrinking)
- Topic emergence/death detection
- Topic splitting/merging

### 4.2 Cross-IC Collaboration

Identify research areas spanning multiple ICs:
- Topics with high IC diversity (current issue)
- Potential collaboration opportunities
- Funding overlap detection

### 4.3 Emerging Research Detection

Use embedding velocity:
- New grants appearing in sparse regions
- Rapid growth in specific embedding neighborhoods
- Early warning for emerging fields

### 4.4 Grant Success Prediction

Features:
- Embedding position (topic)
- IC alignment
- PI track record
- Publication alignment score

Target:
- Renewal success
- Publication output
- Citation impact

---

## Phase 5: Scale to Full Dataset

Current: 50K sample
Target: 2.09M unique projects

Requirements:
- Distributed embedding generation (Vertex AI batch)
- BigQuery ML for clustering at scale
- Optimized visualization (WebGL, data tiling)
- Cloud Run deployment

---

## Priority Ranking

1. Color by funding category (quick win)
2. Validate PROJECT_TERMS with embeddings
3. Publication alignment scoring
4. Temporal topic evolution
5. Scale to full dataset

---

## Questions for NIH Stakeholders

1. Which RCDC categories are most important to track?
2. What constitutes acceptable topic drift?
3. How should alignment scores inform decisions?
4. Who are the target users (POs, IC directors, OD)?
5. What time horizon for publication alignment (2yr, 5yr, 10yr)?

---

*Last updated: November 26, 2025*

---

## Performance: VM vs Cloud Shell

For compute-intensive tasks, use a GCE VM instead of Cloud Shell:

### When to Use VM

- Embedding generation (hours)
- K optimization with many values
- Full dataset clustering (2M+ grants)
- Any job >30 minutes

### Quick VM Setup

    # Create VM with GPUs (for embedding generation)
    gcloud compute instances create nih-compute \
      --zone=us-central1-a \
      --machine-type=n1-standard-8 \
      --accelerator=type=nvidia-tesla-t4,count=1 \
      --image-family=pytorch-latest-gpu \
      --image-project=deeplearning-platform-release \
      --boot-disk-size=100GB \
      --scopes=cloud-platform

    # Or CPU-only for clustering
    gcloud compute instances create nih-compute-cpu \
      --zone=us-central1-a \
      --machine-type=n2-standard-16 \
      --image-family=debian-11 \
      --image-project=debian-cloud \
      --boot-disk-size=50GB \
      --scopes=cloud-platform

    # SSH in
    gcloud compute ssh nih-compute --zone=us-central1-a

    # Install dependencies
    pip install pandas numpy scikit-learn umap-learn google-cloud-bigquery pyarrow

    # Run job
    python3 scripts/find_optimal_k.py

    # Delete when done (saves cost)
    gcloud compute instances delete nih-compute --zone=us-central1-a

### Cost Estimate

- n2-standard-16: ~$0.50/hour
- With T4 GPU: ~$0.75/hour
- Typical clustering job: 1-2 hours = $1-2

Much faster than Cloud Shell timeout issues.
