#!/bin/bash
# Export all table schemas to JSON files for documentation

PROJECT="od-cl-odss-conroyri-f75a"
DATASET="nih_exporter"
OUTPUT_DIR="data/schemas"

echo "=========================================="
echo "Exporting BigQuery Schemas"
echo "=========================================="
echo ""

mkdir -p ${OUTPUT_DIR}

for table in projects abstracts linktables patents clinicalstudies; do
  echo "Exporting schema for ${table}..."
  bq show --schema --format=prettyjson ${PROJECT}:${DATASET}.${table} > ${OUTPUT_DIR}/${table}_schema.json
  bq show --format=prettyjson ${PROJECT}:${DATASET}.${table} > ${OUTPUT_DIR}/${table}_metadata.json
  echo "  ✓ ${OUTPUT_DIR}/${table}_schema.json"
  echo "  ✓ ${OUTPUT_DIR}/${table}_metadata.json"
done

echo ""
echo "Creating schema summary..."
cat > ${OUTPUT_DIR}/README.md << 'SCHEMAEOF'
# NIH ExPORTER BigQuery Schema Documentation

## Overview

This directory contains the complete schema definitions for all tables in the `nih_exporter` BigQuery dataset.

## Files

| File | Description |
|------|-------------|
| `projects_schema.json` | Schema for projects table (2.6M rows, FY1990-2024) |
| `abstracts_schema.json` | Schema for abstracts table (2.3M rows, FY1990-2024) |
| `linktables_schema.json` | Schema for linktables (project-publication links) |
| `patents_schema.json` | Schema for patents table (85K rows) |
| `clinicalstudies_schema.json` | Schema for clinical studies (37K rows) |

## Schema Version History

- **v1.0** (2025-11-25): Initial schema export from consolidated nih_exporter dataset

## Usage

These JSON files can be used for:
- Documentation and reference
- Programmatic schema validation
- Table recreation in other environments
- Data dictionary generation

## Notes

- All schemas exported from location: `US` (multi-region)
- Source project: `od-cl-odss-conroyri-f75a`
- Dataset: `nih_exporter`
SCHEMAEOF

echo "  ✓ ${OUTPUT_DIR}/README.md"
echo ""
echo "Schema export complete! Files saved to ${OUTPUT_DIR}/"
