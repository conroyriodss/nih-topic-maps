#!/bin/bash
# Run all validation scripts and generate comprehensive report

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_DIR="validation_reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="${REPORT_DIR}/validation_report_${TIMESTAMP}.txt"

echo "=========================================="
echo "NIH ExPORTER Validation Suite"
echo "=========================================="
echo ""

mkdir -p ${REPORT_DIR}

{
  echo "NIH ExPORTER COMPLETE VALIDATION REPORT"
  echo "Generated: $(date)"
  echo "========================================"
  echo ""
  
  echo "RUNNING: Table Counts and Coverage"
  echo "-----------------------------------"
  bash ${SCRIPT_DIR}/01_validate_table_counts.sh
  echo ""
  
  echo "RUNNING: Data Quality Checks"
  echo "----------------------------"
  bash ${SCRIPT_DIR}/02_validate_data_quality.sh
  echo ""
  
  echo "RUNNING: Schema Export"
  echo "----------------------"
  bash ${SCRIPT_DIR}/03_export_schemas.sh
  echo ""
  
  echo "========================================"
  echo "VALIDATION SUITE COMPLETE"
  echo "========================================"
  
} | tee ${REPORT_FILE}

echo ""
echo "Complete report saved to: ${REPORT_FILE}"
echo ""
echo "Summary of validation files:"
ls -lh ${REPORT_DIR}/
echo ""
echo "Schema files:"
ls -lh data/schemas/ 2>/dev/null || echo "Schema directory will be created on first run"
