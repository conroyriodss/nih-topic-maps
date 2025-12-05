#!/usr/bin/env python3
"""
Load only the projects table
"""

from google.cloud import bigquery

PROJECT_ID = 'od-cl-odss-conroyri-f75a'
DATASET_ID = 'nih_exporter'
BUCKET = 'gs://od-cl-odss-conroyri-nih-embeddings/exporter'

client = bigquery.Client(project=PROJECT_ID)

print("="*70)
print("Loading PROJECTS Table")
print("="*70)

total_rows = 0
failed_years = []

for i, year in enumerate(range(1990, 2025)):
    uri = f'{BUCKET}/projects_parquet/YEAR={year}/projects_{year}.parquet'
    
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=(
            bigquery.WriteDisposition.WRITE_TRUNCATE if i == 0 
            else bigquery.WriteDisposition.WRITE_APPEND
        ),
        autodetect=True,
        schema_update_options=[
            bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION,
            bigquery.SchemaUpdateOption.ALLOW_FIELD_RELAXATION
        ]
    )
    
    try:
        job = client.load_table_from_uri(
            uri,
            f'{PROJECT_ID}.{DATASET_ID}.projects',
            job_config=job_config
        )
        job.result()
        total_rows += job.output_rows
        print(f"✓ {year}: {job.output_rows:,} rows (total: {total_rows:,})")
    except Exception as e:
        failed_years.append(year)
        print(f"✗ {year}: {str(e)[:80]}")

print(f"\n{'='*70}")
print(f"✓ Loaded {35 - len(failed_years)}/35 years")
print(f"✓ Total rows: {total_rows:,}")
if failed_years:
    print(f"✗ Failed years: {failed_years}")
print(f"{'='*70}")

# Verify
result = client.query("""
SELECT 
  COUNT(*) as total_grants,
  COUNT(DISTINCT FISCAL_YEAR) as years,
  MIN(FISCAL_YEAR) as min_year,
  MAX(FISCAL_YEAR) as max_year
FROM `od-cl-odss-conroyri-f75a.nih_exporter.projects`
""").result()

for row in result:
    print(f"\n✓ Total Grants: {row['total_grants']:,}")
    print(f"✓ Years: {row['years']} ({row['min_year']}-{row['max_year']})")
