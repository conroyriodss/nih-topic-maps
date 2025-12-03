#!/bin/bash
# check_bigquery_schema.sh
# Identify available text columns in BigQuery projects table

echo "========================================================================"
echo "BIGQUERY SCHEMA ANALYSIS"
echo "========================================================================"

echo ""
echo "[1] All columns in projects table:"
bq show --schema --format=prettyjson od-cl-odss-conroyri-f75a:nih_exporter.projects | \
  jq -r '.[] | .name' | sort

echo ""
echo "[2] Text-related columns:"
bq show --schema --format=prettyjson od-cl-odss-conroyri-f75a:nih_exporter.projects | \
  jq -r '.[] | select(.name | ascii_upcase | contains("TITLE") or contains("TEXT") or contains("ABSTRACT") or contains("TERM") or contains("DESC")) | .name'

echo ""
echo "[3] String type columns (first 20):"
bq show --schema --format=prettyjson od-cl-odss-conroyri-f75a:nih_exporter.projects | \
  jq -r '.[] | select(.type == "STRING") | .name' | head -20

echo ""
echo "[4] Sample row to see what data is available:"
bq query --use_legacy_sql=false --max_rows=1 \
  "SELECT * FROM od-cl-odss-conroyri-f75a.nih_exporter.projects LIMIT 1"

echo ""
echo "========================================================================"
