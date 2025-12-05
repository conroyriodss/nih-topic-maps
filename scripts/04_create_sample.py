#!/usr/bin/env python3
"""
Create stratified sample of 50K grants for prototype
Project: od-cl-odss-conroyri-f75a
"""

from google.cloud import bigquery

PROJECT_ID = "od-cl-odss-conroyri-f75a"
DATASET_ID = "nih_data"

client = bigquery.Client(project=PROJECT_ID)

print("\n" + "="*70)
print("Creating 50K Stratified Sample")
print("="*70 + "\n")

# Create sample table - stratified by year and IC to ensure representation
sample_query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.grant_text_sample`
AS
WITH ranked_grants AS (
  SELECT 
    *,
    ROW_NUMBER() OVER (
      PARTITION BY FISCAL_YEAR, IC_NAME 
      ORDER BY RAND()
    ) as rn,
    COUNT(*) OVER (PARTITION BY FISCAL_YEAR, IC_NAME) as group_total
  FROM `{PROJECT_ID}.{DATASET_ID}.grant_text`
)
SELECT 
  APPLICATION_ID,
  PROJECT_TITLE,
  FISCAL_YEAR,
  IC_NAME,
  TOTAL_COST,
  ORG_NAME,
  ORG_CITY,
  ORG_STATE,
  ORG_COUNTRY,
  PI_NAMEs,
  ABSTRACT_TEXT,
  combined_text,
  text_length
FROM ranked_grants
WHERE rn <= GREATEST(1, CAST(group_total * 0.034 AS INT64))  -- ~3.4% sample = 50K
ORDER BY RAND()
LIMIT 50000
"""

print("Executing stratified sampling query...")
job = client.query(sample_query)
job.result()

# Get statistics
stats_query = f"""
SELECT 
  COUNT(*) as total_grants,
  MIN(FISCAL_YEAR) as min_year,
  MAX(FISCAL_YEAR) as max_year,
  COUNT(DISTINCT IC_NAME) as unique_ics,
  COUNT(DISTINCT FISCAL_YEAR) as years_represented,
  ROUND(AVG(text_length), 0) as avg_text_length,
  ROUND(SUM(TOTAL_COST) / 1000000000, 2) as total_funding_billions
FROM `{PROJECT_ID}.{DATASET_ID}.grant_text_sample`
"""

df = client.query(stats_query).to_dataframe()
print("\nSample Statistics:")
print(df.to_string(index=False))

# Distribution by year
year_dist_query = f"""
SELECT 
  FISCAL_YEAR,
  COUNT(*) as grant_count
FROM `{PROJECT_ID}.{DATASET_ID}.grant_text_sample`
GROUP BY FISCAL_YEAR
ORDER BY FISCAL_YEAR
"""

print("\nGrants by Year:")
df = client.query(year_dist_query).to_dataframe()
print(df.to_string(index=False))

# Distribution by IC
ic_dist_query = f"""
SELECT 
  IC_NAME,
  COUNT(*) as grant_count
FROM `{PROJECT_ID}.{DATASET_ID}.grant_text_sample`
GROUP BY IC_NAME
ORDER BY grant_count DESC
LIMIT 15
"""

print("\nTop 15 ICs in Sample:")
df = client.query(ic_dist_query).to_dataframe()
print(df.to_string(index=False))

print("\n" + "="*70)
print("✓ Sample Created: grant_text_sample")
print("="*70)
print("\nNext step: Generate embeddings")
print("  python3 scripts/05_generate_embeddings_sample.py")
