#!/bin/bash

PROJECT_ID="od-cl-odss-conroyri-f75a"
DATASET="nih_exporter"
BUCKET="gs://od-cl-odss-conroyri-nih-embeddings/exporter"

echo "Loading PROJECTS year by year..."

FIRST=true
for YEAR in {1990..2024}; do
    echo -n "Loading ${YEAR}... "
    
    if [ "$FIRST" = true ]; then
        DISPOSITION="--replace"
        FIRST=false
    else
        DISPOSITION="--noreplace"
    fi
    
    bq load \
      --source_format=PARQUET \
      ${DISPOSITION} \
      --autodetect \
      --max_bad_records=100 \
      ${PROJECT_ID}:${DATASET}.projects \
      "${BUCKET}/projects_parquet/YEAR=${YEAR}/projects_${YEAR}.parquet" 2>&1 | grep -q "successfully" && echo "✓" || echo "✗"
done

echo ""
echo "Checking total..."
bq query --use_legacy_sql=false "SELECT COUNT(*) as total FROM \`${PROJECT_ID}.${DATASET}.projects\`"
