#!/usr/bin/env python3
"""
Catalog ExPORTER parquet files - Simple and robust version
"""

import subprocess
import pandas as pd
from datetime import datetime
import json
import os

PROJECT_ID = 'od-cl-odss-conroyri-f75a'
BUCKET_NAME = 'od-cl-odss-conroyri-nih-embeddings'
BUCKET_PATH = f'gs://{BUCKET_NAME}/exporter/'

print("\n" + "="*70)
print("# NIH ExPORTER Data Catalog")
print("="*70 + "\n")

# List all parquet files using gsutil
print("Scanning for parquet files...")
result = subprocess.run(
    ['gsutil', 'ls', '-l', BUCKET_PATH + '**'],
    capture_output=True,
    text=True
)

lines = result.stdout.strip().split('\n')
parquet_files = []

for line in lines:
    if '.parquet' in line and 'TOTAL:' not in line:
        parts = line.split()
        if len(parts) >= 3:
            size_bytes = int(parts[0]) if parts[0].isdigit() else 0
            filepath = parts[-1]
            filename = filepath.split('/')[-1]
            
            parquet_files.append({
                'filename': filename,
                'full_path': filepath,
                'size_mb': size_bytes / 1024**2,
                'size_gb': size_bytes / 1024**3
            })

print(f"✓ Found {len(parquet_files)} parquet files\n")

if len(parquet_files) == 0:
    print("No parquet files found. Check path:")
    print(f"  {BUCKET_PATH}")
    exit(1)

# Analyze each file
catalog = {
    'metadata': {
        'catalog_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'project_id': PROJECT_ID,
        'bucket': BUCKET_NAME,
        'total_files': len(parquet_files)
    },
    'files': []
}

print("="*70)
print("ANALYZING EACH FILE")
print("="*70 + "\n")

for file_info in sorted(parquet_files, key=lambda x: x['filename']):
    print(f"📊 {file_info['filename']}")
    print(f"   Path: {file_info['full_path']}")
    print(f"   Size: {file_info['size_mb']:.2f} MB")
    
    # Try to read file metadata
    try:
        df = pd.read_parquet(file_info['full_path'], engine='pyarrow')
        
        file_info['rows'] = len(df)
        file_info['columns'] = list(df.columns)
        file_info['column_count'] = len(df.columns)
        
        # Identify type
        cols_lower = [c.lower() for c in df.columns]
        
        if 'project_title' in cols_lower or 'core_project_num' in cols_lower:
            file_info['type'] = 'projects'
        elif 'abstract_text' in cols_lower:
            file_info['type'] = 'abstracts'
        elif 'pmid' in cols_lower:
            file_info['type'] = 'publications'
        elif 'patent_id' in cols_lower:
            file_info['type'] = 'patents'
        elif 'clinicaltrials_gov_id' in cols_lower:
            file_info['type'] = 'clinical_studies'
        elif 'org_name' in cols_lower:
            file_info['type'] = 'organizations'
        else:
            file_info['type'] = 'other'
        
        # Get year range
        if 'FISCAL_YEAR' in df.columns:
            file_info['min_year'] = int(df['FISCAL_YEAR'].min())
            file_info['max_year'] = int(df['FISCAL_YEAR'].max())
        
        print(f"   Type: {file_info['type']}")
        print(f"   Rows: {file_info['rows']:,}")
        print(f"   Columns: {file_info['column_count']}")
        
        if 'min_year' in file_info:
            print(f"   Years: {file_info['min_year']}-{file_info['max_year']}")
        
        # Store first 10 column names
        file_info['sample_columns'] = df.columns[:10].tolist()
        
    except Exception as e:
        print(f"   ⚠️  Error reading: {str(e)[:100]}")
        file_info['error'] = str(e)[:200]
    
    catalog['files'].append(file_info)
    print()

# Summary by type
print("="*70)
print("SUMMARY BY TYPE")
print("="*70 + "\n")

type_summary = {}
for file in catalog['files']:
    ftype = file.get('type', 'unknown')
    if ftype not in type_summary:
        type_summary[ftype] = {
            'count': 0,
            'total_rows': 0,
            'total_size_mb': 0,
            'files': []
        }
    type_summary[ftype]['count'] += 1
    type_summary[ftype]['total_rows'] += file.get('rows', 0)
    type_summary[ftype]['total_size_mb'] += file.get('size_mb', 0)
    type_summary[ftype]['files'].append(file['filename'])

for ftype, stats in sorted(type_summary.items()):
    print(f"📁 {ftype.upper()}")
    print(f"   Files: {stats['count']}")
    print(f"   Rows: {stats['total_rows']:,}")
    print(f"   Size: {stats['total_size_mb']:.1f} MB")
    print()

# Save JSON catalog
os.makedirs('data', exist_ok=True)
catalog_json_path = 'data/exporter_catalog.json'
with open(catalog_json_path, 'w') as f:
    json.dump(catalog, f, indent=2)

print(f"✓ Saved: {catalog_json_path}")

# Generate Markdown summary
markdown = f"""# NIH ExPORTER Data Summary

**Generated:** {catalog['metadata']['catalog_date']}  
**Location:** `{BUCKET_PATH}`  
**Total Files:** {len(parquet_files)}  
**Total Size:** {sum(f['size_gb'] for f in parquet_files):.2f} GB

## Files by Type

"""

for ftype, stats in sorted(type_summary.items()):
    markdown += f"\n### {ftype.upper()}\n"
    markdown += f"- Files: {stats['count']}\n"
    markdown += f"- Rows: {stats['total_rows']:,}\n"
    markdown += f"- Size: {stats['total_size_mb']:.1f} MB\n"
    markdown += f"- Files: {', '.join(stats['files'])}\n"

markdown_path = 'data/EXPORTER_SUMMARY.md'
with open(markdown_path, 'w') as f:
    f.write(markdown)

print(f"✓ Saved: {markdown_path}")

# Upload to GCS
print("\nUploading to GCS...")
subprocess.run(['gsutil', 'cp', catalog_json_path, f'{BUCKET_PATH}CATALOG.json'])
subprocess.run(['gsutil', 'cp', markdown_path, f'{BUCKET_PATH}SUMMARY.md'])

print("\n" + "="*70)
print("✓ COMPLETE!")
print("="*70)
print(f"\n📄 Local: cat {markdown_path}")
print(f"☁️  GCS: gsutil cat {BUCKET_PATH}SUMMARY.md")
