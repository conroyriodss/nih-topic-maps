#!/usr/bin/env python3
"""
Create unified tables across all fiscal years
Project: od-cl-odss-conroyri-f75a
"""

from google.cloud import bigquery
import time

PROJECT_ID = "od-cl-odss-conroyri-f75a"
DATASET_ID = "nih_data"

client = bigquery.Client(project=PROJECT_ID)

def run_query(name, query):
    """Run a BigQuery query"""
    print(f"\n{'='*70}")
    print(f"{name}")
    print(f"{'='*70}\n")
    print("Executing query...")
    
    start = time.time()
    job = client.query(query)
    job.result()  # Wait for completion
    elapsed = time.time() - start
    
    print(f"✓ Complete in {elapsed:.1f} seconds")
    return job

print(f"\n{'#'*70}")
print(f"# Creating Unified NIH Tables")
print(f"# Project: {PROJECT_ID}")
print(f"{'#'*70}\n")

# 1. Create unified projects table
projects_query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.projects_all`
AS
SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.projects_fy*`
"""

run_query("Creating Unified Projects Table", projects_query)

# 2. Create unified abstracts table
abstracts_query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.abstracts_all`
AS
SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.abstracts_fy*`
"""

run_query("Creating Unified Abstracts Table", abstracts_query)

# 3. Create combined grant text table (for embeddings)
grant_text_query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.grant_text`
AS
SELECT 
    CAST(p.APPLICATION_ID AS STRING) AS APPLICATION_ID,
    p.PROJECT_TITLE,
    CAST(p.YEAR AS INT64) AS FISCAL_YEAR,
    p.ADMINISTERING_IC AS IC_NAME,
    CAST(p.TOTAL_COST AS FLOAT64) AS TOTAL_COST,
    p.ORG_NAME,
    p.ORG_CITY,
    p.ORG_STATE,
    p.ORG_COUNTRY,
    p.PI_NAMEs,
    a.ABSTRACT_TEXT,
    CONCAT(
        IFNULL(p.PROJECT_TITLE, ''),
        '. ',
        IFNULL(a.ABSTRACT_TEXT, '')
    ) AS combined_text,
    LENGTH(CONCAT(
        IFNULL(p.PROJECT_TITLE, ''),
        IFNULL(a.ABSTRACT_TEXT, '')
    )) AS text_length
FROM `{PROJECT_ID}.{DATASET_ID}.projects_all` p
LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.abstracts_all` a
    ON CAST(p.APPLICATION_ID AS STRING) = CAST(a.APPLICATION_ID AS STRING)
WHERE 
    p.PROJECT_TITLE IS NOT NULL
    AND a.ABSTRACT_TEXT IS NOT NULL
    AND LENGTH(a.ABSTRACT_TEXT) > 100
    AND p.TOTAL_COST IS NOT NULL
    AND p.TOTAL_COST > 0
"""

run_query("Creating Grant Text Table for Embeddings", grant_text_query)

# 4. Get statistics
stats_query = f"""
SELECT 
    'projects_all' as table_name,
    COUNT(*) as row_count,
    MIN(CAST(YEAR AS INT64)) as min_year,
    MAX(CAST(YEAR AS INT64)) as max_year,
    COUNT(DISTINCT ADMINISTERING_IC) as unique_ics
FROM `{PROJECT_ID}.{DATASET_ID}.projects_all`

UNION ALL

SELECT 
    'abstracts_all',
    COUNT(*),
    MIN(CAST(YEAR AS INT64)),
    MAX(CAST(YEAR AS INT64)),
    NULL
FROM `{PROJECT_ID}.{DATASET_ID}.abstracts_all`

UNION ALL

SELECT 
    'grant_text',
    COUNT(*),
    MIN(FISCAL_YEAR),
    MAX(FISCAL_YEAR),
    COUNT(DISTINCT IC_NAME)
FROM `{PROJECT_ID}.{DATASET_ID}.grant_text`
"""

print(f"\n{'='*70}")
print("Table Statistics")
print(f"{'='*70}\n")

df = client.query(stats_query).to_dataframe()
print(df.to_string(index=False))

# 5. Show grants by year
grants_by_year_query = f"""
SELECT 
    FISCAL_YEAR,
    COUNT(*) as grant_count,
    ROUND(SUM(TOTAL_COST) / 1000000000, 2) as total_funding_billions,
    ROUND(AVG(text_length), 0) as avg_text_length
FROM `{PROJECT_ID}.{DATASET_ID}.grant_text`
GROUP BY FISCAL_YEAR
ORDER BY FISCAL_YEAR
"""

print(f"\n{'='*70}")
print("Grants by Fiscal Year (Ready for Embeddings)")
print(f"{'='*70}\n")

df = client.query(grants_by_year_query).to_dataframe()
print(df.to_string(index=False))

# 6. Show IC distribution
ic_distribution_query = f"""
SELECT 
    IC_NAME,
    COUNT(*) as grant_count,
    ROUND(SUM(TOTAL_COST) / 1000000000, 2) as total_funding_billions
FROM `{PROJECT_ID}.{DATASET_ID}.grant_text`
GROUP BY IC_NAME
ORDER BY grant_count DESC
LIMIT 15
"""

print(f"\n{'='*70}")
print("Top 15 Institutes/Centers by Grant Count")
print(f"{'='*70}\n")

df = client.query(ic_distribution_query).to_dataframe()
print(df.to_string(index=False))

print(f"\n{'='*70}")
print("UNIFIED TABLES COMPLETE")
print(f"{'='*70}")
print(f"\nTables created:")
print(f"  ✓ {PROJECT_ID}.{DATASET_ID}.projects_all")
print(f"  ✓ {PROJECT_ID}.{DATASET_ID}.abstracts_all")
print(f"  ✓ {PROJECT_ID}.{DATASET_ID}.grant_text")
print(f"\nReady for embeddings generation!")
