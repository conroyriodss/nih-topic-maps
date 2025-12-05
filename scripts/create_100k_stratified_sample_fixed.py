#!/usr/bin/env python3
"""
Create Stratified 100k Sample - FIXED VERSION
Auto-detects available columns in BigQuery table
"""
import pandas as pd
import numpy as np
from google.cloud import bigquery
import time
import sys

PROJECT_ID = 'od-cl-odss-conroyri-f75a'
SAMPLE_SIZE = 100_000
RANDOM_SEED = 42

print("=" * 70)
print("CREATING STRATIFIED 100K SAMPLE (AUTO-DETECT VERSION)")
print("=" * 70)

client = bigquery.Client(project=PROJECT_ID)

# Step 0: Auto-detect available columns
print("\n[0/5] Detecting available columns...")
query_schema = """
SELECT column_name, data_type
FROM `od-cl-odss-conroyri-f75a.nih_exporter`.INFORMATION_SCHEMA.COLUMNS
WHERE table_name = 'projects'
ORDER BY ordinal_position
"""

schema_df = client.query(query_schema).to_dataframe()
available_columns = set(schema_df['column_name'].values)
print(f"  Found {len(available_columns)} columns")

# Identify text column
text_candidates = ['ABSTRACT_TEXT', 'ABSTRACT', 'PROJECT_ABSTRACT', 'PROJECT_TERMS', 'PROJECT_DESCRIPTION', 'PUBLIC_HEALTH_RELEVANCE']
text_column = next((col for col in text_candidates if col in available_columns), 'PROJECT_TITLE')
print(f"  → Using {text_column} for text embeddings")

# Check optional columns
has_rcdc = 'NIH_SPENDING_CATS' in available_columns
has_cost = 'TOTAL_COST' in available_columns
has_core = 'CORE_PROJECT_NUM' in available_columns

print(f"  ✓ RCDC: {has_rcdc}, Cost: {has_cost}, Core#: {has_core}")

# Build dynamic SELECT
select_cols = ['APPLICATION_ID', 'PROJECT_TITLE', 'FY', 'IC_NAME']
if has_core: select_cols.append('CORE_PROJECT_NUM')
if text_column != 'PROJECT_TITLE': select_cols.append(text_column)
if has_cost: select_cols.append('TOTAL_COST')
if has_rcdc: select_cols.append('NIH_SPENDING_CATS')
select_clause = ', '.join(select_cols)

# Step 1: Population stats
print("\n[1/5] Analyzing population...")
query_stats = f"""
SELECT FY, IC_NAME, COUNT(*) as n_grants,
  {('SUM(TOTAL_COST) as total_funding' if has_cost else '0 as total_funding')}
FROM `od-cl-odss-conroyri-f75a.nih_exporter.projects`
WHERE FY BETWEEN 1990 AND 2024 AND PROJECT_TITLE IS NOT NULL AND IC_NAME IS NOT NULL
GROUP BY FY, IC_NAME
"""
stats_df = client.query(query_stats).to_dataframe()
stats_df['target'] = np.ceil(stats_df['n_grants'] / stats_df['n_grants'].sum() * SAMPLE_SIZE).astype(int)
print(f"  Population: {stats_df['n_grants'].sum():,} grants, Target: {SAMPLE_SIZE:,}")

# Step 2: Adjust allocation
print("\n[2/5] Adjusting stratification...")
stats_df.loc[stats_df['target'] / stats_df['n_grants'] > 0.9, 'target'] = (stats_df.loc[stats_df['target'] / stats_df['n_grants'] > 0.9, 'n_grants'] * 0.9).astype(int)
stats_df['target'] = (stats_df['target'] * SAMPLE_SIZE / stats_df['target'].sum()).round().astype(int)
diff = SAMPLE_SIZE - stats_df['target'].sum()
if diff != 0:
    stats_df.loc[stats_df.nlargest(abs(diff), 'n_grants').index, 'target'] += np.sign(diff)
print(f"  Adjusted sum: {stats_df['target'].sum():,}")

# Step 3: Sample
print("\n[3/5] Sampling strata...")
samples = []
for idx, row in stats_df.iterrows():
    if row['target'] == 0: continue
    query = f"SELECT {select_clause} FROM `od-cl-odss-conroyri-f75a.nih_exporter.projects` WHERE FY = {row['FY']} AND IC_NAME = '{row['IC_NAME'].replace(chr(39), chr(39)*2)}' AND PROJECT_TITLE IS NOT NULL ORDER BY RAND() LIMIT {row['target']}"
    try:
        samples.append(client.query(query).to_dataframe())
    except Exception as e:
        print(f"  Warning: FY={row['FY']}, IC={row['IC_NAME'][:20]}: {e}")
    if (idx + 1) % 100 == 0: print(f"  {idx + 1}/{len(stats_df)}...")

df = pd.concat(samples, ignore_index=True)
print(f"  Sampled: {len(df):,} grants")

# Step 4: Validate
print("\n[4/5] Validating...")
print(f"  FY range: {df['FY'].min()}-{df['FY'].max()}")
print(f"  ICs: {df['IC_NAME'].nunique()}")
if has_rcdc: print(f"  RCDC coverage: {df['NIH_SPENDING_CATS'].notna().mean():.1%}")

# Step 5: Save
print("\n[5/5] Saving...")
df.to_parquet('grants_100k_stratified.parquet', index=False)
import json
with open('grants_100k_metadata.json', 'w') as f:
    json.dump({'sample_size': len(df), 'text_column': text_column, 'columns': df.columns.tolist(), 'fy_range': f"{df['FY'].min()}-{df['FY'].max()}", 'n_ics': int(df['IC_NAME'].nunique())}, f, indent=2)
print("  ✓ grants_100k_stratified.parquet")
print("  ✓ grants_100k_metadata.json")
print("\n" + "=" * 70)
print("COMPLETE! Next: python scripts/05_generate_embeddings_pubmedbert.py")
