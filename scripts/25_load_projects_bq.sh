#!/bin/bash

PROJECT_ID="od-cl-odss-conroyri-f75a"
DATASET="nih_exporter"
BUCKET="gs://od-cl-odss-conroyri-nih-embeddings/exporter"

echo "======================================================================"
echo "Loading PROJECTS table (all years at once)"
echo "======================================================================"

# Build list of all files
FILES=""
for YEAR in {1990..2024}; do
    FILES="${FILES}${BUCKET}/projects_parquet/YEAR=${YEAR}/projects_${YEAR}.parquet,"
done

# Remove trailing comma
FILES=${FILES%,}

echo "Loading from ${BUCKET}/projects_parquet/..."

# Load all at once
bq load \
  --source_format=PARQUET \
  --replace \
  --autodetect \
  --max_bad_records=100 \
  ${PROJECT_ID}:${DATASET}.projects \
  ${FILES}

# Verify
echo ""
echo "Verifying..."
bq query --use_legacy_sql=false "
SELECT 
  COUNT(*) as total_grants,
  MIN(FY) as min_year,
  MAX(FY) as max_year
FROM \`${PROJECT_ID}.${DATASET}.projects\`
"

echo ""
echo "Sample data:"
bq query --use_legacy_sql=false --max_rows=5 "
SELECT 
  CORE_PROJECT_NUM,
  PROJECT_TITLE,
  FY,
  IC_NAME
FROM \`${PROJECT_ID}.${DATASET}.projects\`
LIMIT 5
"
