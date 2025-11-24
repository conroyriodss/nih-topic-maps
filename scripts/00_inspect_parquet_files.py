#!/usr/bin/env python3
"""
Inspect and validate NIH Parquet files in GCS
Project: od-cl-odss-conroyri-f75a
"""

from google.cloud import storage
import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path
import json
from collections import defaultdict
import sys

PROJECT_ID = "od-cl-odss-conroyri-f75a"
BUCKET_NAME = "od-cl-odss-conroyri-nih-raw-data"

storage_client = storage.Client(project=PROJECT_ID)

def list_all_files():
    """List all files in the bucket with size and structure"""
    
    print(f"\n{'='*70}")
    print(f"BUCKET CONTENTS: gs://{BUCKET_NAME}")
    print(f"{'='*70}\n")
    
    bucket = storage_client.bucket(BUCKET_NAME)
    blobs = list(bucket.list_blobs())
    
    if not blobs:
        print("❌ Bucket is empty!")
        return []
    
    # Organize by directory
    file_tree = defaultdict(list)
    total_size = 0
    
    for blob in blobs:
        path_parts = blob.name.split('/')
        if len(path_parts) > 1:
            directory = '/'.join(path_parts[:-1])
        else:
            directory = 'root'
        
        file_info = {
            'name': blob.name,
            'size_mb': blob.size / (1024**2),
            'updated': blob.updated,
            'type': blob.name.split('.')[-1] if '.' in blob.name else 'unknown'
        }
        file_tree[directory].append(file_info)
        total_size += blob.size
    
    # Print directory structure
    print(f"Total files: {len(blobs)}")
    print(f"Total size: {total_size / (1024**3):.2f} GB\n")
    
    for directory in sorted(file_tree.keys()):
        files = file_tree[directory]
        dir_size = sum(f['size_mb'] for f in files)
        
        print(f"📁 {directory}/ ({len(files)} files, {dir_size:.1f} MB)")
        
        # Group by file type
        by_type = defaultdict(list)
        for f in files:
            by_type[f['type']].append(f)
        
        for ftype in sorted(by_type.keys()):
            type_files = by_type[ftype]
            type_size = sum(f['size_mb'] for f in type_files)
            print(f"  ├─ .{ftype}: {len(type_files)} files ({type_size:.1f} MB)")
            
            # Show first 5 files
            for i, f in enumerate(sorted(type_files, key=lambda x: x['name'])[:5]):
                prefix = "  │  ├─" if i < min(4, len(type_files)-1) else "  │  └─"
                print(f"{prefix} {Path(f['name']).name} ({f['size_mb']:.1f} MB)")
            
            if len(type_files) > 5:
                print(f"  │  └─ ... and {len(type_files) - 5} more")
        print()
    
    # Return parquet files only
    parquet_files = [blob.name for blob in blobs if blob.name.endswith('.parquet')]
    return parquet_files

def inspect_parquet_file(file_path):
    """Download and inspect a single Parquet file"""
    
    print(f"\n{'='*70}")
    print(f"INSPECTING: {file_path}")
    print(f"{'='*70}\n")
    
    # Download to temp location
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(file_path)
    
    temp_file = f"/tmp/{Path(file_path).name}"
    
    print(f"Downloading to {temp_file}...", end="", flush=True)
    blob.download_to_filename(temp_file)
    print(" ✓")
    
    # Read Parquet metadata
    print("\n--- Parquet Metadata ---")
    parquet_file = pq.ParquetFile(temp_file)
    print(f"Number of row groups: {parquet_file.num_row_groups}")
    print(f"Number of columns: {len(parquet_file.schema)}")
    print(f"Total rows: {parquet_file.metadata.num_rows:,}")
    
    # Read into pandas for detailed inspection
    print("\n--- Loading data sample ---")
    df = pd.read_parquet(temp_file)
    
    print(f"DataFrame shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"Memory usage: {df.memory_usage(deep=True).sum() / (1024**2):.1f} MB")
    
    # Schema
    print("\n--- Column Schema ---")
    print(f"{'Column Name':<40} {'Type':<15} {'Non-Null':<12} {'Null %'}")
    print("-" * 80)
    
    for col in df.columns:
        dtype = str(df[col].dtype)
        non_null = df[col].notna().sum()
        null_pct = (df[col].isna().sum() / len(df)) * 100
        print(f"{col:<40} {dtype:<15} {non_null:>10,}  {null_pct:>6.1f}%")
    
    # Key columns detection
    print("\n--- Key Columns Detected ---")
    key_columns = []
    
    # Common NIH field names
    id_cols = [col for col in df.columns if any(
        x in col.upper() for x in ['APPLICATION_ID', 'APPL_ID', 'PROJECT_NUM', 'CORE_PROJECT']
    )]
    
    title_cols = [col for col in df.columns if any(
        x in col.upper() for x in ['PROJECT_TITLE', 'TITLE']
    )]
    
    abstract_cols = [col for col in df.columns if any(
        x in col.upper() for x in ['ABSTRACT', 'PHR']
    )]
    
    fiscal_cols = [col for col in df.columns if any(
        x in col.upper() for x in ['FISCAL_YEAR', 'FY', 'YEAR']
    )]
    
    ic_cols = [col for col in df.columns if any(
        x in col.upper() for x in ['IC_NAME', 'INSTITUTE', 'CENTER', 'AGENCY']
    )]
    
    cost_cols = [col for col in df.columns if any(
        x in col.upper() for x in ['TOTAL_COST', 'AWARD_AMOUNT', 'FUNDING']
    )]
    
    if id_cols:
        print(f"  ✓ ID columns: {', '.join(id_cols)}")
        key_columns.extend(id_cols)
    if title_cols:
        print(f"  ✓ Title columns: {', '.join(title_cols)}")
    if abstract_cols:
        print(f"  ✓ Abstract columns: {', '.join(abstract_cols)}")
    if fiscal_cols:
        print(f"  ✓ Fiscal year columns: {', '.join(fiscal_cols)}")
    if ic_cols:
        print(f"  ✓ IC/Agency columns: {', '.join(ic_cols)}")
    if cost_cols:
        print(f"  ✓ Cost columns: {', '.join(cost_cols)}")
    
    # Data quality checks
    print("\n--- Data Quality Checks ---")
    
    # Check for ID column
    if id_cols:
        id_col = id_cols[0]
        unique_ids = df[id_col].nunique()
        total_rows = len(df)
        print(f"  Unique IDs: {unique_ids:,} / {total_rows:,} rows", end="")
        if unique_ids == total_rows:
            print(" ✓ (No duplicates)")
        else:
            print(f" ⚠ ({total_rows - unique_ids:,} duplicates)")
    
    # Check text fields
    if title_cols:
        title_col = title_cols[0]
        avg_length = df[title_col].str.len().mean()
        empty = df[title_col].isna().sum()
        print(f"  Title avg length: {avg_length:.0f} chars, {empty:,} empty")
    
    if abstract_cols:
        abstract_col = abstract_cols[0]
        avg_length = df[abstract_col].str.len().mean()
        empty = df[abstract_col].isna().sum()
        print(f"  Abstract avg length: {avg_length:.0f} chars, {empty:,} empty")
    
    # Fiscal year distribution
    if fiscal_cols:
        fy_col = fiscal_cols[0]
        print(f"\n  Fiscal year distribution:")
        fy_dist = df[fy_col].value_counts().sort_index()
        for year, count in fy_dist.items():
            print(f"    FY{year}: {count:,} records")
    
    # Show sample rows
    print("\n--- Sample Data (first 3 rows) ---")
    sample_cols = key_columns[:3] if key_columns else df.columns[:5]
    print(df[sample_cols].head(3).to_string(index=False))
    
    # Clean up
    Path(temp_file).unlink()
    
    return {
        'file': file_path,
        'rows': len(df),
        'columns': list(df.columns),
        'id_columns': id_cols,
        'has_title': bool(title_cols),
        'has_abstract': bool(abstract_cols),
        'fiscal_years': fy_dist.to_dict() if fiscal_cols else {}
    }

def generate_loading_script(parquet_files, metadata_list):
    """Generate optimized BigQuery loading script based on discovered structure"""
    
    print(f"\n{'='*70}")
    print("GENERATING BIGQUERY LOADING SCRIPT")
    print(f"{'='*70}\n")
    
    # Categorize files
    projects_files = []
    abstracts_files = []
    other_files = []
    
    for meta in metadata_list:
        file_path = meta['file']
        filename = Path(file_path).name.lower()
        
        if meta['has_abstract'] and not meta['has_title']:
            abstracts_files.append(meta)
        elif 'abstract' in filename or 'abs' in filename:
            abstracts_files.append(meta)
        elif 'project' in filename or 'prj' in filename:
            projects_files.append(meta)
        else:
            other_files.append(meta)
    
    print(f"Categorized files:")
    print(f"  Projects: {len(projects_files)}")
    print(f"  Abstracts: {len(abstracts_files)}")
    print(f"  Other: {len(other_files)}")
    
    # Generate script
    script_path = "scripts/02_load_discovered_parquet.py"
    
    with open(script_path, 'w') as f:
        f.write('''#!/usr/bin/env python3
"""
Auto-generated script to load discovered Parquet files to BigQuery
Project: od-cl-odss-conroyri-f75a
"""

from google.cloud import bigquery
import sys

PROJECT_ID = "od-cl-odss-conroyri-f75a"
DATASET_ID = "nih_data"
BUCKET_NAME = "od-cl-odss-conroyri-nih-raw-data"

client = bigquery.Client(project=PROJECT_ID)

def load_parquet(gcs_uri, table_id):
    """Load Parquet file to BigQuery"""
    
    print(f"\\nLoading: {gcs_uri}")
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

print("Loading projects files...")
''')
        
        # Add projects files
        for meta in sorted(projects_files, key=lambda x: x['file']):
            file_path = meta['file']
            years = list(meta['fiscal_years'].keys())
            if years:
                year = years[0] if len(years) == 1 else "multi"
                table_name = f"projects_fy{year}"
            else:
                table_name = f"projects_{Path(file_path).stem}"
            
            f.write(f'''
# {file_path} ({meta['rows']:,} rows)
load_parquet(
    "gs://{BUCKET_NAME}/{file_path}",
    f"{{PROJECT_ID}}.{{DATASET_ID}}.{table_name}"
)
''')
        
        f.write('\nprint("\\nLoading abstracts files...")\n')
        
        # Add abstracts files
        for meta in sorted(abstracts_files, key=lambda x: x['file']):
            file_path = meta['file']
            years = list(meta['fiscal_years'].keys())
            if years:
                year = years[0] if len(years) == 1 else "multi"
                table_name = f"abstracts_fy{year}"
            else:
                table_name = f"abstracts_{Path(file_path).stem}"
            
            f.write(f'''
# {file_path} ({meta['rows']:,} rows)
load_parquet(
    "gs://{BUCKET_NAME}/{file_path}",
    f"{{PROJECT_ID}}.{{DATASET_ID}}.{table_name}"
)
''')
        
        f.write('\nprint("\\n✓ All files loaded!")\n')
    
    print(f"✓ Generated: {script_path}")
    print(f"\nTo load all files to BigQuery, run:")
    print(f"  chmod +x {script_path}")
    print(f"  python3 {script_path}")

def main():
    """Main execution"""
    
    print(f"\n{'#'*70}")
    print(f"# NIH Parquet File Inspector")
    print(f"# Project: {PROJECT_ID}")
    print(f"# Bucket: gs://{BUCKET_NAME}")
    print(f"{'#'*70}")
    
    # List all files
    parquet_files = list_all_files()
    
    if not parquet_files:
        print("\n❌ No Parquet files found in bucket!")
        print("Please upload files to gs://od-cl-odss-conroyri-nih-raw-data/")
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print(f"Found {len(parquet_files)} Parquet files")
    print(f"{'='*70}")
    
    # Ask user how many to inspect in detail
    if len(parquet_files) > 5:
        print(f"\nInspecting first 5 files in detail...")
        print("(To inspect all, modify the script)")
        files_to_inspect = parquet_files[:5]
    else:
        files_to_inspect = parquet_files
    
    # Inspect each file
    metadata_list = []
    for file_path in files_to_inspect:
        try:
            meta = inspect_parquet_file(file_path)
            metadata_list.append(meta)
        except Exception as e:
            print(f"\n❌ Error inspecting {file_path}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Save summary
    summary = {
        'project_id': PROJECT_ID,
        'bucket': BUCKET_NAME,
        'total_parquet_files': len(parquet_files),
        'inspected_files': len(metadata_list),
        'file_details': metadata_list
    }
    
    summary_file = 'data/parquet_inspection_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n✓ Summary saved to {summary_file}")
    
    # Generate loading script
    generate_loading_script(parquet_files, metadata_list)
    
    print(f"\n{'='*70}")
    print("INSPECTION COMPLETE")
    print(f"{'='*70}")
    print("\nNext steps:")
    print("  1. Review the inspection results above")
    print("  2. Run the auto-generated loading script:")
    print("     python3 scripts/02_load_discovered_parquet.py")
    print("  3. Verify data in BigQuery")

if __name__ == "__main__":
    main()
