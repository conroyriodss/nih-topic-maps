#!/usr/bin/env python3
"""
Create 100k stratified sample - Run in Cloud Shell
"""
from google.cloud import bigquery
import pandas as pd

PROJECT_ID = 'od-cl-odss-conroyri-f75a'

print("=" * 80)
print("CREATING 100K STRATIFIED SAMPLE")
print("=" * 80)

client = bigquery.Client(project=PROJECT_ID)

query = f"""
WITH base_data AS (
  SELECT 
    CAST(APPLICATION_ID AS INT64) as APPLICATION_ID,
    PROJECT_TITLE,
    IC_NAME,
    FY,
    TOTAL_COST,
    NIH_SPENDING_CATS,
    PROJECT_TERMS,
    CONCAT(
      IC_NAME, '_',
      CAST(FY AS STRING), '_',
      CASE 
        WHEN TOTAL_COST < 250000 THEN 'LOW'
        WHEN TOTAL_COST < 750000 THEN 'MED'
        ELSE 'HIGH'
      END
    ) as stratum
  FROM `{PROJECT_ID}.nih_exporter.projects`
  WHERE TOTAL_COST > 0
    AND FY BETWEEN 2000 AND 2024
    AND PROJECT_TITLE IS NOT NULL
),
stratum_counts AS (
  SELECT 
    stratum,
    COUNT(*) as stratum_size
  FROM base_data
  GROUP BY stratum
),
stratified_sample AS (
  SELECT 
    b.*,
    ROW_NUMBER() OVER (
      PARTITION BY b.stratum 
      ORDER BY RAND()
    ) as row_num,
    CAST(CEIL(sc.stratum_size * 100000 / 
      (SELECT COUNT(*) FROM base_data)) AS INT64) as stratum_target
  FROM base_data b
  JOIN stratum_counts sc ON b.stratum = sc.stratum
)
SELECT 
  APPLICATION_ID,
  PROJECT_TITLE,
  IC_NAME,
  FY,
  TOTAL_COST,
  NIH_SPENDING_CATS,
  PROJECT_TERMS
FROM stratified_sample
WHERE row_num <= stratum_target
ORDER BY RAND()
LIMIT 100000
"""

print("\nQuerying BigQuery...")
df = client.query(query).to_dataframe()
print(f"✅ Created {len(df):,} grant sample")

print("\nBreakdown by IC:")
print(df['IC_NAME'].value_counts().head(10))

print("\nBreakdown by FY:")
print(df['FY'].value_counts().sort_index().tail(10))

df.to_csv('sample_100k.csv', index=False)
print(f"\n✅ Saved to sample_100k.csv")

# Upload to GCS
print("\nUploading to GCS...")
import subprocess
subprocess.run(['gsutil', 'cp', 'sample_100k.csv', 
                'gs://od-cl-odss-conroyri-nih-embeddings/'])

print("\n" + "=" * 80)
print("SAMPLE READY")
print("=" * 80)
print("\nNext: Generate embeddings and cluster (run scripts/cluster_100k.py)")
print("=" * 80)
