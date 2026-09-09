{{ config(materialized='table') }}

WITH base_jobs AS (
    SELECT * FROM {{ ref('init_all_jobs') }}
)

SELECT
    standard_role as job_category,
    company_name,
    COALESCE(company_industry, 'Not Specified') AS company_industry,
    source_platform,
    COUNT(*) AS total_openings,
    COUNT(DISTINCT standard_role) AS distinct_roles_hiring
FROM base_jobs
WHERE company_name IS NOT NULL
GROUP BY 1, 2, 3,4
ORDER BY total_openings DESC
