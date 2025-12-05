#!/bin/bash
# Consolidate NIH ExPORTER data - load from parquet files
# Handles location mismatch by loading directly from GCS

PROJECT="od-cl-odss-conroyri-f75a"
DATASET="nih_exporter"
BUCKET="gs://od-cl-odss-conroyri-nih-embeddings/exporter"

echo "=== Step 1: Load projects from parquet (all years) ==="
bq load \
  --source_format=PARQUET \
  --replace \
  --hive_partitioning_mode=AUTO \
  --hive_partitioning_source_uri_prefix="${BUCKET}/projects_parquet/" \
  ${PROJECT}:${DATASET}.projects \
  "${BUCKET}/projects_parquet/*"

echo "=== Step 2: Load clinicalstudies from parquet ==="
bq load \
  --source_format=PARQUET \
  --replace \
  ${PROJECT}:${DATASET}.clinicalstudies \
  "${BUCKET}/clinicalstudies_parquet/clinicalstudies_ALL.parquet"

echo "=== Step 3: Load abstracts from parquet ==="
bq load \
  --source_format=PARQUET \
  --replace \
  --hive_partitioning_mode=AUTO \
  --hive_partitioning_source_uri_prefix="${BUCKET}/abstracts_parquet/" \
  ${PROJECT}:${DATASET}.abstracts \
  "${BUCKET}/abstracts_parquet/*"

echo "=== Step 4: Load linktables from parquet ==="
bq load \
  --source_format=PARQUET \
  --replace \
  --hive_partitioning_mode=AUTO \
  --hive_partitioning_source_uri_prefix="${BUCKET}/linktables_parquet/" \
  ${PROJECT}:${DATASET}.linktables \
  "${BUCKET}/linktables_parquet/*"

echo "=== Step 5: Validate projects by fiscal year ==="
bq query --use_legacy_sql=false \
"SELECT 
  CAST(FY AS INT64) as fiscal_year, 
  COUNT(*) as row_count,
  ROUND(SUM(TOTAL_COST)/1e9, 2) as funding_billions
FROM \`${PROJECT}.${DATASET}.projects\`
GROUP BY 1 ORDER BY 1;"

echo "=== Step 6: Validate abstracts by fiscal year ==="
bq query --use_legacy_sql=false \
"SELECT 
  CAST(FY AS INT64) as fiscal_year, 
  COUNT(*) as row_count
FROM \`${PROJECT}.${DATASET}.abstracts\`
GROUP BY 1 ORDER BY 1;"

echo "=== Step 7: Show clinicalstudies count ==="
bq query --use_legacy_sql=false \
"SELECT COUNT(*) as row_count FROM \`${PROJECT}.${DATASET}.clinicalstudies\`;"

echo "=== Step 8: Final table inventory ==="
bq ls --format=pretty ${PROJECT}:${DATASET}

echo "=== Done ==="
