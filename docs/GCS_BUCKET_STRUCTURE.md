# NIH Topic Maps - GCS Bucket Structure

**Last Updated:** $(date)
**Total Storage:** ~15 GiB across all NIH buckets

## Bucket Overview

### od-cl-odss-conroyri-nih-embeddings (12.94 GiB)
**Purpose:** Store embeddings, UMAP coordinates, and clustering results

**Structure:**
gs://od-cl-odss-conroyri-nih-embeddings/
├── phase1/                    # Initial 50k sample work
│   ├── embedding_sample_50k.jsonl
│   ├── embedding_sample_v2_50k.jsonl
│   ├── embeddings_50k_sample.parquet
│   ├── embeddings_pubmedbert_50k.npy
│   ├── hierarchical_50k_clustered.csv
│   ├── hierarchical_50k_with_umap.csv
│   ├── projects_pubmedbert_50k.json
│   └── projects_pubmedbert_5k.json
├── phase2/                    # 250k+ production clustering
│   ├── hierarchical_250k_with_umap.csv
│   └── sample_250k.csv
├── development/               # Active development work
│   └── clusters_74_tfidf.json
└── archive/                   # Historical/deprecated files
    ├── sample/
    ├── temp/
    └── exporter/

**Key Files:**
- `phase2/hierarchical_250k_with_umap.csv` - Production clustering with 253,487 awards
- `phase1/*_50k.*` - Initial proof-of-concept work
- PubMedBERT embeddings and TF-IDF clusters archived

---

### od-cl-odss-conroyri-nih-processed (0 B → Will grow)
**Purpose:** Store processed grant cards, cluster summaries, and exports

**Structure:**
gs://od-cl-odss-conroyri-nih-processed/
├── grant-cards/               # Entity card exports
│   ├── award/
│   ├── pi/
│   ├── ic/
│   └── institution/
├── clusters/                  # Cluster-level analytics
│   ├── cluster_summaries/
│   ├── topic_analysis/
│   └── domain_mappings/
├── exports/                   # Data exports for external tools
│   ├── csv/
│   ├── json/
│   └── parquet/
├── reports/                   # Generated analysis reports
├── workspace-archive/         # Cloud Shell workspace backups
└── legacy/                    # Data from old nih-analytics-* buckets

---

### od-cl-odss-conroyri-nih-raw-data (1.93 GiB)
**Purpose:** Store raw NIH Reporter data downloads

**Structure:**
gs://od-cl-odss-conroyri-nih-raw-data/
├── abstracts/                 # Project abstracts (parquet, yearly)
├── clinicalstudies/           # Clinical study linkages (parquet, yearly)
├── linktables/               # Award-to-output linkages (parquet, yearly)
├── patents/                   # Patent data (parquet, yearly)
└── projects/                  # Core project/award data (parquet, yearly)

**Notes:**
- Partitioned by YEAR for efficient querying
- Source: NIH Reporter ExPORTER downloads
- Updated periodically from NIH Reporter API

---

### od-cl-odss-conroyri-nih-webapp (0 B)
**Purpose:** Host web application assets (if deployed)

**Status:** Empty (webapp not yet deployed)

---

## Legacy Buckets (To Consolidate)

### gs://nih-analytics-embeddings/
- **Status:** OLD - should merge into od-cl-odss-conroyri-nih-embeddings/legacy/
- **Action:** Review contents, copy to new bucket, delete if obsolete

### gs://nih-analytics-exports/
- **Status:** OLD - should merge into od-cl-odss-conroyri-nih-processed/legacy/
- **Action:** Review contents, copy to new bucket, delete if obsolete

---

## File Naming Conventions

### Embeddings
- `embeddings__.` - Embedding matrices
- `hierarchical__with_umap.` - Clustered data with UMAP coords
- `clusters__.` - Cluster analysis results

### Grant Cards
- `grant_cards__.parquet` - Entity-level aggregations
- Entity types: award, pi, ic, institution

### Exports
- `_export_.` - Timestamped exports
- Formats: CSV (external tools), Parquet (analysis), JSON (web)

### Reports
- `_report_.html` - Analysis reports
- `_data_.json` - Report data

---

## Maintenance Guidelines

### Weekly
- Monitor bucket sizes: `gsutil du -sh gs://bucket-name`
- Check for failed uploads in `/temp` directories

### Monthly
- Archive old workspace backups (>30 days)
- Review development/ folders for completed work → move to archive/

### Quarterly
- Consolidate phase1/ and phase2/ if newer production data available
- Review archive/ folders for deletion candidates (>90 days)
- Update this documentation

### As Needed
- When consolidating legacy buckets (nih-analytics-*)
- When deploying webapp (populate webapp bucket)
- When BigQuery tables become too large (export to GCS)

---

## Access Patterns

### For Analysis
1. **Embeddings:** Load from `phase2/` for production work
2. **Raw Data:** Query via BigQuery, not directly from GCS
3. **Grant Cards:** Load from `processed/grant-cards/`
4. **Reports:** Generate to `processed/reports/`, serve from there

### For Webapp (Future)
1. Store static assets in `webapp/`
2. Load grant card summaries from `processed/exports/json/`
3. Serve pre-computed visualizations from `processed/reports/`

---

## Cost Management

**Current Monthly Estimate:** ~$0.30/month
- Standard storage: $0.023/GB/month
- ~15 GB × $0.023 = $0.345/month

**Optimization Tips:**
1. Move `archive/` to Nearline storage: $0.013/GB/month (43% savings)
2. Delete truly obsolete files from `archive/` after 90 days
3. Compress large CSV files (use parquet when possible)
4. Consolidate/delete legacy buckets when ready

---

## Disaster Recovery

**Backup Strategy:**
- GCS provides 99.999999999% durability
- Critical data also in BigQuery (separate storage)
- Workspace archives in `processed/workspace-archive/`

**Recovery Procedures:**
1. **Lost embeddings:** Regenerate from BigQuery award data (slow, ~12 hours)
2. **Lost grant cards:** Rebuild from BigQuery tables (fast, ~30 minutes)
3. **Lost raw data:** Re-download from NIH Reporter API (slow, rate-limited)

---

## Next Steps Post-Organization

1. ✅ Run this organization script
2. ⏳ Review legacy buckets (nih-analytics-*) for consolidation
3. ⏳ Generate initial grant card exports to `processed/grant-cards/`
4. ⏳ Create cluster summaries in `processed/clusters/`
5. ⏳ Document BigQuery → GCS export workflows
6. ⏳ Set up scheduled backups for workspace changes


---

## Consolidation Log

**Date:** $(date)

### Legacy Buckets Consolidated:
- ✅ nih-analytics-embeddings → od-cl-odss-conroyri-nih-embeddings/legacy/
- ✅ nih-analytics-exports → od-cl-odss-conroyri-nih-processed/legacy/

### Legacy Bucket Contents:
Located in:
- `gs://od-cl-odss-conroyri-nih-embeddings/legacy/nih-analytics-embeddings/`
- `gs://od-cl-odss-conroyri-nih-processed/legacy/nih-analytics-exports/`

**Retention:** Review quarterly, delete if unused for 90+ days

