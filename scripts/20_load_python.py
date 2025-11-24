#!/usr/bin/env python3
"""
Load all ExPORTER data to BigQuery using Python
"""

from google.cloud import bigquery

PROJECT_ID = 'od-cl-odss-conroyri-f75a'
DATASET_ID = 'nih_exporter'
BUCKET = 'gs://od-cl-odss-conroyri-nih-embeddings/exporter'

client = bigquery.Client(project=PROJECT_ID)

print("="*70)
print("Loading NIH ExPORTER to BigQuery")
print("="*70)

# PROJECTS
print("\nLoading PROJECTS...")
uris = [f'{BUCKET}/projects_parquet/YEAR={year}/projects_{year}.parquet' 
        for year in range(1990, 2025)]

job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.PARQUET,
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    autodetect=True
)

job = client.load_table_from_uri(
    uris,
    f'{PROJECT_ID}.{DATASET_ID}.projects',
    job_config=job_config
)
job.result()
print(f"✓ Projects: {job.output_rows:,} rows")

# ABSTRACTS
print("\nLoading ABSTRACTS...")
uris = [f'{BUCKET}/abstracts_parquet/YEAR={year}/abstracts_{year}.parquet' 
        for year in range(1990, 2025)]

job = client.load_table_from_uri(
    uris,
    f'{PROJECT_ID}.{DATASET_ID}.abstracts',
    job_config=job_config
)
job.result()
print(f"✓ Abstracts: {job.output_rows:,} rows")

# LINKTABLES
print("\nLoading LINKTABLES...")
uris = [f'{BUCKET}/linktables_parquet/YEAR={year}/linktables_{year}.parquet' 
        for year in range(1990, 2025)]

job = client.load_table_from_uri(
    uris,
    f'{PROJECT_ID}.{DATASET_ID}.linktables',
    job_config=job_config
)
job.result()
print(f"✓ Linktables: {job.output_rows:,} rows")

# PATENTS (already loaded)
print("\n✓ Patents: already loaded")

print("\n" + "="*70)
print("✓ ALL DATA LOADED!")
print("="*70)

# Verify
print("\nVerifying tables...")
for table in ['projects', 'abstracts', 'linktables', 'patents']:
    query = f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{DATASET_ID}.{table}`"
    result = client.query(query).result()
    count = list(result)[0]['cnt']
    print(f"  {table}: {count:,} rows")
