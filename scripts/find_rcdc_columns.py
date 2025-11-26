#!/usr/bin/env python3
"""Search all datasets for RCDC and other category columns"""
from google.cloud import bigquery

client = bigquery.Client(project='od-cl-odss-conroyri-f75a')

print("=" * 60)
print("COMPREHENSIVE COLUMN SEARCH - ALL DATASETS")
print("=" * 60)

datasets = ['nih_exporter', 'nih_processed', 'nih_data', 'nih_analytics']

for dataset in datasets:
    print(f"\n{'='*60}")
    print(f"Dataset: {dataset}")
    print(f"{'='*60}")
    
    try:
        # Get all columns across all tables
        query = f"""
        SELECT 
          table_name,
          column_name,
          data_type
        FROM `od-cl-odss-conroyri-f75a.{dataset}.INFORMATION_SCHEMA.COLUMNS`
        ORDER BY table_name, ordinal_position
        """
        results = client.query(query).result()
        
        # Group by table
        tables = {}
        for row in results:
            if row.table_name not in tables:
                tables[row.table_name] = []
            tables[row.table_name].append((row.column_name, row.data_type))
        
        # Show all columns for each table
        for table_name, columns in tables.items():
            print(f"\n{table_name} ({len(columns)} columns):")
            
            # Show all columns
            for col_name, col_type in columns:
                # Highlight interesting columns
                if any(keyword in col_name.lower() for keyword in 
                      ['rcdc', 'category', 'spending', 'disease', 'mesh', 'term', 'topic']):
                    print(f"  *** {col_name}: {col_type} ***")
                else:
                    print(f"      {col_name}: {col_type}")
            
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 60)
print("✓ Complete column inventory")
