{{ config(materialized='table') }}

WITH base_jobs AS (
    SELECT * FROM {{ ref('init_all_jobs') }}
),

filtered_salaries AS (
    SELECT 
        standard_role,
        location_city,
        salary_min,
        salary_max,
        (salary_min + salary_max) / 2.0 AS salary_mid
    FROM base_jobs
    WHERE salary_currency = 'IDR'
      AND salary_min IS NOT NULL
      AND salary_max IS NOT NULL
)

SELECT 
    standard_role AS job_category,
    location_city,
    COUNT(*) AS total_jobs_with_salary,
    CAST(AVG(salary_min) AS BIGINT) AS avg_salary_min,
    CAST(AVG(salary_max) AS BIGINT) AS avg_salary_max,
    CAST(AVG(salary_mid) AS BIGINT) AS avg_salary_mid
FROM filtered_salaries
GROUP BY 1, 2
ORDER BY job_category ASC, avg_salary_mid DESC
