# Script Reference Guide
**NIH Topic Maps Project**

Quick reference for modifying and using project scripts.

---

## create_viz_enhanced_simple.py

**Purpose:** Generate interactive visualization  
**Input:** hierarchical_50k_with_umap.csv  
**Output:** HTML file with embedded data  

### Key Customization Points

**Change input file (line 12):**
```python
df = pd.read_csv('hierarchical_50k_with_umap.csv')
```

**Adjust background density (line 145):**
```python
# Current: Every 5th point
background_points = [... if i % 5 == 0]
# Denser: i % 2 (2.5x more points)
# Sparser: i % 10 (50% fewer points)
```

**Domain boundary opacity (line 54):**
```python
f.write('.boundary-layer{opacity:0.2}\n')
# Range: 0.0 (invisible) to 1.0 (opaque)
```

**Dynamic loading (line 380):**
```python
const maxPoints=Math.floor(2000*currentZoom);
# Change 2000 to adjust points at each zoom level
```

**Label font size (line 395):**
```python
.attr("font-size",12/currentZoom+"px")
# Change 12 for base label size
```

**Color scheme (line 360):**
```javascript
const domainColors=d3.scaleOrdinal()
    .range(["#e74c3c","#3498db","#2ecc71",...]);
// Modify hex colors here
```

---

## vm_process_250k.py

**Purpose:** Complete 250K pipeline on VM  
**Environment:** n1-highmem-32 (208GB RAM)  
**Runtime:** 2-3 hours  

### Critical Parameters

**Embedding batch size (line 50):**
```python
batch_size = 250
# Vertex AI max: 250
```

**Rate limiting (line 75):**
```python
if batch_num % 20 == 0:
    time.sleep(2)
# Adjust if getting API errors
```

**Topic count per domain (line 245):**
```python
n_topics = min(6, max(2, len(domain_features) // 500))
# 500 = grants per topic
# Adjust based on sample size:
#   50K: 100
#   100K: 200
#   250K: 500
```

**Subtopic count (line 270):**
```python
n_sub = min(4, max(2, len(topic_features) // 100))
# 100 = grants per subtopic
```

**UMAP memory mode (line 320):**
```python
reducer = umap.UMAP(
    low_memory=True  # Set False for speed on huge VMs
)
```

### Add Checkpointing

Insert after embeddings (line 80):
```python
df.to_pickle('checkpoint_embeddings.pkl')
```

Insert after clustering (line 300):
```python
df.to_pickle('checkpoint_clustered.pkl')
```

Resume from checkpoint:
```python
df = pd.read_pickle('checkpoint_embeddings.pkl')
```

---

## 02_hierarchical_clustering.py

**Purpose:** 3-level hierarchical clustering  

### Tunable Parameters

**Domain count (line 215):**
```python
df['domain'] = fcluster(Z, 10, criterion='maxclust')
# Recommended: 8-15 domains
```

**Feature weights (line 180):**
```python
features = np.hstack([
    0.60 * emb_scaled,    # Embeddings
    0.25 * rcdc_scaled,   # RCDC categories
    0.15 * terms_scaled   # Project terms
])
# Must sum to 1.0
```

**TF-IDF settings (line 150):**
```python
tfidf = TfidfVectorizer(
    max_features=400,  # Reduce to 200 for speed
    min_df=10,         # Increase to 20 for sparsity
    max_df=0.4         # Document frequency cutoff
)
```

**Domain labels (line 220):**
```python
domain_labels = {
    1: "Clinical Trials & Prevention",
    # Modify labels here
}
```

---

## vm_umap_script.py

**Purpose:** Apply UMAP to clustered data  
**Environment:** n1-highmem-8  
**Runtime:** 1-2 minutes for 50K  

### UMAP Parameter Tuning

**Denser layouts:**
```python
reducer = umap.UMAP(
    n_neighbors=30,   # Increase from 15
    min_dist=0.05     # Decrease from 0.1
)
```

**Faster processing:**
```python
reducer = umap.UMAP(
    n_neighbors=10,   # Decrease
    min_dist=0.2,     # Increase
    low_memory=True
)
```

**Better global structure:**
```python
reducer = umap.UMAP(
    n_neighbors=50,   # Much larger
    min_dist=0.3,
    metric='euclidean'  # Alternative to cosine
)
```

---

## Quick Commands

**Check file sizes:**
```bash
ls -lh *.csv *.parquet *.html
```

**Count CSV rows:**
```bash
wc -l hierarchical_*.csv
```

**Preview data:**
```bash
head -20 hierarchical_250k_with_umap.csv | column -t -s,
```

**Check VM status:**
```bash
gcloud compute instances list
```

**Monitor VM process:**
```bash
gcloud compute ssh nih-250k-vm --zone=us-central1-a \
  --command="ps aux | grep python"
```

**Download from GCS:**
```bash
gsutil -m cp gs://od-cl-odss-conroyri-nih-embeddings/hierarchical_*.csv .
```

**Archive results:**
```bash
tar -czf results_$(date +%Y%m%d).tar.gz *.csv *.html
```

---

## Debugging

### Out of Memory Errors

**Reduce feature dimensions:**
```python
features = np.hstack([
    0.70 * emb_scaled,
    0.30 * rcdc_scaled  # Remove terms
])
```

**Enable low memory mode:**
```python
reducer = umap.UMAP(low_memory=True)
```

### API Quota Exceeded

**Add exponential backoff:**
```python
for retry in range(5):
    try:
        batch_embs = model.get_embeddings(batch)
        break
    except Exception as e:
        wait = (2 ** retry) + random()
        time.sleep(wait)
```

### Slow Performance

**Test on sample first:**
```python
df_sample = df.sample(frac=0.1, random_state=42)
# Test pipeline on 10% sample
```

---

## Memory Requirements

| Grants | Min RAM | Recommended |
|--------|---------|-------------|
| 50K    | 16 GB   | 32 GB       |
| 100K   | 32 GB   | 64 GB       |
| 250K   | 64 GB   | 208 GB      |
| 1M     | 256 GB  | 512 GB      |

---

## Best Practices

1. **Test on 5K sample** - Validate logic
2. **Run 50K** - Check quality  
3. **Scale to 250K+** - Production
4. **Delete VMs immediately** - Save money
5. **Version control parameters** - Reproducibility
6. **Archive successful runs** - Safety

---

## Common Modifications

### Change number of domains
Edit line 215 in clustering script:
```python
df['domain'] = fcluster(Z, 12, criterion='maxclust')  # 12 domains
```

### Adjust visualization colors
Edit line 360 in viz script:
```javascript
.range(["#FF6B6B","#4ECDC4","#45B7D1","#FFA07A",...])
```

### Make labels larger
Edit line 395 in viz script:
```javascript
.attr("font-size",16/currentZoom+"px")  # Larger base size
```

### Show more background points
Edit line 145 in viz script:
```python
if i % 3 == 0  # Every 3rd point instead of 5th
```

---

**Last Updated:** December 2, 2024

