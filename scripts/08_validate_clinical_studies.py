#!/usr/bin/env python3
"""
Validate and fix clinical studies data
"""

from google.cloud import bigquery
import pandas as pd

client = bigquery.Client(project='od-cl-odss-conroyri-f75a')

print("Checking clinical_studies table...")

# Check if table exists and has data
query = """
SELECT 
  COUNT(*) as total_records,
  COUNT(DISTINCT APPLICATION_ID) as unique_apps,
  MIN(FISCAL_YEAR) as min_year,
  MAX(FISCAL_YEAR) as max_year,
  COUNT(DISTINCT STUDY_STATUS) as status_types
FROM `od-cl-odss-conroyri-f75a.nih_exporter.clinical_studies`
"""

try:
    df = client.query(query).to_dataframe()
    print("\n✓ Clinical Studies Table Status:")
    print(f"  Total Records: {df['total_records'].iloc[0]:,}")
    print(f"  Unique Applications: {df['unique_apps'].iloc[0]:,}")
    print(f"  Year Range: {df['min_year'].iloc[0]}-{df['max_year'].iloc[0]}")
    print(f"  Status Types: {df['status_types'].iloc[0]}")
    
    if df['total_records'].iloc[0] > 0:
        print("\n✓ Clinical studies data loaded successfully!")
    else:
        print("\n⚠️  Table exists but has no data - needs reload")
        
except Exception as e:
    print(f"\n❌ Error accessing table: {e}")
    print("\nTable may need to be recreated.")
