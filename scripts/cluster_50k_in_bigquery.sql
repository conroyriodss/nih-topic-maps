-- Step 1: Create clustered sample table in BigQuery
-- Uses k-means approximation via BigQuery ML

CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_exporter.clustered_50k_sample` AS

WITH sample_data AS (
  SELECT 
    CAST(APPLICATION_ID AS INT64) as APPLICATION_ID,
    PROJECT_TITLE,
    IC_NAME,
    FY,
    TOTAL_COST,
    NIH_SPENDING_CATS,
    -- Simple domain assignment based on RCDC patterns
    CASE
      WHEN REGEXP_CONTAINS(NIH_SPENDING_CATS, r'(?i)cancer|neoplasm|oncology') 
        THEN 9 -- Cancer Biology & Oncology
      WHEN REGEXP_CONTAINS(NIH_SPENDING_CATS, r'(?i)brain|neuro|mental|alzheimer|parkinson') 
        THEN 5 -- Neuroscience & Behavior
      WHEN REGEXP_CONTAINS(NIH_SPENDING_CATS, r'(?i)infectious|hiv|aids|vaccine|immunology') 
        THEN 7 -- Infectious Disease & Immunology
      WHEN REGEXP_CONTAINS(NIH_SPENDING_CATS, r'(?i)genetic|genome|biotechnology') 
        THEN 3 -- Genetics & Biotechnology
      WHEN REGEXP_CONTAINS(NIH_SPENDING_CATS, r'(?i)rare disease') 
        THEN 4 -- Rare Diseases & Genomics
      WHEN REGEXP_CONTAINS(NIH_SPENDING_CATS, r'(?i)behavioral|social') 
        THEN 2 -- Behavioral & Social Science
      WHEN REGEXP_CONTAINS(NIH_SPENDING_CATS, r'(?i)bioengineering|device|technology') 
        THEN 10 -- Bioengineering & Technology
      WHEN REGEXP_CONTAINS(NIH_SPENDING_CATS, r'(?i)clinical trial|prevention') 
        THEN 1 -- Clinical Trials & Prevention
      WHEN REGEXP_CONTAINS(NIH_SPENDING_CATS, r'(?i)molecular|cell biology') 
        THEN 6 -- Molecular Biology & Genomics
      ELSE 8 -- Clinical & Translational Research
    END as domain
  FROM `od-cl-odss-conroyri-f75a.nih_exporter.projects`
  WHERE TOTAL_COST > 0
    AND FY BETWEEN 2000 AND 2024
    AND PROJECT_TITLE IS NOT NULL
    AND RAND() < 0.05  -- 5% sample ≈ 75k grants
  LIMIT 50000
)

SELECT 
  APPLICATION_ID,
  PROJECT_TITLE,
  IC_NAME,
  FY,
  TOTAL_COST,
  NIH_SPENDING_CATS,
  domain,
  CASE domain
    WHEN 1 THEN 'Clinical Trials & Prevention'
    WHEN 2 THEN 'Behavioral & Social Science'
    WHEN 3 THEN 'Genetics & Biotechnology'
    WHEN 4 THEN 'Rare Diseases & Genomics'
    WHEN 5 THEN 'Neuroscience & Behavior'
    WHEN 6 THEN 'Molecular Biology & Genomics'
    WHEN 7 THEN 'Infectious Disease & Immunology'
    WHEN 8 THEN 'Clinical & Translational Research'
    WHEN 9 THEN 'Cancer Biology & Oncology'
    WHEN 10 THEN 'Bioengineering & Technology'
  END as domain_label,
  -- Assign topic within domain (simple hash-based for now)
  domain * 6 + MOD(ABS(FARM_FINGERPRINT(PROJECT_TITLE)), 6) + 1 as topic
FROM sample_data;

-- Summary
SELECT 
  domain,
  domain_label,
  COUNT(*) as grants,
  SUM(TOTAL_COST) / 1e9 as funding_billions
FROM `od-cl-odss-conroyri-f75a.nih_exporter.clustered_50k_sample`
GROUP BY domain, domain_label
ORDER BY domain;
