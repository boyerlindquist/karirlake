{{ config(materialized='table') }}

WITH base_jobs AS (
    SELECT * FROM {{ ref('init_all_jobs') }}
)

SELECT 
    standard_role AS job_category,
    COALESCE(location_city, 'Remote / Not Specified') AS location_city,
    source_platform,
    COUNT(*) AS total_jobs
FROM base_jobs
GROUP BY 1, 2, 3
ORDER BY total_jobs DESC
