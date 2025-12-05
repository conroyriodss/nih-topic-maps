PROJECT_STRUCTURE_20251205.md
NIH Topic Maps - Project Structure Documentation
Last Updated: December 5, 2025, 10:35 AM EST
Status: Phase 2 Complete - Entity Cards Complete - Ready for Topic Analysis

Executive Summary
Completed Milestones
Phase 2 Clustering: 253,487 NIH grant awards clustered

Grant Cards Updated: Phase 2 cluster assignments integrated

Entity Cards Built: PI, Institution, and IC aggregations complete

Workspace Organized: Cloud Shell (25% usage), GCS structured by phase

Current State
Total Funding Analyzed: $934B across 65,031 PIs

Institutions Profiled: 2,599 organizations with cluster specializations

NIH Portfolio: 45 ICs with strategic distribution analysis

Data Location: BigQuery nih_analytics (source), nih_processed (entity cards)

Next Phase
Topic/domain analysis and cluster summaries

PI collaboration network analysis

Specialized reports for strategic planning

Cloud Shell Workspace
Directory Structure
text
/home/conroyri/
├── nih-topic-maps/           # Main project (organized, 1.8GB archived)
│   ├── scripts/              # Production scripts
│   ├── notebooks/            # Analysis notebooks
│   ├── data/                 # Local data cache (minimal)
│   ├── outputs/              # Generated reports
│   ├── docs/                 # Project documentation (THIS FILE)
│   └── archive/              # Deprecated files
├── exports/                  # Temporary exports (65MB)
├── big-query/                # BigQuery utility scripts (24KB)
└── cleanup.sh               # Workspace maintenance script
Disk Usage
Total Home Directory: 1.2GB / 4.8GB (25% utilization)

Project Directory: Organized and archived to GCS

System Caches: Cleaned (Python pycache, temp files removed)

Large Files: Phase 1 clustering archived to GCS

Google Cloud Storage Structure
Primary Buckets
1. gs://od-cl-odss-conroyri-nih-embeddings/ (12.94 GiB)
Purpose: Vector embeddings and clustering outputs

text
gs://od-cl-odss-conroyri-nih-embeddings/
├── phase1/                   # Phase 1: 50k sample clustering (643 MB)
│   ├── embeddings_project_terms_50k.parquet
│   ├── hierarchical_50k_clustered.csv
│   ├── hierarchical_50k_with_umap.csv
│   ├── clusters_74_tfidf.json
│   └── projects_pubmedbert_*.json
├── phase2/                   # Phase 2: 253k full clustering (281 MB)
│   ├── hierarchical_250k_with_umap.csv
│   └── sample_250k.csv
├── exporter/                 # NIH ExPORTER linktables
│   └── linktables_parquet/  # By year (1994-2024)
├── sample/                   # Clustering analysis samples
│   ├── clustering_summary_*.json
│   └── cluster_centers_*.npy
└── legacy-embeddings/        # Consolidated from old bucket (PENDING)
File Types:

Parquet: 218 files (embeddings, structured data)

CSV: 4 files (hierarchical clustering results)

JSON: 136 files (cluster metadata, summaries)

NPY: NumPy arrays (embeddings, cluster centers)

2. gs://od-cl-odss-conroyri-nih-raw-data/ (1.93 GiB)
Purpose: Original NIH ExPORTER data

text
gs://od-cl-odss-conroyri-nih-raw-data/
├── abstracts/                # Publication abstracts (parquet)
├── clinicalstudies/          # Clinical trial linkages (parquet)
├── linktables/               # Award-publication links (107 parquet files)
├── patents/                  # Patent linkages (parquet)
└── projects/                 # Project/award records (parquet)
Data Coverage: 1985-2024 fiscal years

3. gs://od-cl-odss-conroyri-nih-processed/ (Ready for Exports)
Purpose: Processed datasets and entity cards

text
gs://od-cl-odss-conroyri-nih-processed/
├── archive/                  # Historical Phase 1 work
│   └── phase1/              # Archived clustering outputs
├── entity-cards/             # Entity card outputs (READY FOR EXPORT)
│   ├── pi/                  # Principal Investigator cards (65,031 PIs)
│   ├── ic/                  # Institute/Center cards (45 ICs)
│   └── institutions/        # Organization cards (2,599 institutions)
├── grant-cards/              # Award-level grant cards (PENDING)
├── clusters/                 # Cluster analysis outputs (PENDING)
├── exports/                  # BigQuery exports
├── documentation/            # Project documentation (THIS FILE)
└── workspace-archive/        # Cloud Shell archives
4. gs://od-cl-odss-conroyri-nih-webapp/ (Empty)
Purpose: Web application deployment assets (reserved for future use)

5. System Buckets (Do Not Modify)
gs://gcf-v2-sources-893751956690-us-central1/ - Cloud Functions source

gs://gcf-v2-uploads-893751956690.us-central1.cloudfunctions.appspot.com/ - CF uploads

gs://run-sources-od-cl-odss-conroyri-f75a-us-central1/ - Cloud Run deployments

Buckets to Consolidate
gs://nih-analytics-embeddings/ - Merge into main embeddings bucket

gs://nih-analytics-exports/ - Merge into processed bucket

BigQuery Datasets
Dataset: nih_analytics (PRIMARY - Production Data)
Purpose: Phase 2 clustering results and production grant cards

Core Tables
Grant Cards (Primary Asset):

grant_cards_v2_0_complete - CURRENT PRODUCTION (253,487+ awards)

Fields: CORE_PROJECT_NUM, ADMINISTERING_IC, ACTIVITY, type1_title

Fields: contact_pi_name, all_pi_names, type1_project_terms

Fields: TOTAL_LIFETIME_FUNDING, FIRST/LAST_FISCAL_YEAR

Fields: PRIMARY_ORG, PRIMARY_STATE, cluster_id, cluster_label

Phase 2 cluster assignments integrated

Grant Card Version History:

grant_cards_v1_3_production - Phase 1 production baseline

grant_cards_v1_4_hierarchical - Initial hierarchical clustering

grant_cards_v1_5_hierarchical - Enhanced hierarchy

grant_cards_v1_6_backup_before_phase2 - Pre-Phase 2 backup (ARCHIVE)

grant_cards_v1_6_with_agency - Agency field added

grant_cards_v2_0_complete - CURRENT

Clustering Tables:

phase2_cluster_assignments - 253,487 awards with Phase 2 clusters

Fields: CORE_PROJECT_NUM, cluster_id, cluster_label

Fields: domain_id, domain_name, umap_x, umap_y

Fields: ic_cluster_size, assignment_method

cluster_hierarchy_complete - Hierarchical cluster structure

clusterable_unclustered - Awards excluded from clustering

phase2_unclustered_awards - Unclustered in Phase 2

phase2_unclustered_for_ml - Prepared for ML clustering

grant_topic_mapping_tfidf - TF-IDF topic mappings

Scorecards:

grant_scorecard_v2 - Production scorecards

Partitioned by: agency, funding_category, administering_ic

grant_scorecard - Legacy scorecard (administering_ic, activity)

grant_scorecard_with_agency (VIEW) - Scorecard with agency dimension

Analytics Tables:

pi_award_portfolio - PI-level aggregations

grants_for_embedding - Prepared for embedding generation

grants_for_embedding_v2 - Enhanced preparation

Views:

grant_cards_production - Current production view to v2_0_complete

Export Tables:

export_cluster_metadata - Cluster metadata for external use

Dataset: nih_processed (Entity Cards)
Purpose: Entity-level aggregations from Phase 2 data

Entity Card Tables (COMPLETE - Dec 5, 2025)
PI Cards:

pi_cards_phase2 - 65,031 Principal Investigators

Fields: pi_name, total_awards, total_funding_millions

Fields: cluster_diversity, ic_count, institution_count

Fields: first_award_year, last_award_year

Fields: ics (ARRAY), activities (ARRAY), institutions (ARRAY)

Fields: cluster_profile (ARRAY<STRUCT>) - awards/funding per cluster

Total Funding Represented: $934 billion

Institution Cards:

institution_cards_phase2 - 2,599 Organizations

Fields: PRIMARY_ORG, primary_state

Fields: total_awards, total_funding_millions

Fields: cluster_count, ic_count, activity_count

Fields: first_award_year, last_award_year

Fields: cluster_specialization (ARRAY<STRUCT>) - top 15 clusters

Total Funding Represented: $576 billion

Example Specializations:

Boston Children's Hospital: Neuroscience (33% specialization)

MD Anderson: Clinical/Translational (29% specialization)

IC Cards:

ic_cards_phase2 - 45 NIH Institutes/Centers

Fields: ADMINISTERING_IC, total_awards, total_funding_millions

Fields: portfolio_diversity, activity_count

Fields: first_year, last_year

Fields: portfolio_distribution (ARRAY<STRUCT>) - funding by cluster

Total Portfolio: $579 billion

Top ICs by Funding:

HD (NICHD): $283B - Stroke/Patient research

DE (NIDCR): $155B - Assay/Detection methods

GM (NIGMS): $18.5B - Viral/Infection research

Export Tables (For GCS Flattening)
pi_cards_export - Flattened PI cards with JSON arrays

institution_cards_export - Flattened institution cards

ic_cards_export - Flattened IC cards

Dataset: nih_data
Purpose: Raw grant text data for analysis

Tables:

grant_text - Full grant text corpus

grant_text_sample - Sample for testing/development

Dataset: nih_exporter
Purpose: Development and testing environment

Tables:

awards_250k_for_clustering - Phase 2 clustering input dataset

clustered_50k_sample - Phase 1 sample clustering results

clustered_50k_semantic - Semantic clustering tests

clustered_50k_with_viz - Visualization-ready Phase 1 data

Dataset: nih_topic_maps (Empty - Reserved)
Purpose: Topic mapping and domain analysis (NEXT PHASE)

Planned Tables:

cluster_summaries - Cluster-level topic summaries

topic_taxonomy - Hierarchical topic organization

domain_keywords - Domain-specific keyword extraction

Data Lineage
Phase 1: Initial Clustering (Complete - Archived)
text
Raw NIH ExPORTER Data (1985-2024)
    ↓
Sample Selection (50k awards)
    ↓
Embedding Generation (PubMedBERT, TF-IDF)
    → gs://...nih-embeddings/phase1/
    ↓
Hierarchical Clustering (74 clusters)
    → nih_exporter.clustered_50k_*
    ↓
Grant Cards v1.3 Production
    → nih_analytics.grant_cards_v1_3_production
Phase 2: Full Dataset Clustering (Complete)
text
Full Dataset (253,487 awards)
    ↓
Embedding Generation (scaled pipeline)
    → gs://...nih-embeddings/phase2/
    ↓
Hierarchical Clustering (VM-based, ~100-250 clusters)
    → nih_analytics.phase2_cluster_assignments
    ↓
Grant Cards v2.0 Complete (cluster assignments merged)
    → nih_analytics.grant_cards_v2_0_complete
    ↓
Grant Scorecards v2 (agency + IC + funding dimensions)
    → nih_analytics.grant_scorecard_v2
Phase 3: Entity Card Aggregation (Complete - Dec 5, 2025)
text
Grant Cards v2.0 + Phase 2 Cluster Assignments
    ↓
PI Aggregation (split by semicolon-delimited pi_names)
    → nih_processed.pi_cards_phase2 (65,031 PIs)
    ↓
Institution Aggregation (by PRIMARY_ORG)
    → nih_processed.institution_cards_phase2 (2,599 orgs)
    ↓
IC Aggregation (by ADMINISTERING_IC)
    → nih_processed.ic_cards_phase2 (45 ICs)
    ↓
Export to GCS (JSON with flattened arrays)
    → gs://...nih-processed/entity-cards/
Phase 4: Topic Analysis (Next - PENDING)
text
Phase 2 Cluster Assignments + Grant Cards
    ↓
Cluster-Level Topic Summaries
    → nih_topic_maps.cluster_summaries
    ↓
Domain Taxonomy Mapping
    → nih_topic_maps.topic_taxonomy
    ↓
Keyword Extraction & TF-IDF per Cluster
    → nih_topic_maps.domain_keywords
    ↓
Specialized Reports
    → PI collaboration networks
    → Institutional research profiles
    → IC strategic portfolio analysis
Key Metrics
Data Volumes
Total Awards Clustered: 253,487 (Phase 2)

Unique Clusters: ~100-250 (hierarchical structure)

PIs Profiled: 65,031 unique investigators

Institutions: 2,599 organizations

NIH ICs: 45 institutes/centers (27 major ICs)

Fiscal Years Coverage: 1985-2024 (40 years)

Total Funding Analyzed: $934 billion (PI cards aggregate)

Entity Card Statistics (Dec 5, 2025)
PI Cards: 65,031 records

Avg awards per PI: 3.9

Avg funding per PI: $14.4M

Top PI cluster diversity: 21 clusters

Institution Cards: 2,599 records

Avg awards per institution: 97.5

Avg funding per institution: $221.6M

Top institution: Boston Children's Hospital ($2.79B)

IC Cards: 45 records

Avg awards per IC: 5,633

Avg funding per IC: $12.9B

Top IC: NICHD - HD ($283B)

Storage
GCS Total: ~15 GiB across NIH buckets

Embeddings: 12.94 GiB

Raw data: 1.93 GiB

Processed: Ready for exports

BigQuery Storage: ~8-12 GB (compressed)

nih_analytics: ~6 GB (grant cards + clustering)

nih_processed: ~2 GB (entity cards)

Cloud Shell: 1.2 GB / 4.8 GB (25% utilization)

Cluster Distribution Highlights
Largest Cluster: "Stroke / Patients / Motor" (Neuroscience domain)

Most Represented Domain: Neuroscience & Behavior

Emerging Domains: Infectious Disease & Immunity, Cancer Research

Cross-IC Clusters: Multiple clusters span 15+ ICs

Table Schemas Reference
grant_cards_v2_0_complete
text
CORE_PROJECT_NUM (STRING) - Primary key
ADMINISTERING_IC (STRING) - NIH IC code
ACTIVITY (STRING) - Award mechanism (R01, R21, etc.)
type1_title (STRING) - Project title
contact_pi_name (STRING) - Lead PI
all_pi_names (STRING) - Semicolon-delimited PI list
type1_project_terms (STRING) - Project keywords
type1_nih_categories (STRING) - NIH-assigned categories
FIRST_FISCAL_YEAR (INTEGER) - First award year
LAST_FISCAL_YEAR (INTEGER) - Last award year
duration_years (INTEGER) - Project duration
TOTAL_LIFETIME_FUNDING (FLOAT) - Total funding (dollars)
TOTAL_DIRECT_COSTS (FLOAT) - Direct costs
TOTAL_INDIRECT_COSTS (FLOAT) - Indirect costs
AVG_ANNUAL_FUNDING (FLOAT) - Average per year
is_mpi (BOOLEAN) - Multiple PI flag
pi_count (INTEGER) - Number of PIs
PRIMARY_ORG (STRING) - Primary institution
PRIMARY_STATE (STRING) - State abbreviation
IS_MULTISITE (BOOLEAN) - Multi-site flag
DISTINCT_ORGANIZATIONS (INTEGER) - Org count
cluster_id (INTEGER) - Phase 2 cluster ID
cluster_label (STRING) - Phase 2 cluster label
domain_name (STRING) - Research domain
phase2_cluster_assignments
text
CORE_PROJECT_NUM (STRING) - Links to grant cards
cluster_id (INTEGER) - Cluster identifier
cluster_label (STRING) - Human-readable cluster name
domain_id (STRING) - Domain code
domain_name (STRING) - Domain name
umap_x (FLOAT) - UMAP X coordinate
umap_y (FLOAT) - UMAP Y coordinate
ic_cluster_size (INTEGER) - Awards in cluster
assignment_method (STRING) - Clustering algorithm used
pi_cards_phase2
text
pi_name (STRING) - Principal Investigator name
total_awards (INTEGER) - Total award count
total_funding_millions (FLOAT) - Total funding ($M)
avg_annual_funding_millions (FLOAT) - Avg annual funding
cluster_diversity (INTEGER) - Unique clusters PI participates in
ic_count (INTEGER) - Unique ICs funded by
institution_count (INTEGER) - Unique institutions affiliated with
first_award_year (INTEGER) - Career start year
last_award_year (INTEGER) - Most recent award year
ics (ARRAY<STRING>) - List of ICs (up to 10)
activities (ARRAY<STRING>) - Award mechanisms (up to 10)
institutions (ARRAY<STRING>) - Affiliations (up to 5)
cluster_profile (ARRAY<STRUCT>) - Per-cluster breakdown:
  - cluster_label (STRING)
  - domain_name (STRING)
  - awards_in_cluster (INTEGER)
  - funding_in_cluster_millions (FLOAT)
  - pct_of_awards (FLOAT) - % of PI's total awards
institution_cards_phase2
text
PRIMARY_ORG (STRING) - Institution name
primary_state (STRING) - State abbreviation
total_awards (INTEGER) - Total awards
total_funding_millions (FLOAT) - Total funding ($M)
cluster_count (INTEGER) - Unique clusters
ic_count (INTEGER) - ICs represented
activity_count (INTEGER) - Award types
first_award_year (INTEGER) - First award year
last_award_year (INTEGER) - Most recent year
cluster_specialization (ARRAY<STRUCT>) - Top 15 clusters:
  - cluster_label (STRING)
  - domain_name (STRING)
  - awards_in_cluster (INTEGER)
  - funding_in_cluster_millions (FLOAT)
  - specialization_pct (FLOAT) - % of institution's portfolio
ic_cards_phase2
text
ADMINISTERING_IC (STRING) - IC code (e.g., CA, GM, HD)
total_awards (INTEGER) - Total awards administered
total_funding_millions (FLOAT) - Total funding ($M)
portfolio_diversity (INTEGER) - Unique clusters in portfolio
activity_count (INTEGER) - Award mechanisms used
first_year (INTEGER) - First award year
last_year (INTEGER) - Most recent year
portfolio_distribution (ARRAY<STRUCT>) - Funding by cluster:
  - cluster_label (STRING)
  - domain_name (STRING)
  - awards_in_cluster (INTEGER)
  - funding_in_cluster_millions (FLOAT)
  - pct_of_budget (FLOAT) - % of IC's total budget
Maintenance & Operations
Daily Operations
Monitor Cloud Shell disk usage (keep <50%) - Currently 25%

Check BigQuery job logs for errors

Verify data pipeline health

Weekly Tasks
Archive temporary exports to GCS

Clean Cloud Shell cache directories

Review BigQuery query costs

Update entity cards with new award data (if needed)

Monthly Tasks
Consolidate legacy GCS buckets (nih-analytics-*)

Refresh grant scorecards with new fiscal year data

Review cluster assignments for outliers

Archive old table versions to save costs

Quarterly Tasks
Full data quality audit

Cost optimization review (storage, compute)

Documentation updates (THIS FILE)

Strategic analysis refresh (PI networks, IC portfolios)

Cost Optimization
Current Strategy
Archive infrequently accessed data to Nearline/Coldline storage classes

Use BigQuery partitioning for time-series queries (fiscal year)

Compress large exports (Parquet, GZIP for JSON)

Delete temporary tables after 30 days

Keep Cloud Shell usage under 50% to avoid performance degradation

Estimated Monthly Costs
GCS Storage: ~$0.30-0.40 (15GB Standard class)

BigQuery Storage: ~$0.20 (10GB active + long-term)

BigQuery Queries: ~$5-10 (variable based on analysis workload)

Cloud Shell: Free (within 5GB home directory limit)

Compute Engine: $0 (VMs spun down after clustering)

Total: ~$6-11/month (operational baseline)

Cost Reduction Opportunities
Move Phase 1 data to Nearline storage (50% savings)

Delete deprecated grant card versions (v1.4, v1.5)

Consolidate duplicate ExPORTER linktables

Use partitioned tables for large time-series queries

Access Patterns & Query Optimization
High Frequency (Weekly+)
nih_analytics.grant_cards_v2_0_complete - Production grant cards

nih_analytics.grant_scorecard_v2 - Scorecard analytics

nih_analytics.phase2_cluster_assignments - Cluster lookups

nih_processed.pi_cards_phase2 - PI profile queries

nih_processed.institution_cards_phase2 - Institution analytics

Medium Frequency (Monthly)
nih_processed.ic_cards_phase2 - IC portfolio analysis

nih_analytics.cluster_hierarchy_complete - Hierarchy navigation

nih_data.grant_text - Full-text search (when needed)

Low Frequency (Quarterly+)
Historical grant card versions (v1.3, v1.6_backup)

Phase 1 clustering outputs

Raw ExPORTER data (projects, abstracts, patents)

Security & Access Control
Service Accounts
Default Compute Engine service account (VM clustering)

BigQuery Data Editor role for ETL pipelines

Storage Admin role for GCS bucket management

User Access
Project Owner: conroyri

Location: Cloud Shell (od-cl-odss-conroyri-f75a project)

Data Privacy
All data is de-identified public NIH data

No PII, PHI, or confidential information

Safe for external collaboration and publication

Next Steps & Roadmap
Immediate (Week of Dec 5, 2025)
Export Entity Cards to GCS (READY)

Run GCS export script (flattened JSON format)

Estimated time: 5-10 minutes

Output: gs://...nih-processed/entity-cards/{pi,ic,institutions}/

Generate Cluster Summaries (HIGH PRIORITY)

Create cluster-level topic summaries

Aggregate: awards, funding, ICs, institutions per cluster

Extract: top keywords, representative projects

Output: nih_topic_maps.cluster_summaries

Update Project Documentation

THIS FILE (current update)

Update GitHub README with Phase 2/3 status

Generate data dictionary for entity cards

Create visual dashboard documentation

Short-Term (Next 2 Weeks)
Topic/Domain Analysis

Extract cluster-level keywords using TF-IDF

Map clusters to NIH Strategic Plan priorities

Identify emerging research trends by fiscal year

Generate domain taxonomy visualization data

Specialized Reports

PI Collaboration Networks:

Analyze multi-PI awards by cluster

Identify collaboration hubs and bridges

Track PI mobility across institutions

Institutional Research Profiles:

Define institutional "signature" clusters

Track cluster specialization trends over time

Benchmark institutions within domains

IC Strategic Portfolio Analysis:

Compare IC cluster distributions

Identify cross-IC collaboration opportunities

Track IC portfolio evolution (2000-2024)

Consolidate GCS Buckets

Merge nih-analytics-embeddings into main embeddings bucket

Merge nih-analytics-exports into processed bucket

Delete empty buckets after verification

Medium-Term (Next Month)
Visualization & Dashboard Development

Interactive cluster map (UMAP visualization)

PI profile pages with cluster timeline

Institution comparison tool

IC portfolio dashboard

Data Quality & Validation

Audit cluster assignments for edge cases

Validate PI name disambiguation accuracy

Check institution name standardization

Review multi-site award handling

External Collaboration Prep

Export public-facing datasets

Generate API documentation

Create sample queries and use cases

Prepare methodology documentation

Long-Term (Next Quarter)
Temporal Analysis

Track cluster evolution over fiscal years

Identify emerging vs. declining research areas

Analyze funding trend correlations with policy changes

Predictive Analytics

Award success prediction models

PI career trajectory analysis

Institutional research direction forecasting

Integration & APIs

REST API for grant card queries

Cluster recommendation system for new awards

Real-time NIH ExPORTER data pipeline

Technical Details
BigQuery Regions
Primary: us-central1 (Iowa)

Dataset Locations: US (multi-region)

Note: Some legacy tables in US region, new tables in us-central1

Cloud Shell Configuration
Machine Type: e2-medium (2 vCPU, 4GB RAM)

Disk: 5GB persistent home directory

Location: us-central1

Session Timeout: 20 minutes inactive, 12 hours max

VM Configuration (Clustering - Shut Down)
Machine Type: n1-highmem-16 (16 vCPU, 104GB RAM)

GPU: Optional Tesla T4 for embedding generation

Disk: 200GB SSD

Status: Deleted after Phase 2 completion (cost savings)

Contact & Resources
Project Information
Project ID: od-cl-odss-conroyri-f75a

Region: us-central1

Primary Dataset: nih_analytics

Entity Cards Dataset: nih_processed

Git Repository: ~/nih-topic-maps/.git

Key Files
This Documentation: ~/nih-topic-maps/docs/PROJECT_STRUCTURE_*.md

Cleanup Script: ~/cleanup.sh

Entity Card Script: ~/entity_cards_rebuild.sh

Export Script: ~/entity_cards_export.sh (PENDING)

External Resources
NIH ExPORTER: https://reporter.nih.gov/

NIH RePORTER API: https://api.reporter.nih.gov/

PubMedBERT: https://huggingface.co/microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract

UMAP Documentation: https://umap-learn.readthedocs.io/

Change Log
2025-12-05 10:35 AM
Phase 2 clustering complete (253,487 awards)

Grant cards v2.0 updated with cluster assignments

Entity cards complete: PI (65,031), Institution (2,599), IC (45)

Cloud Shell workspace organized (25% disk usage)

GCS bucket structure standardized (phase1/phase2 folders)

Next: Cluster summaries, topic analysis, specialized reports

2025-12-04
Phase 2 clustering VM shut down (cost optimization)

Cluster assignments exported to BigQuery

Grant cards updated with cluster metadata

Planned: Entity card rebuild with Phase 2 data

2025-12-02
Phase 2 clustering job completed on VM

UMAP dimensionality reduction for visualization

Cluster hierarchy validation and labeling

2025-11-28
Phase 1 clustering archived

VM provisioned for Phase 2 (n1-highmem-16)

Embedding generation scaled to 253k awards

Document Version: 3.0
Generated: December 5, 2025, 10:35 AM EST
Next Review: January 5, 2026
Status: Phase 2 Complete | Entity Cards Complete | Topic Analysis Next
