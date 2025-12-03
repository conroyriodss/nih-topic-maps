CREATE OR REPLACE TABLE `od-cl-odss-conroyri-f75a.nih_exporter.awards_250k_for_clustering` AS

WITH eligible_awards AS (
  SELECT 
    core_project_num,
    administering_ic,
    ic_name,
    activity,
    project_title,
    primary_org,
    primary_state,
    first_fiscal_year,
    last_fiscal_year,
    distinct_fiscal_years,
    total_lifetime_funding,
    total_direct_costs,
    avg_annual_funding,
    all_pis,
    is_mpi,
    subproject_count,
    is_multisite,
    funding_category,
    award_type,
    CASE 
      WHEN first_fiscal_year < 2005 THEN '1990-2004'
      WHEN first_fiscal_year < 2015 THEN '2005-2014'
      ELSE '2015-2024'
    END as era,
    ROW_NUMBER() OVER (
      PARTITION BY 
        administering_ic,
        CASE 
          WHEN first_fiscal_year < 2005 THEN '1990-2004'
          WHEN first_fiscal_year < 2015 THEN '2005-2014'
          ELSE '2015-2024'
        END
      ORDER BY RAND()
    ) as rn
  FROM 
    `od-cl-odss-conroyri-f75a.nih_analytics.grant_scorecard_v2`
  WHERE 
    first_fiscal_year >= 2000
    AND project_title IS NOT NULL
    AND LENGTH(project_title) > 20
    AND activity IN ('R01', 'R21', 'R03', 'R15', 'R35', 'U01', 'U19', 'P01', 'P30', 'P50', 'DP1', 'DP2', 'DP5')
)
SELECT 
  core_project_num,
  administering_ic,
  ic_name,
  activity,
  project_title,
  primary_org,
  primary_state,
  first_fiscal_year,
  last_fiscal_year,
  distinct_fiscal_years,
  total_lifetime_funding,
  total_direct_costs,
  avg_annual_funding,
  all_pis,
  is_mpi,
  subproject_count,
  is_multisite,
  funding_category,
  award_type,
  era
FROM 
  eligible_awards
WHERE 
  rn <= CAST(250000.0 / (SELECT COUNT(DISTINCT administering_ic || era) FROM eligible_awards) AS INT64)
LIMIT 250000;
