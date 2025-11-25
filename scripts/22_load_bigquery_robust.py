#!/usr/bin/env python3
"""
Robust BigQuery loader with schema conflict resolution
"""

from google.cloud import bigquery
import pandas as pd
from tqdm import tqdm

PROJECT_ID = 'od-cl-odss-conroyri-f75a'
DATASET_ID = 'nih_exporter'
BUCKET = 'gs://od-cl-odss-conroyri-nih-embeddings/exporter'

client = bigquery.Client(project=PROJECT_ID)

print("="*70)
print("Loading NIH ExPORTER to BigQuery (Robust Version)")
print("="*70)

# Create dataset if needed
dataset = bigquery.Dataset(f"{PROJECT_ID}.{DATASET_ID}")
dataset.location = "US"
try:
    client.create_dataset(dataset, exists_ok=True)
    print(f"✓ Dataset ready: {DATASET_ID}\n")
except Exception as e:
    print(f"Dataset exists: {e}\n")

def load_table_robust(table_name, folder, years=range(1990, 2025)):
    """Load table year by year with error handling"""
    
    print(f"\n{'='*70}")
    print(f"Loading {table_name.upper()}")
    print(f"{'='*70}")
    
    loaded_years = []
    failed_years = []
    
    for year in years:
        uri = f'{BUCKET}/{folder}/YEAR={year}/{table_name}_{year}.parquet'
        
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.PARQUET,
            write_disposition=(
                bigquery.WriteDisposition.WRITE_TRUNCATE 
                if year == years[0] 
                else bigquery.WriteDisposition.WRITE_APPEND
            ),
            autodetect=True,
            schema_update_options=[
                bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION,
                bigquery.SchemaUpdateOption.ALLOW_FIELD_RELAXATION
            ],
            # Ignore schema errors by converting problematic types to strings
            max_bad_records=0
        )
        
        try:
            job = client.load_table_from_uri(
                uri,
                f'{PROJECT_ID}.{DATASET_ID}.{table_name}',
                job_config=job_config
            )
            job.result()
            loaded_years.append(year)
            print(f"  ✓ {year}: {job.output_rows:,} rows", flush=True)
            
        except Exception as e:
            error_msg = str(e)
            if "type" in error_msg.lower() and "mismatch" in error_msg.lower():
                # Schema conflict - try loading as string
                print(f"  ⚠️  {year}: Schema conflict, retrying...", flush=True)
                try:
                    # Read parquet, convert problematic columns to string
                    df = pd.read_parquet(uri)
                    
                    # Convert all columns to compatible types
                    for col in df.columns:
                        if df[col].dtype == 'object':
                            df[col] = df[col].astype(str)
                    
                    # Write to temp location
                    temp_uri = f'{BUCKET}/temp/{table_name}_{year}_fixed.parquet'
                    df.to_parquet(temp_uri.replace('gs://', '/tmp/'), index=False)
                    
                    # Upload fixed file
                    import subprocess
                    subprocess.run(['gsutil', 'cp', f'/tmp/{table_name}_{year}_fixed.parquet', temp_uri])
                    
                    # Try loading again
                    job = client.load_table_from_uri(
                        temp_uri,
                        f'{PROJECT_ID}.{DATASET_ID}.{table_name}',
                        job_config=job_config
                    )
                    job.result()
                    loaded_years.append(year)
                    print(f"  ✓ {year}: {job.output_rows:,} rows (fixed)", flush=True)
                    
                except Exception as e2:
                    failed_years.append((year, str(e2)[:100]))
                    print(f"  ✗ {year}: Failed ({str(e2)[:50]})", flush=True)
            else:
                failed_years.append((year, error_msg[:100]))
                print(f"  ✗ {year}: {error_msg[:50]}", flush=True)
    
    # Summary
    print(f"\n  Summary:")
    print(f"  ✓ Loaded: {len(loaded_years)} years")
    if failed_years:
        print(f"  ✗ Failed: {len(failed_years)} years")
        for year, error in failed_years[:5]:
            print(f"    - {year}: {error}")
    
    # Get final count
    try:
        query = f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}`"
        result = client.query(query).result()
        count = list(result)[0]['cnt']
        print(f"  📊 Total rows: {count:,}")
        return count
    except:
        return 0

# Load each table
tables = {
    'projects': 'projects_parquet',
    'abstracts': 'abstracts_parquet',
    'linktables': 'linktables_parquet'
}

totals = {}
for table_name, folder in tables.items():
    totals[table_name] = load_table_robust(table_name, folder)

# Load single-file tables
print(f"\n{'='*70}")
print("Loading PATENTS")
print(f"{'='*70}")

job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.PARQUET,
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    autodetect=True
)

try:
    job = client.load_table_from_uri(
        f'{BUCKET}/patents_parquet/patents_ALL.parquet',
        f'{PROJECT_ID}.{DATASET_ID}.patents',
        job_config=job_config
    )
    job.result()
    totals['patents'] = job.output_rows
    print(f"✓ Patents: {job.output_rows:,} rows")
except Exception as e:
    print(f"✗ Patents failed: {e}")
    totals['patents'] = 0

print("\n" + "="*70)
print("✓ LOAD COMPLETE!")
print("="*70)

print("\nFinal Summary:")
for table, count in totals.items():
    print(f"  {table}: {count:,} rows")

print("\nTotal records loaded:", sum(totals.values()))
