{{ config(materialized='table') }}

WITH base_jobs AS (
    SELECT * FROM {{ ref('init_all_jobs') }}
)

SELECT 
    standard_role AS job_category,
    COALESCE(education_level, 'Not Specified') AS education_level,
    COALESCE(CAST(min_experience AS VARCHAR), 'Not Specified') AS min_experience,
    COUNT(*) AS total_jobs
FROM base_jobs
GROUP BY 1, 2, 3
ORDER BY job_category ASC, total_jobs DESC
