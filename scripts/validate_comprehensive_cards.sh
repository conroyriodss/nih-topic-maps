#!/bin/bash
set -e

echo "=========================================="
echo "COMPREHENSIVE CARDS VALIDATION"
echo "=========================================="
echo ""

echo "[1/4] IC Cards Coverage..."
bq query --use_legacy_sql=false << 'EOSQL'
SELECT
  COUNT(*) as num_ics,
  SUM(total_projects) as total_projects,
  SUM(total_funding_billions) as total_funding_b,
  SUM(rpg_standard_count) as total_rpg,
  SUM(centers_p_count) as total_centers,
  SUM(coop_agreements_u_count) as total_coop_agreements,
  SUM(training_t_count) as total_training
FROM `od-cl-odss-conroyri-f75a.nih_analytics.ic_cards_comprehensive`;
EOSQL

echo ""
echo "[2/4] PI Cards Coverage..."
bq query --use_legacy_sql=false << 'EOSQL'
SELECT
  COUNT(*) as num_pis,
  SUM(total_awards) as total_awards,
  ROUND(SUM(total_funding_millions)/1e3, 2) as total_funding_b,
  SUM(rpg_awards) as total_rpg,
  SUM(center_awards) as total_centers,
  SUM(training_awards) as total_training
FROM `od-cl-odss-conroyri-f75a.nih_analytics.pi_cards_comprehensive`;
EOSQL

echo ""
echo "[3/4] Institution Cards Coverage..."
bq query --use_legacy_sql=false << 'EOSQL'
SELECT
  COUNT(*) as num_institutions,
  SUM(total_awards) as total_awards,
  SUM(total_funding_billions) as total_funding_b,
  SUM(ul1_ctsa_awards) as total_ctsa,
  SUM(t32_awards) as total_t32,
  SUM(g12_rcmi_awards) as total_rcmi
FROM `od-cl-odss-conroyri-f75a.nih_analytics.institution_cards_comprehensive`;
EOSQL

echo ""
echo "[4/4] Temporal Trends Coverage..."
bq query --use_legacy_sql=false << 'EOSQL'
SELECT
  MIN(fiscal_year) as earliest_year,
  MAX(fiscal_year) as latest_year,
  COUNT(*) as num_years,
  SUM(total_awards) as cumulative_awards,
  SUM(total_funding_billions) as cumulative_funding_b
FROM `od-cl-odss-conroyri-f75a.nih_analytics.temporal_trends_comprehensive`;
EOSQL

echo ""
echo "=========================================="
echo "✅ VALIDATION COMPLETE"
echo "=========================================="
