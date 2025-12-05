#!/usr/bin/env python3
"""
Create Stratified 100k Sample for Hierarchical Clustering Optimization
Balanced across fiscal years, ICs, and research domains
"""
import pandas as pd
import numpy as np
from google.cloud import bigquery
import time

# Configuration
PROJECT_ID = 'od-cl-odss-conroyri-f75a'
SAMPLE_SIZE = 100_000
RANDOM_SEED = 42

print("=" * 70)
print("CREATING STRATIFIED 100K SAMPLE")
print("=" * 70)

# Step 1: Query full population statistics
print("\n[1/5] Analyzing population distribution...")
client = bigquery.Client(project=PROJECT_ID)

query_stats = """
SELECT 
  FY,
  IC_NAME,
  COUNT(*) as n_grants,
  SUM(TOTAL_COST) as total_funding
FROM `od-cl-odss-conroyri-f75a.nih_exporter.projects`
WHERE FY BETWEEN 1990 AND 2024
  AND PROJECT_TITLE IS NOT NULL
  AND IC_NAME IS NOT NULL
GROUP BY FY, IC_NAME
ORDER BY FY, IC_NAME
"""
stats_df = client.query(query_stats).to_dataframe()

# Calculate target samples per stratum
total_grants = stats_df['n_grants'].sum()
stats_df['target_sample'] = np.ceil(
    stats_df['n_grants'] / total_grants * SAMPLE_SIZE
).astype(int)

print(f"  Total grants in population: {total_grants:,}")
print(f"  Fiscal years: {stats_df['FY'].min()} - {stats_df['FY'].max()}")
print(f"  Unique ICs: {stats_df['IC_NAME'].nunique()}")
print(f"  Target sample size: {SAMPLE_SIZE:,}")

# Step 2: Verify stratum sizes are feasible
print("\n[2/5] Validating stratification feasibility...")
stats_df['sample_rate'] = stats_df['target_sample'] / stats_df['n_grants']
oversample = stats_df[stats_df['sample_rate'] > 0.95]

if len(oversample) > 0:
    print(f"  WARNING: {len(oversample)} strata require >95% sampling:")
    print(oversample[['FY', 'IC_NAME', 'n_grants', 'target_sample']].head(10))
    print("  Adjusting sample allocation...")
    
    # Cap at 90% for small strata and redistribute
    stats_df.loc[stats_df['sample_rate'] > 0.9, 'target_sample'] = \
        (stats_df.loc[stats_df['sample_rate'] > 0.9, 'n_grants'] * 0.9).astype(int)

# Normalize to exactly 100k
adjustment = SAMPLE_SIZE / stats_df['target_sample'].sum()
stats_df['target_sample'] = (stats_df['target_sample'] * adjustment).round().astype(int)

# Final adjustment to hit exact count
diff = SAMPLE_SIZE - stats_df['target_sample'].sum()
if diff != 0:
    # Add/subtract from largest strata
    largest_idx = stats_df.nlargest(abs(diff), 'n_grants').index
    stats_df.loc[largest_idx, 'target_sample'] += np.sign(diff)

print(f"  Adjusted sample sum: {stats_df['target_sample'].sum():,}")

# Step 3: Sample from each stratum
print("\n[3/5] Sampling from each stratum...")
samples = []
start = time.time()

for idx, row in stats_df.iterrows():
    fy = row['FY']
    ic = row['IC_NAME']
    n = row['target_sample']
    
    if n == 0:
        continue
    
    # Query this stratum with random sampling
    query_stratum = f"""
    SELECT 
      APPLICATION_ID,
      CORE_PROJECT_NUM,
      PROJECT_TITLE,
      PROJECT_TERMS,
      ABSTRACT_TEXT,
      FY,
      IC_NAME,
      TOTAL_COST,
      NIH_SPENDING_CATS
    FROM `od-cl-odss-conroyri-f75a.nih_exporter.projects`
    WHERE FY = {fy}
      AND IC_NAME = '{ic}'
      AND PROJECT_TITLE IS NOT NULL
    ORDER BY RAND()
    LIMIT {n}
    """
    
    stratum_df = client.query(query_stratum).to_dataframe()
    samples.append(stratum_df)
    
    if (idx + 1) % 50 == 0:
        print(f"  Processed {idx + 1}/{len(stats_df)} strata...")

# Combine samples
df_sample = pd.concat(samples, ignore_index=True)
print(f"  Sampling completed in {time.time() - start:.1f}s")
print(f"  Final sample size: {len(df_sample):,}")

# Step 4: Validate sample quality
print("\n[4/5] Validating sample quality...")

# Check FY distribution
fy_dist = df_sample['FY'].value_counts().sort_index()
print(f"  Fiscal years represented: {fy_dist.index.min()} - {fy_dist.index.max()}")
print(f"  Grants per year: {fy_dist.min()} - {fy_dist.max()} (mean: {fy_dist.mean():.0f})")

# Check IC distribution
ic_dist = df_sample['IC_NAME'].value_counts()
print(f"  ICs represented: {len(ic_dist)}")
print(f"  Top 5 ICs:")
for ic, count in ic_dist.head(5).items():
    pct = count / len(df_sample) * 100
    print(f"    {ic}: {count:,} ({pct:.1f}%)")

# Check RCDC coverage
rcdc_coverage = df_sample['NIH_SPENDING_CATS'].notna().mean()
print(f"  RCDC category coverage: {rcdc_coverage:.1%}")

# Check text data availability
abstract_coverage = df_sample['ABSTRACT_TEXT'].notna().mean()
terms_coverage = df_sample['PROJECT_TERMS'].notna().mean()
print(f"  Abstract coverage: {abstract_coverage:.1%}")
print(f"  Project terms coverage: {terms_coverage:.1%}")

# Step 5: Save sample
print("\n[5/5] Saving sample...")
output_file = 'grants_100k_stratified.parquet'
df_sample.to_parquet(output_file, index=False)
print(f"  Saved: {output_file}")

# Save metadata
metadata = {
    'sample_size': len(df_sample),
    'fiscal_years': f"{df_sample['FY'].min()}-{df_sample['FY'].max()}",
    'n_ics': int(df_sample['IC_NAME'].nunique()),
    'rcdc_coverage': float(rcdc_coverage),
    'abstract_coverage': float(abstract_coverage),
    'terms_coverage': float(terms_coverage),
    'total_funding': float(df_sample['TOTAL_COST'].sum()),
    'random_seed': RANDOM_SEED,
    'creation_date': pd.Timestamp.now().isoformat(),
    'fy_distribution': fy_dist.to_dict(),
    'ic_distribution': ic_dist.head(20).to_dict()
}

import json
with open('grants_100k_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)
print(f"  Saved: grants_100k_metadata.json")

print("\n" + "=" * 70)
print("STRATIFIED SAMPLE CREATION COMPLETE!")
print("=" * 70)
print(f"\nNext steps:")
print(f"1. Generate embeddings: python scripts/05_generate_embeddings_pubmedbert.py")
print(f"2. Run hierarchical parameter sweep: python scripts/hierarchical_param_sweep.py")
