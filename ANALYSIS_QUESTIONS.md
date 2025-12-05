# Research Questions for NIH Topic Maps

## Portfolio Analysis

1. **Domain Distribution**
   - Which domains receive most funding?
   - How has distribution changed over time?
   - IC specialization by domain?

2. **Temporal Trends**
   - Which domains are growing/shrinking?
   - Emerging research areas (new clusters)?
   - Declining areas?

3. **Institute Portfolios**
   - Which ICs fund which domains?
   - Portfolio diversity by IC?
   - Cross-IC collaboration patterns?

## Cluster Quality

4. **Validation**
   - Do clusters align with known research areas?
   - Are domain labels appropriate?
   - Outliers and misclassifications?

5. **Granularity**
   - Are 10 domains the right number?
   - Topic/subtopic distributions meaningful?
   - Need for more/fewer levels?

## Visualization Insights

6. **Spatial Patterns**
   - Do nearby grants share characteristics?
   - Clear domain boundaries?
   - Bridging grants between domains?

7. **User Experience**
   - Most useful filters?
   - Performance with 250K points?
   - Additional features needed?

## Policy Implications

8. **Gap Analysis**
   - Underfunded research areas?
   - Overconcentration risks?
   - Diversity of research portfolio?

9. **Strategic Planning**
   - Priority areas for investment?
   - Cross-cutting opportunities?
   - Emerging trends to support?


## Completed Milestones (December 2, 2025)

### ✅ 250K Grant Processing
- **Status**: Complete
- **Grants**: 250,000 (FY 2019-2024)
- **Domains**: 10 major research areas identified
- **Infrastructure**: GCP VM (n1-standard-16)
- **Runtime**: ~37 minutes
- **Cost**: ~$10

### ✅ Interactive Visualization
- **File**: `nih_topic_map_250k_domains.html`
- **Features**:
  - Domain heatmaps
  - 50K grant sample displayed
  - Filtering by IC, FY, keywords
  - Award detail cards
  - Zoom/pan navigation

### Key Files Generated
1. `hierarchical_250k_with_umap.csv` - Full dataset
2. `nih_topic_map_250k_domains.html` - Visualization
3. `create-viz-250k-complete.py` - Generator script

## Next Priority: Hierarchical Expansion

**Goal**: Split 10 domains → 30 topics → 100 subtopics

**Approach**:
1. Use domain assignments as starting point
2. Re-cluster each domain independently
3. Generate 3-level hierarchy
4. Update visualization with drill-down

**Timeline**: ~1 week development + 2 hours compute

## Storage Status

**GCS Bucket**: `gs://od-cl-odss-conroyri-nih-embeddings/`
- ✅ `hierarchical_250k_with_umap.csv` (43 MB)
- ✅ All processing scripts backed up
- ✅ Repository synced to GitHub

---
*Updated: December 2, 2025*
