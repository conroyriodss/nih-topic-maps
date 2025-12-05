# NIH Topic Maps - Workspace Structure

**Last Updated:** $(date)

## Directory Organization

~/nih-topic-maps/
├── scripts/           # Python, SQL, shell scripts
├── notebooks/         # Jupyter notebooks
├── data/
│   ├── raw/          # Original data (rare - mostly in BigQuery)
│   └── processed/    # Exported/processed files
├── outputs/
│   ├── reports/      # Generated analysis reports
│   └── exports/      # Data exports (CSV, JSON)
├── archive/
│   ├── phase1/       # Phase 1 clustering work
│   └── phase2/       # Phase 2 clustering work (COMPLETED)
├── config/           # Configuration files
├── docs/             # Documentation
└── logs/             # Execution logs

## Data Sources

### Primary Data Location
- **BigQuery Dataset:** `nih_topic_maps`
- **GCS Buckets:**
  - `od-cl-odss-conroyri-nih-embeddings/` - Embeddings and UMAP coordinates
  - `od-cl-odss-conroyri-nih-processed/` - Processed data, grant cards, exports
  - `od-cl-odss-conroyri-nih-raw-data/` - Raw NIH Reporter data
  - `od-cl-odss-conroyri-nih-webapp/` - Web application assets

### Key BigQuery Tables
- `award_clustering` - 253,487 awards with Phase 2 cluster assignments
- `grant_cards_award` - Award-level grant cards
- `grant_cards_pi` - PI aggregations
- `grant_cards_ic` - IC aggregations  
- `grant_cards_institution` - Institution aggregations

## Phase 2 Status (COMPLETED)

✅ **Completed:**
- 253,487 awards clustered
- Grant cards updated with clustering metadata
- VM deleted
- Workspace cleaned and organized

⏳ **Next Steps:**
1. Rebuild entity cards with complete Phase 2 data
2. Generate cluster/topic summaries
3. Create domain analysis reports
4. Build PI collaboration networks

## File Naming Conventions

- `build_*.py` - Pipeline construction
- `analyze_*.py` - Analysis scripts
- `export_*.py` - Data export utilities
- `explore_*.ipynb` - EDA notebooks
- `report_*.ipynb` - Report generation
- `*_YYYYMMDD.*` - Dated snapshots

## Maintenance

- **Weekly:** Review logs for errors
- **Monthly:** Run cleanup script, audit BigQuery tables
- **Quarterly:** Archive old notebooks/scripts to GCS
- **Annual:** Review and update documentation
