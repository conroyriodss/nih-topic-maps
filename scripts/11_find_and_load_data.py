#!/usr/bin/env python3
"""
Find ExPORTER data in GCS and load to BigQuery
"""

from google.cloud import bigquery
import subprocess
import re

PROJECT_ID = 'od-cl-odss-conroyri-f75a'
DATASET_ID = 'nih_exporter'
BUCKET = 'od-cl-odss-conroyri-nih-embeddings'

client = bigquery.Client(project=PROJECT_ID)

print("\n" + "="*70)
print("# Finding NIH ExPORTER Data")
print("="*70 + "\n")

# Search for CSV files in bucket
print("Searching bucket for ExPORTER files...")
result = subprocess.run(
    ['gsutil', 'ls', '-r', f'gs://{BUCKET}/'],
    capture_output=True,
    text=True
)

all_files = result.stdout.strip().split('\n')
print(f"Found {len(all_files)} total files")

# Find CSV files that look like ExPORTER data
csv_files = [f for f in all_files if f.endswith('.csv')]
print(f"\nFound {len(csv_files)} CSV files:")

# Group by type
file_groups = {}
for f in csv_files[:20]:  # Show first 20
    filename = f.split('/')[-1]
    print(f"  {filename}")
    
    # Categorize
    if 'PRJ' in filename or 'project' in filename.lower():
        file_groups.setdefault('projects', []).append(f)
    elif 'PRJABS' in filename or 'abstract' in filename.lower():
        file_groups.setdefault('abstracts', []).append(f)
    elif 'PRJPUB' in filename or 'publication' in filename.lower():
        file_groups.setdefault('publications', []).append(f)

print(f"\n✓ Categorized into {len(file_groups)} types")

# Load the most recent projects file
if 'projects' in file_groups and file_groups['projects']:
    print("\nLoading PROJECTS data...")
    projects_file = file_groups['projects'][0]  # Take first/most recent
    
    table_id = f'{PROJECT_ID}.{DATASET_ID}.projects'
    
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    
    try:
        load_job = client.load_table_from_uri(
            projects_file,
            table_id,
            job_config=job_config
        )
        load_job.result()
        
        table = client.get_table(table_id)
        print(f"✓ Loaded projects: {table.num_rows:,} rows")
    except Exception as e:
        print(f"❌ Error: {e}")

# Load abstracts
if 'abstracts' in file_groups and file_groups['abstracts']:
    print("\nLoading ABSTRACTS data...")
    abstracts_file = file_groups['abstracts'][0]
    
    table_id = f'{PROJECT_ID}.{DATASET_ID}.abstracts'
    
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    
    try:
        load_job = client.load_table_from_uri(
            abstracts_file,
            table_id,
            job_config=job_config
        )
        load_job.result()
        
        table = client.get_table(table_id)
        print(f"✓ Loaded abstracts: {table.num_rows:,} rows")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "="*70)
print("DATA LOAD COMPLETE")
print("="*70)
