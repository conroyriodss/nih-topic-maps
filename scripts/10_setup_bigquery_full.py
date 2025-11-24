#!/usr/bin/env python3
"""
Complete BigQuery setup for NIH ExPORTER data
Creates dataset and loads all tables from parquet files
"""

from google.cloud import bigquery
import subprocess

PROJECT_ID = 'od-cl-odss-conroyri-f75a'
DATASET_ID = 'nih_exporter'
BUCKET = 'od-cl-odss-conroyri-nih-embeddings'

client = bigquery.Client(project=PROJECT_ID)

print("\n" + "="*70)
print("# Setting Up NIH ExPORTER BigQuery Dataset")
print("="*70 + "\n")

# 1. Create dataset
print("Creating dataset...")
dataset = bigquery.Dataset(f"{PROJECT_ID}.{DATASET_ID}")
dataset.location = "US"
dataset.description = "NIH ExPORTER data (2000-2024)"

try:
    dataset = client.create_dataset(dataset, exists_ok=True)
    print(f"✓ Dataset created: {DATASET_ID}")
except Exception as e:
    print(f"Dataset exists: {e}")

# 2. Check available parquet files
print("\nChecking available parquet files...")
result = subprocess.run(
    ['gsutil', 'ls', f'gs://{BUCKET}/parquet/'],
    capture_output=True,
    text=True
)

files = [line.split('/')[-1] for line in result.stdout.strip().split('\n') if line.endswith('.parquet')]
print(f"✓ Found {len(files)} parquet files:")
for f in files:
    print(f"  - {f}")

# 3. Define table schemas (flexible - will auto-detect from parquet)
tables_to_load = {
    'projects': 'projects.parquet',
    'abstracts': 'abstracts.parquet', 
    'publications': 'publications.parquet',
    'patents': 'patents.parquet',
    'clinical_studies': 'clinical_studies.parquet',
    'project_orgs': 'project_orgs.parquet',
    'link_tables': 'link_tables.parquet'
}

# 4. Load each table
print("\nLoading tables to BigQuery...")
for table_name, parquet_file in tables_to_load.items():
    if parquet_file not in files:
        print(f"⚠️  Skipping {table_name} - file not found")
        continue
    
    print(f"\nLoading {table_name}...")
    gcs_uri = f'gs://{BUCKET}/parquet/{parquet_file}'
    table_id = f'{PROJECT_ID}.{DATASET_ID}.{table_name}'
    
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=True,  # Auto-detect schema from parquet
    )
    
    try:
        load_job = client.load_table_from_uri(
            gcs_uri,
            table_id,
            job_config=job_config
        )
        load_job.result()  # Wait for completion
        
        # Get row count
        table = client.get_table(table_id)
        print(f"✓ Loaded {table_name}: {table.num_rows:,} rows")
        
    except Exception as e:
        print(f"❌ Error loading {table_name}: {e}")

# 5. Verify all tables
print("\n" + "="*70)
print("VERIFICATION")
print("="*70 + "\n")

tables = list(client.list_tables(dataset))
print(f"Tables in {DATASET_ID}:")

for table in tables:
    table_ref = client.get_table(table)
    print(f"\n{table.table_id}:")
    print(f"  Rows: {table_ref.num_rows:,}")
    print(f"  Size: {table_ref.num_bytes / 1024**3:.2f} GB")
    print(f"  Columns: {len(table_ref.schema)}")

# 6. Create useful views
print("\n" + "="*70)
print("Creating Analytical Views")
print("="*70 + "\n")

views = {
    'grants_with_abstracts': """
        SELECT 
            p.*,
            a.ABSTRACT_TEXT,
            a.PROJECT_TERMS
        FROM `{project}.{dataset}.projects` p
        LEFT JOIN `{project}.{dataset}.abstracts` a
            ON p.APPLICATION_ID = a.APPLICATION_ID
    """,
    
    'grants_with_publications': """
        SELECT 
            p.APPLICATION_ID,
            p.PROJECT_TITLE,
            p.IC_NAME,
            p.FISCAL_YEAR,
            p.TOTAL_COST,
            COUNT(DISTINCT pub.PMID) as publication_count
        FROM `{project}.{dataset}.projects` p
        LEFT JOIN `{project}.{dataset}.publications` pub
            ON p.APPLICATION_ID = pub.APPLICATION_ID
        GROUP BY 1,2,3,4,5
    """,
    
    'grants_with_clinical_trials': """
        SELECT 
            p.APPLICATION_ID,
            p.PROJECT_TITLE,
            p.IC_NAME,
            p.FISCAL_YEAR,
            COUNT(DISTINCT cs.CLINICALTRIALS_GOV_ID) as trial_count,
            STRING_AGG(DISTINCT cs.STUDY_STATUS, '; ') as trial_statuses
        FROM `{project}.{dataset}.projects` p
        LEFT JOIN `{project}.{dataset}.clinical_studies` cs
            ON p.APPLICATION_ID = cs.APPLICATION_ID
        GROUP BY 1,2,3,4
    """
}

for view_name, view_sql in views.items():
    view_id = f"{PROJECT_ID}.{DATASET_ID}.{view_name}"
    view_sql_formatted = view_sql.format(project=PROJECT_ID, dataset=DATASET_ID)
    
    view = bigquery.Table(view_id)
    view.view_query = view_sql_formatted
    
    try:
        view = client.create_table(view, exists_ok=True)
        print(f"✓ Created view: {view_name}")
    except Exception as e:
        print(f"⚠️  View {view_name}: {e}")

print("\n" + "="*70)
print("✓ BIGQUERY SETUP COMPLETE!")
print("="*70)
print(f"\nDataset: {PROJECT_ID}.{DATASET_ID}")
print(f"Tables: {len(tables)}")
print("\nReady for analysis!")
