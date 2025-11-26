#!/usr/bin/env python3
"""Check for Project_Terms in your BigQuery data"""
from google.cloud import bigquery

client = bigquery.Client(project='od-cl-odss-conroyri-f75a')

print("=" * 60)
print("PROJECT_TERMS AVAILABILITY CHECK")
print("=" * 60)

# Check if Project_Terms exists in any table
datasets = ['nih_data', 'nih_processed', 'nih_exporter']

for dataset in datasets:
    print(f"\nChecking {dataset}...")
    query = f"""
    SELECT table_name
    FROM `od-cl-odss-conroyri-f75a.{dataset}.INFORMATION_SCHEMA.COLUMNS`
    WHERE LOWER(column_name) IN ('project_terms', 'project_term', 'terms')
    """
    try:
        results = list(client.query(query).result())
        if results:
            for row in results:
                print(f"  ✓ Found in {dataset}.{row.table_name}")
                
                # Sample the data
                sample_query = f"""
                SELECT PROJECT_TERMS
                FROM `od-cl-odss-conroyri-f75a.{dataset}.{row.table_name}`
                WHERE PROJECT_TERMS IS NOT NULL
                LIMIT 5
                """
                samples = list(client.query(sample_query).result())
                if samples:
                    print(f"\n  Sample Project_Terms:")
                    for i, s in enumerate(samples[:3], 1):
                        terms = s.PROJECT_TERMS[:150]
                        print(f"    {i}. {terms}...")
        else:
            print(f"  ✗ No PROJECT_TERMS column found")
    except Exception as e:
        print(f"  Error: {e}")

# Also check NIH_SPENDING_CATS format
print("\n" + "=" * 60)
print("NIH_SPENDING_CATS SAMPLE")
print("=" * 60)

query = """
SELECT NIH_SPENDING_CATS
FROM `od-cl-odss-conroyri-f75a.nih_processed.projects`
WHERE NIH_SPENDING_CATS IS NOT NULL
LIMIT 5
"""
try:
    results = list(client.query(query).result())
    for i, row in enumerate(results, 1):
        cats = row.NIH_SPENDING_CATS
        print(f"\n{i}. {cats[:200]}")
        if ';' in cats:
            cat_list = [c.strip() for c in cats.split(';')]
            print(f"   → {len(cat_list)} categories")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("SUMMARY:")
print("- PROJECT_TERMS = text-mined keywords (multiple per project)")
print("- NIH_SPENDING_CATS = RCDC categories (multiple per project)")
print("Both can be used for hybrid clustering!")
print("=" * 60)
