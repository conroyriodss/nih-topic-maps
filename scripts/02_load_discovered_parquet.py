#!/usr/bin/env python3
"""
Load NIH Parquet files to BigQuery - CORRECTED
Project: od-cl-odss-conroyri-f75a
"""

from google.cloud import bigquery, storage
import sys
import re

PROJECT_ID = "od-cl-odss-conroyri-f75a"
DATASET_ID = "nih_data"
BUCKET_NAME = "od-cl-odss-conroyri-nih-raw-data"

client = bigquery.Client(project=PROJECT_ID)
storage_client = storage.Client(project=PROJECT_ID)

def extract_year_from_path(path):
    """Extract year from path like 'abstracts/YEAR=1990/abstracts_1990.parquet'"""
    match = re.search(r'YEAR=(\d{4})', path)
    if match:
        return match.group(1)
    
    # Try filename
    match = re.search(r'_(\d{4})\.parquet', path)
    if match:
        return match.group(1)
    
    return None

def load_parquet(gcs_uri, table_id):
    """Load Parquet file to BigQuery"""
    
    print(f"\nLoading: {gcs_uri}")
    print(f"Target:  {table_id}")
    
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )
    
    try:
        load_job = client.load_table_from_uri(gcs_uri, table_id, job_config=job_config)
        load_job.result()
        
        table = client.get_table(table_id)
        print(f"✓ Loaded {table.num_rows:,} rows")
        return table.num_rows
    except Exception as e:
        print(f"❌ Error: {e}")
        return 0

def main():
    """Main loading function"""
    
    print(f"\n{'='*70}")
    print("Loading NIH Parquet Files to BigQuery")
    print(f"Project: {PROJECT_ID}")
    print(f"{'='*70}\n")
    
    bucket = storage_client.bucket(BUCKET_NAME)
    all_blobs = list(bucket.list_blobs())
    parquet_files = [b for b in all_blobs if b.name.endswith('.parquet')]
    
    print(f"Found {len(parquet_files)} Parquet files\n")
    
    # Categorize files
    projects_files = []
    abstracts_files = []
    linktables_files = []
    patents_files = []
    clinical_files = []
    
    for blob in parquet_files:
        path = blob.name
        if 'project' in path.lower() and 'YEAR=' in path:
            projects_files.append(path)
        elif 'abstract' in path.lower() and 'YEAR=' in path:
            abstracts_files.append(path)
        elif 'linktable' in path.lower() and 'YEAR=' in path:
            linktables_files.append(path)
        elif 'patent' in path.lower():
            patents_files.append(path)
        elif 'clinical' in path.lower():
            clinical_files.append(path)
    
    print(f"Categorized:")
    print(f"  Projects: {len(projects_files)}")
    print(f"  Abstracts: {len(abstracts_files)}")
    print(f"  Linktables: {len(linktables_files)}")
    print(f"  Patents: {len(patents_files)}")
    print(f"  Clinical Studies: {len(clinical_files)}")
    
    total_rows = 0
    
    # Load projects
    if projects_files:
        print(f"\n{'='*70}")
        print("Loading Projects")
        print(f"{'='*70}")
        
        for path in sorted(projects_files):
            year = extract_year_from_path(path)
            if year:
                table_id = f"{PROJECT_ID}.{DATASET_ID}.projects_fy{year}"
                gcs_uri = f"gs://{BUCKET_NAME}/{path}"
                rows = load_parquet(gcs_uri, table_id)
                total_rows += rows
    
    # Load abstracts
    if abstracts_files:
        print(f"\n{'='*70}")
        print("Loading Abstracts")
        print(f"{'='*70}")
        
        for path in sorted(abstracts_files):
            year = extract_year_from_path(path)
            if year:
                table_id = f"{PROJECT_ID}.{DATASET_ID}.abstracts_fy{year}"
                gcs_uri = f"gs://{BUCKET_NAME}/{path}"
                rows = load_parquet(gcs_uri, table_id)
                total_rows += rows
    
    # Load linktables (publications)
    if linktables_files:
        print(f"\n{'='*70}")
        print("Loading Link Tables (Publications)")
        print(f"{'='*70}")
        
        for path in sorted(linktables_files):
            year = extract_year_from_path(path)
            if year:
                table_id = f"{PROJECT_ID}.{DATASET_ID}.publications_fy{year}"
                gcs_uri = f"gs://{BUCKET_NAME}/{path}"
                rows = load_parquet(gcs_uri, table_id)
                total_rows += rows
    
    # Load patents
    if patents_files:
        print(f"\n{'='*70}")
        print("Loading Patents")
        print(f"{'='*70}")
        
        for path in patents_files:
            table_id = f"{PROJECT_ID}.{DATASET_ID}.patents_all"
            gcs_uri = f"gs://{BUCKET_NAME}/{path}"
            rows = load_parquet(gcs_uri, table_id)
            total_rows += rows
    
    # Load clinical studies
    if clinical_files:
        print(f"\n{'='*70}")
        print("Loading Clinical Studies")
        print(f"{'='*70}")
        
        for path in clinical_files:
            table_id = f"{PROJECT_ID}.{DATASET_ID}.clinical_studies_all"
            gcs_uri = f"gs://{BUCKET_NAME}/{path}"
            rows = load_parquet(gcs_uri, table_id)
            total_rows += rows
    
    print(f"\n{'='*70}")
    print("LOADING COMPLETE")
    print(f"{'='*70}")
    print(f"Total rows loaded: {total_rows:,}")
    print(f"\nTables created in: {PROJECT_ID}.{DATASET_ID}")
    print(f"\nNext step: Create unified tables")
    print(f"  python3 scripts/03_create_unified_tables.py")

if __name__ == "__main__":
    main()
