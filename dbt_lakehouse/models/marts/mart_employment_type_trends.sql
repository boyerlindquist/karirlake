{{ config(materialized='table') }}

WITH base_jobs AS (
    SELECT * FROM {{ ref('init_all_jobs') }}
)

SELECT 
    standard_role AS job_category,
    COALESCE(employment_type, 'Not Specified') AS employment_type,
    COUNT(*) AS total_jobs
FROM base_jobs
GROUP BY 1, 2
ORDER BY job_category ASC, total_jobs DESC
