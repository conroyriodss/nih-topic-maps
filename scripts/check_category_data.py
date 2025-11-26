#!/usr/bin/env python3
"""Check what NIH category data is available - checking all relevant tables"""
from google.cloud import bigquery

client = bigquery.Client(project='od-cl-odss-conroyri-f75a')

print("=" * 60)
print("NIH Category Data Availability - Complete Check")
print("=" * 60)

# Check nih_exporter (raw data)
print("\n=== 1. NIH_EXPORTER Dataset (Raw ExPORTER Data) ===")
try:
    tables = list(client.list_tables('nih_exporter'))
    print(f"Found {len(tables)} tables")
    
    # Look for projects_2024
    query = """
    SELECT column_name, data_type
    FROM `od-cl-odss-conroyri-f75a.nih_exporter.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'projects_2024'
    ORDER BY ordinal_position
    """
    results = client.query(query).result()
    print("\nColumns in projects_2024:")
    for row in results:
        print(f"  - {row.column_name}: {row.data_type}")
except Exception as e:
    print(f"Error: {e}")

# Check nih_processed
print("\n=== 2. NIH_PROCESSED Dataset ===")
try:
    tables = list(client.list_tables('nih_processed'))
    print(f"Tables: {[t.table_id for t in tables]}")
    
    # Check schema
    if tables:
        first_table = tables[0].table_id
        table_ref = client.get_table(f'nih_processed.{first_table}')
        print(f"\nColumns in {first_table}:")
        for field in table_ref.schema[:20]:
            print(f"  - {field.name}: {field.field_type}")
except Exception as e:
    print(f"Error: {e}")

# Check nih_data
print("\n=== 3. NIH_DATA Dataset ===")
try:
    tables = list(client.list_tables('nih_data'))
    print(f"Tables: {[t.table_id for t in tables]}")
except Exception as e:
    print(f"Error: {e}")

# Check grant_scorecard (has rich metadata)
print("\n=== 4. Grant Scorecard (Metadata Rich) ===")
try:
    query = """
    SELECT * 
    FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_scorecard_v2`
    LIMIT 3
    """
    results = client.query(query).result()
    
    # Get column names
    if results.total_rows > 0:
        first_row = next(iter(results))
        print(f"\nColumns in grant_scorecard_v2:")
        for key in dict(first_row).keys():
            print(f"  - {key}")
except Exception as e:
    print(f"Error: {e}")

# Check for RCDC or category data
print("\n=== 5. Looking for RCDC/Category Data ===")
datasets = ['nih_exporter', 'nih_processed', 'nih_data', 'nih_analytics']
for dataset in datasets:
    try:
        query = f"""
        SELECT table_name
        FROM `od-cl-odss-conroyri-f75a.{dataset}.INFORMATION_SCHEMA.TABLES`
        WHERE LOWER(table_name) LIKE '%rcdc%'
           OR LOWER(table_name) LIKE '%category%'
           OR LOWER(table_name) LIKE '%mesh%'
        """
        results = client.query(query).result()
        found = list(results)
        if found:
            print(f"\n{dataset}:")
            for row in found:
                print(f"  ✓ {row.table_name}")
    except:
        pass

print("\n" + "=" * 60)
print("✓ Complete check done")
