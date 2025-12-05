#!/bin/bash

PROJECT_ID="od-cl-odss-conroyri-f75a"
DATASET="nih_exporter"
BUCKET="gs://od-cl-odss-conroyri-nih-embeddings/exporter"

echo "======================================================================"
echo "Loading NIH ExPORTER Data to BigQuery"
echo "======================================================================"
echo ""

# Create dataset
echo "Creating dataset..."
bq mk --dataset --location=US ${PROJECT_ID}:${DATASET} 2>/dev/null || echo "Dataset already exists"

# Load PROJECTS (partitioned by year)
echo ""
echo "Loading PROJECTS table..."
bq load --source_format=PARQUET \
  --replace \
  --autodetect \
  --hive_partitioning_mode=AUTO \
  --hive_partitioning_source_uri_prefix="${BUCKET}/projects_parquet" \
  ${PROJECT_ID}:${DATASET}.projects \
  "${BUCKET}/projects_parquet/*/*.parquet"

echo "✓ Projects loaded"

# Load ABSTRACTS (partitioned by year)
echo ""
echo "Loading ABSTRACTS table..."
bq load --source_format=PARQUET \
  --replace \
  --autodetect \
  --hive_partitioning_mode=AUTO \
  --hive_partitioning_source_uri_prefix="${BUCKET}/abstracts_parquet" \
  ${PROJECT_ID}:${DATASET}.abstracts \
  "${BUCKET}/abstracts_parquet/*/*.parquet"

echo "✓ Abstracts loaded"

# Load LINK TABLES (partitioned by year)
echo ""
echo "Loading LINKTABLES table..."
bq load --source_format=PARQUET \
  --replace \
  --autodetect \
  --hive_partitioning_mode=AUTO \
  --hive_partitioning_source_uri_prefix="${BUCKET}/linktables_parquet" \
  ${PROJECT_ID}:${DATASET}.linktables \
  "${BUCKET}/linktables_parquet/*/*.parquet"

echo "✓ Link tables loaded"

# Load PATENTS (single file)
echo ""
echo "Loading PATENTS table..."
bq load --source_format=PARQUET \
  --replace \
  --autodetect \
  ${PROJECT_ID}:${DATASET}.patents \
  "${BUCKET}/patents_parquet/patents_ALL.parquet"

echo "✓ Patents loaded"

# Load CLINICAL STUDIES (single file)
echo ""
echo "Loading CLINICAL_STUDIES table..."
bq load --source_format=PARQUET \
  --replace \
  --autodetect \
  ${PROJECT_ID}:${DATASET}.clinical_studies \
  "${BUCKET}/clinicalstudies_parquet/clinicalstudies_ALL.parquet"

echo "✓ Clinical studies loaded"

echo ""
echo "======================================================================"
echo "Verifying tables..."
echo "======================================================================"
echo ""

# Verify each table
for TABLE in projects abstracts linktables patents clinical_studies; do
    echo "Checking ${TABLE}..."
    bq query --use_legacy_sql=false "
    SELECT 
      '${TABLE}' as table_name,
      COUNT(*) as row_count,
      MIN(FISCAL_YEAR) as min_year,
      MAX(FISCAL_YEAR) as max_year
    FROM \`${PROJECT_ID}.${DATASET}.${TABLE}\`
    " --format=pretty
done

echo ""
echo "======================================================================"
echo "✓ ALL TABLES LOADED!"
echo "======================================================================"
echo ""
echo "Dataset: ${PROJECT_ID}.${DATASET}"
echo ""
echo "Tables loaded:"
echo "  - projects (1990-2024)"
echo "  - abstracts (1990-2024)"
echo "  - linktables (1990-2024)"
echo "  - patents (all years)"
echo "  - clinical_studies (all years)"
