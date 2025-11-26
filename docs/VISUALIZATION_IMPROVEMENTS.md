# Visualization Improvement Plan

## Current Issues
1. Poor cluster separation in some areas
2. Distant outlier clusters without clear reason
3. Generic topic labels ("health • care • based")
4. Too many ICs in single topics (38+ different ICs)

## Planned Improvements

### Phase 1: Clustering (In Progress)
- [x] Analyze current K=74 clustering quality
- [ ] Run K optimization (testing K=74, 100, 150, 200)
- [ ] Re-cluster with optimal K (~150 per NIH Maps)
- [ ] Merge singleton/tiny clusters

### Phase 2: UMAP Parameters
- [ ] Test different n_neighbors (15 → 30)
- [ ] Test different min_dist (0.1 → 0.0)
- [ ] Use cosine metric instead of euclidean
- [ ] Regenerate 2D coordinates

### Phase 3: Topic Labels
- [ ] Use TF-IDF on cluster abstracts
- [ ] Extract 3-5 most distinctive terms per topic
- [ ] Manual curation of ambiguous labels

### Phase 4: Visualization UX
- [ ] Add topic size indicators
- [ ] Show IC distribution per topic
- [ ] Better color scheme for overlapping clusters
- [ ] Add year timeline filter

## Success Metrics
- Zero clusters with <50 grants
- No topics with >30 different ICs
- All topic labels specific and meaningful
- Better visual separation in 2D space
