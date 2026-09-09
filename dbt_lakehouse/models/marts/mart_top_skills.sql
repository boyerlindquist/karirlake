{{ config(materialized='table') }}

WITH base_jobs AS (
    SELECT * FROM {{ ref('init_all_jobs') }}
),

unnested_skills AS (
    SELECT 
        standard_role,
        UNNEST(skills) AS skill_name
    FROM base_jobs
    WHERE skills IS NOT NULL
)

SELECT 
    standard_role AS job_category,
    skill_name,
    COUNT(*) AS total_demand
FROM unnested_skills
WHERE skill_name != ''
GROUP BY 1, 2
ORDER BY job_category ASC, total_demand DESC
