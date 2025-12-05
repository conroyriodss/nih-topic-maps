#!/usr/bin/env python3
"""
Create 50k stratified sample from 1.5M NIH grants
Preserves FY, IC, and funding level distribution
"""
from google.cloud import bigquery
import pandas as pd

PROJECT_ID = 'od-cl-odss-conroyri-f75a'
SAMPLE_SIZE = 50000

print("=" * 80)
print("CREATING 50K STRATIFIED SAMPLE FROM 1.5M GRANTS")
print("=" * 80)

client = bigquery.Client(project=PROJECT_ID)

# Stratified sampling query
query = f"""
WITH base_data AS (
  SELECT 
    CAST(APPLICATION_ID AS INT64) as APPLICATION_ID,
    PROJECT_TITLE,
    IC_NAME,
    FY,
    TOTAL_COST,
    -- Create strata
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
    -- Calculate target per stratum
    CAST(CEIL(sc.stratum_size * {SAMPLE_SIZE} / 
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
  stratum
FROM stratified_sample
WHERE row_num <= stratum_target
ORDER BY RAND()
LIMIT {SAMPLE_SIZE}
"""

print("\n[1/3] Executing stratified sampling query...")
print(f"  Target sample size: {SAMPLE_SIZE:,}")

df = client.query(query).to_dataframe()

print(f"\n[2/3] Sample created: {len(df):,} grants")
print("\nSample distribution:")
print(f"  Fiscal years: {df['FY'].min():.0f} - {df['FY'].max():.0f}")
print(f"  Institutes: {df['IC_NAME'].nunique()}")
print(f"  Total funding: ${df['TOTAL_COST'].sum() / 1e9:.2f}B")
print(f"\nFunding distribution:")
print(df['TOTAL_COST'].describe())

print(f"\n[3/3] Saving sample...")
df[['APPLICATION_ID', 'PROJECT_TITLE', 'IC_NAME', 'FY', 'TOTAL_COST']].to_parquet(
    'sample_50k_stratified.parquet',
    index=False
)

print(f"\n✅ Saved: sample_50k_stratified.parquet")

# Show IC distribution
print("\nTop 15 ICs in sample:")
ic_dist = df['IC_NAME'].value_counts().head(15)
for ic, count in ic_dist.items():
    pct = count / len(df) * 100
    print(f"  {ic[:50]:50s}: {count:5d} ({pct:4.1f}%)")

print("\nFY distribution:")
fy_dist = df.groupby('FY').size()
print(f"  Mean per year: {fy_dist.mean():.0f}")
print(f"  Range: {fy_dist.min()}-{fy_dist.max()}")

print("\n" + "=" * 80)
print("READY FOR EMBEDDING GENERATION")
print("=" * 80)
