#!/bin/bash
set -e
echo "=========================================="
echo "CREATING IC/AGENCY HIERARCHY SCHEMA"
echo "=========================================="
echo ""

echo "[1/3] Creating agency hierarchy table..."

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.ic_agency_hierarchy` AS
WITH ic_mapping AS (
  SELECT 'AA' as ic_code, 'National Institute on Alcohol Abuse and Alcoholism' as ic_name, 'NIH' as agency, 'Research IC' as ic_type, 'HHS' as department, 1 as sort_order
  UNION ALL SELECT 'AG', 'National Institute on Aging', 'NIH', 'Research IC', 'HHS', 2
  UNION ALL SELECT 'AI', 'National Institute of Allergy and Infectious Diseases', 'NIH', 'Research IC', 'HHS', 3
  UNION ALL SELECT 'AR', 'National Institute of Arthritis and Musculoskeletal and Skin Diseases', 'NIH', 'Research IC', 'HHS', 4
  UNION ALL SELECT 'AT', 'National Center for Advancing Translational Sciences', 'NIH', 'Research IC', 'HHS', 5
  UNION ALL SELECT 'CA', 'National Cancer Institute', 'NIH', 'Research IC', 'HHS', 6
  UNION ALL SELECT 'DA', 'National Institute on Drug Abuse', 'NIH', 'Research IC', 'HHS', 7
  UNION ALL SELECT 'DC', 'National Institute on Deafness and Other Communication Disorders', 'NIH', 'Research IC', 'HHS', 8
  UNION ALL SELECT 'DE', 'National Institute of Dental and Craniofacial Research', 'NIH', 'Research IC', 'HHS', 9
  UNION ALL SELECT 'DK', 'National Institute of Diabetes and Digestive and Kidney Diseases', 'NIH', 'Research IC', 'HHS', 10
  UNION ALL SELECT 'EB', 'National Institute of Biomedical Imaging and Bioengineering', 'NIH', 'Research IC', 'HHS', 11
  UNION ALL SELECT 'ES', 'National Institute of Environmental Health Sciences', 'NIH', 'Research IC', 'HHS', 12
  UNION ALL SELECT 'EY', 'National Eye Institute', 'NIH', 'Research IC', 'HHS', 13
  UNION ALL SELECT 'GM', 'National Institute of General Medical Sciences', 'NIH', 'Research IC', 'HHS', 14
  UNION ALL SELECT 'HD', 'Eunice Kennedy Shriver National Institute of Child Health and Human Development', 'NIH', 'Research IC', 'HHS', 15
  UNION ALL SELECT 'HG', 'National Human Genome Research Institute', 'NIH', 'Research IC', 'HHS', 16
  UNION ALL SELECT 'HL', 'National Heart, Lung, and Blood Institute', 'NIH', 'Research IC', 'HHS', 17
  UNION ALL SELECT 'LM', 'National Library of Medicine', 'NIH', 'Research IC', 'HHS', 18
  UNION ALL SELECT 'MD', 'National Institute on Minority Health and Health Disparities', 'NIH', 'Research IC', 'HHS', 19
  UNION ALL SELECT 'MH', 'National Institute of Mental Health', 'NIH', 'Research IC', 'HHS', 20
  UNION ALL SELECT 'NR', 'National Institute of Nursing Research', 'NIH', 'Research IC', 'HHS', 21
  UNION ALL SELECT 'NS', 'National Institute of Neurological Disorders and Stroke', 'NIH', 'Research IC', 'HHS', 22
  
  -- NIH Support/Administrative
  UNION ALL SELECT 'CC', 'NIH Clinical Center', 'NIH', 'Support IC', 'HHS', 23
  UNION ALL SELECT 'CIT', 'Center for Information Technology', 'NIH', 'Support IC', 'HHS', 24
  UNION ALL SELECT 'CSR', 'Center for Scientific Review', 'NIH', 'Support IC', 'HHS', 25
  UNION ALL SELECT 'FIC', 'Fogarty International Center', 'NIH', 'Support IC', 'HHS', 26
  UNION ALL SELECT 'OD', 'Office of the Director', 'NIH', 'Support IC', 'HHS', 27
  UNION ALL SELECT 'RR', 'National Center for Research Resources (Legacy)', 'NIH', 'Support IC', 'HHS', 28
  
  -- NIH Common Fund
  UNION ALL SELECT 'RM', 'NIH Common Fund', 'NIH', 'Common Fund', 'HHS', 29
  
  -- Other HHS Agencies
  UNION ALL SELECT 'FDA', 'Food and Drug Administration', 'FDA', 'Regulatory', 'HHS', 30
  UNION ALL SELECT 'FD', 'FDA Orphan Products', 'FDA', 'Regulatory', 'HHS', 31
  UNION ALL SELECT 'CD', 'Centers for Disease Control and Prevention', 'CDC', 'Public Health', 'HHS', 32
  UNION ALL SELECT 'HS', 'Agency for Healthcare Research and Quality', 'AHRQ', 'Health Services', 'HHS', 33
  UNION ALL SELECT 'HR', 'Health Resources and Services Administration', 'HRSA', 'Health Services', 'HHS', 34
  
  -- Other Federal
  UNION ALL SELECT 'VA', 'Department of Veterans Affairs', 'VA', 'Veterans Health', 'VA', 35
  UNION ALL SELECT 'DOD', 'Department of Defense', 'DOD', 'Defense', 'DOD', 36
  UNION ALL SELECT 'DOE', 'Department of Energy', 'DOE', 'Energy', 'DOE', 37
  UNION ALL SELECT 'NASA', 'National Aeronautics and Space Administration', 'NASA', 'Space', 'NASA', 38
  
  -- Special codes
  UNION ALL SELECT 'OH', 'Other HHS Agencies', 'HHS', 'Other', 'HHS', 39
  UNION ALL SELECT 'TR', 'Trans-NIH', 'NIH', 'Trans-NIH', 'HHS', 40
  UNION ALL SELECT 'CK', 'Common Fund Keck', 'NIH', 'Common Fund', 'HHS', 41
  UNION ALL SELECT 'TW', 'Fogarty International (Legacy)', 'NIH', 'Support IC', 'HHS', 42
  UNION ALL SELECT 'TS', 'Trans-NIH Special', 'NIH', 'Trans-NIH', 'HHS', 43
  UNION ALL SELECT 'DD', 'NIH Data Discovery', 'NIH', 'Support IC', 'HHS', 44
  UNION ALL SELECT 'CE', 'Common Fund Exceptional Research', 'NIH', 'Common Fund', 'HHS', 45
)
SELECT * FROM ic_mapping
ORDER BY sort_order;
EOSQL

echo "  ✓ Created ic_agency_hierarchy table"

echo ""
echo "[2/3] Adding hierarchy columns to grant cards..."

bq query --use_legacy_sql=false << 'EOSQL'
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency` AS
SELECT 
  g.*,
  
  -- Add IC hierarchy
  COALESCE(h.ic_name, 'Unknown IC') as ic_full_name,
  COALESCE(h.agency, 'Unknown') as funding_agency,
  COALESCE(h.ic_type, 'Unknown') as ic_type,
  COALESCE(h.department, 'Unknown') as department,
  
  -- Organizational categories
  CASE 
    WHEN h.agency = 'NIH' AND h.ic_type = 'Research IC' THEN 'NIH Research'
    WHEN h.agency = 'NIH' AND h.ic_type = 'Support IC' THEN 'NIH Support'
    WHEN h.agency = 'NIH' AND h.ic_type = 'Common Fund' THEN 'NIH Common Fund'
    WHEN h.agency = 'NIH' AND h.ic_type = 'Trans-NIH' THEN 'NIH Trans-IC'
    WHEN h.agency = 'FDA' THEN 'FDA'
    WHEN h.agency = 'CDC' THEN 'CDC'
    WHEN h.department = 'HHS' THEN 'Other HHS'
    WHEN h.department IN ('VA', 'DOD', 'NASA', 'DOE') THEN h.department
    ELSE 'Other Federal'
  END as organizational_category

FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_5_hierarchical` g
LEFT JOIN `od-cl-odss-conroyri-f75a.nih_analytics.ic_agency_hierarchy` h
  ON g.ADMINISTERING_IC = h.ic_code;
EOSQL

echo "  ✓ Created grant_cards_v1_6_with_agency table"

echo ""
echo "[3/3] Creating summary views..."

bq query --use_legacy_sql=false << 'EOSQL'
-- Agency portfolio summary
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.portfolio_by_agency` AS
SELECT 
  department,
  funding_agency,
  organizational_category,
  COUNT(*) as num_awards,
  COUNT(DISTINCT ADMINISTERING_IC) as num_ics,
  ROUND(SUM(TOTAL_LIFETIME_FUNDING)/1e9, 2) as funding_billions,
  ROUND(AVG(publication_count), 1) as avg_pubs,
  COUNTIF(is_mpi) as mpi_awards,
  ROUND(COUNTIF(is_mpi) * 100.0 / COUNT(*), 1) as pct_mpi,
  MIN(FIRST_FISCAL_YEAR) as earliest_year,
  MAX(LAST_FISCAL_YEAR) as latest_year
FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency`
GROUP BY department, funding_agency, organizational_category
ORDER BY funding_billions DESC;

-- IC detail with agency context
CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_analytics.portfolio_by_ic_detailed` AS
SELECT 
  h.department,
  h.agency as funding_agency,
  h.ic_type,
  h.ic_code as ADMINISTERING_IC,
  h.ic_name,
  g.organizational_category,
  COUNT(*) as num_awards,
  ROUND(SUM(g.TOTAL_LIFETIME_FUNDING)/1e9, 2) as funding_billions,
  ROUND(AVG(g.publication_count), 1) as avg_pubs,
  ROUND(AVG(g.pi_count), 2) as avg_pi_count,
  COUNTIF(g.is_mpi) as mpi_awards,
  ROUND(COUNTIF(g.is_mpi) * 100.0 / COUNT(*), 1) as pct_mpi,
  APPROX_TOP_COUNT(g.ACTIVITY, 5) as top_mechanisms
FROM `od-cl-odss-conroyri-f75a.nih_analytics.grant_cards_v1_6_with_agency` g
JOIN `od-cl-odss-conroyri-f75a.nih_analytics.ic_agency_hierarchy` h
  ON g.ADMINISTERING_IC = h.ic_code
GROUP BY h.department, h.agency, h.ic_type, h.ic_code, h.ic_name, g.organizational_category
ORDER BY funding_billions DESC;
EOSQL

echo "  ✓ Created summary tables"

echo ""
echo "=========================================="
echo "✅ IC HIERARCHY COMPLETE"
echo "=========================================="
echo ""
echo "Created Tables:"
echo "  1. ic_agency_hierarchy (45 IC/agency codes)"
echo "  2. grant_cards_v1_6_with_agency (1.26M cards with hierarchy)"
echo "  3. portfolio_by_agency (agency-level summary)"
echo "  4. portfolio_by_ic_detailed (IC-level with agency context)"
echo ""
echo "New Columns Added:"
echo "  - ic_full_name (full institute name)"
echo "  - funding_agency (NIH, FDA, CDC, VA, etc.)"
echo "  - ic_type (Research IC, Support IC, Common Fund, etc.)"
echo "  - department (HHS, VA, DOD, NASA, DOE)"
echo "  - organizational_category (NIH Research, FDA, Other HHS, etc.)"
echo ""
echo "Hierarchy Levels:"
echo "  Department → Agency → IC Type → IC Code"
echo "  Example: HHS → NIH → Research IC → CA"
echo ""
echo "=========================================="
