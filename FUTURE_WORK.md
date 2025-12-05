# Future Work: NIH Topic Map Enhancement

## Completed (December 1, 2025)
- 3-level hierarchical clustering (5 domains x 13 topics x 24 subtopics)
- 43,320 grants (FY 2000-2024) analyzed
- Interactive UMAP visualization
- Tighter layout with domain background regions

## Phase 1: Expand Historical Data (NEXT)
Goal: Add 1980-1999 grants to create 60-70k dataset
Time: 4-6 hours
Tasks:
- Fetch NIH REPORTER data for FY 1980-1999
- Re-generate embeddings for full dataset
- Re-cluster with K-means hierarchy
- Re-run UMAP layout
- Update visualization

## Phase 2: Topic Network View (FUTURE)
Goal: Network graph showing topic-to-topic relationships
Time: 2-3 hours
Tasks:
- Build topic-to-topic co-funding matrix
- Implement D3 force-directed layout
- Add hover/filter interactions
