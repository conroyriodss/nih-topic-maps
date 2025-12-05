#!/bin/bash

PROJECT_ID="od-cl-odss-conroyri-f75a"
DATASET="nih_exporter"
BUCKET="gs://od-cl-odss-conroyri-nih-embeddings/exporter"

echo "======================================================================"
echo "Loading NIH ExPORTER Data to BigQuery"
echo "======================================================================"

# Load PROJECTS (year-partitioned structure YEAR=XXXX/)
echo ""
echo "Loading PROJECTS table..."
bq load --source_format=PARQUET \
  --replace \
  --autodetect \
  ${PROJECT_ID}:${DATASET}.projects \
  "${BUCKET}/projects_parquet/YEAR=*/projects_*.parquet"

echo "✓ Projects loaded"

# Load ABSTRACTS 
echo ""
echo "Loading ABSTRACTS table..."
bq load --source_format=PARQUET \
  --replace \
  --autodetect \
  ${PROJECT_ID}:${DATASET}.abstracts \
  "${BUCKET}/abstracts_parquet/YEAR=*/abstracts_*.parquet"

echo "✓ Abstracts loaded"

# Load LINKTABLES
echo ""
echo "Loading LINKTABLES table..."
bq load --source_format=PARQUET \
  --replace \
  --autodetect \
  ${PROJECT_ID}:${DATASET}.linktables \
  "${BUCKET}/linktables_parquet/YEAR=*/linktables_*.parquet"

echo "✓ Link tables loaded"

# Load PATENTS (already worked)
echo ""
echo "Loading PATENTS table..."
bq load --source_format=PARQUET \
  --replace \
  --autodetect \
  ${PROJECT_ID}:${DATASET}.patents \
  "${BUCKET}/patents_parquet/patents_ALL.parquet"

echo "✓ Patents loaded"

# Skip clinical studies for now (has column name issues)
echo ""
echo "⚠️  Skipping clinical_studies (column name issue - will fix separately)"

echo ""
echo "======================================================================"
echo "Verifying tables..."
echo "======================================================================"

# Verify with correct flag placement
for TABLE in projects abstracts linktables patents; do
    echo ""
    echo "Checking ${TABLE}..."
    bq query --use_legacy_sql=false --format=pretty \
    "SELECT 
      '${TABLE}' as table_name,
      COUNT(*) as row_count,
      MIN(FISCAL_YEAR) as min_year,
      MAX(FISCAL_YEAR) as max_year
    FROM \`${PROJECT_ID}.${DATASET}.${TABLE}\`"
done

echo ""
echo "======================================================================"
echo "✓ LOAD COMPLETE!"
echo "======================================================================"
