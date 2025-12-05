#!/usr/bin/env python3
"""
Load ExPORTER data with schema conflict resolution
"""

from google.cloud import bigquery
import pandas as pd

PROJECT_ID = 'od-cl-odss-conroyri-f75a'
DATASET_ID = 'nih_exporter'
BUCKET = 'gs://od-cl-odss-conroyri-nih-embeddings/exporter'

client = bigquery.Client(project=PROJECT_ID)

print("="*70)
print("Loading NIH ExPORTER to BigQuery (with schema fixes)")
print("="*70)

# Strategy: Load each table year by year, let BigQuery merge schemas
tables = {
    'projects': 'projects_parquet',
    'abstracts': 'abstracts_parquet',
    'linktables': 'linktables_parquet'
}

for table_name, folder in tables.items():
    print(f"\n{'='*70}")
    print(f"Loading {table_name.upper()}")
    print(f"{'='*70}")
    
    for year in range(1990, 2025):
        uri = f'{BUCKET}/{folder}/YEAR={year}/{table_name}_{year}.parquet'
        
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.PARQUET,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND if year > 1990 else bigquery.WriteDisposition.WRITE_TRUNCATE,
            autodetect=True,
            schema_update_options=[
                bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION,
                bigquery.SchemaUpdateOption.ALLOW_FIELD_RELAXATION
            ]
        )
        
        try:
            job = client.load_table_from_uri(
                uri,
                f'{PROJECT_ID}.{DATASET_ID}.{table_name}',
                job_config=job_config
            )
            job.result()
            print(f"  ✓ {year}: {job.output_rows:,} rows", end='\r')
        except Exception as e:
            print(f"  ⚠️  {year}: {str(e)[:100]}")
    
    # Get final count
    query = f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}`"
    result = client.query(query).result()
    count = list(result)[0]['cnt']
    print(f"\n  ✓ Total {table_name}: {count:,} rows")

print("\n" + "="*70)
print("✓ ALL DATA LOADED!")
print("="*70)

# Final verification
print("\nFinal counts:")
for table in ['projects', 'abstracts', 'linktables', 'patents']:
    try:
        query = f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{DATASET_ID}.{table}`"
        result = client.query(query).result()
        count = list(result)[0]['cnt']
        print(f"  {table}: {count:,} rows")
    except:
        print(f"  {table}: not loaded yet")
