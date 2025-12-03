# NIH 250K Grant Clustering - Complete Output Index
**Generated:** December 3, 2025, 2:16 PM EST

## Quick Access to Key Files

### 📊 Main Results
- **hierarchical_250k_clustered_k75.csv** (44MB) - Full dataset with cluster assignments
- **cluster_75_labels.csv** (11KB) - All cluster names, keywords, and metadata
- **FINAL_SUMMARY_250K.md** - Executive summary and methodology

### 📈 Visualizations
**Static Images:**
- **nih_250k_labeled_map.png** (793KB) - Main topic map with all 75 clusters labeled
- **nih_250k_cluster_sizes.png** - Size distribution histograms and top 20
- **nih_250k_funding_distribution.png** - Top 30 clusters by funding
- **nih_250k_ic_cluster_heatmap.png** - IC × Cluster distribution matrix

**Interactive:**
- **nih_250k_interactive_viz.html** - Web-based explorer (open in browser)

### 📋 Detailed Reports
- **CLUSTER_LABELS_REPORT.txt** - Complete listing of all 75 clusters
- **cluster_250k_summary.csv** (6.2KB) - Statistical summary by cluster
- **cluster_250k_stats.csv** (5.6KB) - Additional statistics

### 📝 Documentation
- **UPDATE_CONTEXT_DEC3.md** - Technical session notes
- **CONTEXT_FOR_NEXT_SESSION.md** - Previous context (Dec 2)

## Summary Statistics

**Scale:** 250,000 grants | FY 2000-2024 | $126.24B funding
**Clusters:** 75 research topics | K=75 MiniBatchKMeans
**Quality:** Silhouette 0.347 | All clusters span 10+ ICs and 20+ years
**Balance:** Min=337, Median=3,527, Max=6,873 grants per cluster

## Top 5 Research Areas
1. Cancer Centers & Clinical (C51) - $4.9B
2. Cancer & Clinical Research (C67) - $3.9B  
3. Cell & HCV Research (C8) - $3.4B
4. Clinical Centers & Data (C69) - $3.3B
5. HIV/AIDS Care & Health (C4) - $3.2B

## Commands to Explore

View cluster labels:
  cat cluster_75_labels.csv | column -t -s,

Open interactive visualization:
  # Download nih_250k_interactive_viz.html and open in browser

Load data in Python:
  python3
  >>> import pandas as pd
  >>> df = pd.read_csv('hierarchical_250k_clustered_k75.csv')
  >>> labels = pd.read_csv('cluster_75_labels.csv', index_col=0)

Check specific cluster:
  python3 -c "import pandas as pd; df=pd.read_csv('hierarchical_250k_clustered_k75.csv'); print(df[df['cluster_k75']==51][['PROJECT_TITLE','IC_NAME','FY']].head(10))"

## Status
✅ Clustering complete
✅ Labels generated
✅ Visualizations created
✅ Documentation finalized
✅ Ready for stakeholder review

Next: Choose deployment path (exploration vs. production 768D embeddings)
