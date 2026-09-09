{{ config(materialized='table') }}

WITH kalibrr AS (
    SELECT * FROM {{ ref('stg_kalibrr_jobs') }}
),

glints AS (
    SELECT * FROM {{ ref('stg_glints_jobs') }}
),

unioned AS (
    SELECT * FROM kalibrr
    UNION ALL
    SELECT * FROM glints
),

classified AS (
    SELECT 
        *,
        CASE 
            -- 1. Data Engineer & ETL
            WHEN LOWER(job_title) LIKE '%data%engineer%' 
              OR LOWER(job_title) LIKE '%etl%' 
              OR LOWER(job_title) LIKE '%big%data%'
              OR LOWER(job_title) LIKE '%data%pipeline%'
              OR LOWER(job_title) LIKE '%data%infra%'
            THEN 'Data Engineer'

            -- 2. Data Analyst & BI (Nangkep 'Analyst', 'Analisis', 'Analis data', 'BI')
            WHEN LOWER(job_title) LIKE '%data%analys%' 
              OR LOWER(job_title) LIKE '%analis%data%' 
              OR LOWER(job_title) LIKE '%business%intelligence%' 
              OR LOWER(job_title) LIKE '%bi%analys%'
              OR LOWER(job_title) LIKE '%bi%developer%'
            THEN 'Data Analyst'

            -- 3. Data Scientist & AI (Nangkep 'Scientist', 'Science', 'Scienstist', 'Machine Learning')
            WHEN LOWER(job_title) LIKE '%data%scien%' 
              OR LOWER(job_title) LIKE '%machine%learning%' 
              OR LOWER(job_title) LIKE '%ml%engineer%'
              OR LOWER(job_title) LIKE '%ai%engineer%' 
            THEN 'Data Scientist'

            -- 4. Database Administrator (DBA & RDBMS, buang admin toko/finance/marketplace)
            WHEN (
                LOWER(job_title) LIKE '%database%' 
                OR LOWER(job_title) LIKE '%dba%'
                OR LOWER(job_title) LIKE '%rdbms%'
            )
             AND LOWER(job_title) NOT LIKE '%marketplace%'
             AND LOWER(job_title) NOT LIKE '%finance%'
             AND LOWER(job_title) NOT LIKE '%online%'
             AND LOWER(job_title) NOT LIKE '%admin %'
             AND LOWER(job_title) NOT LIKE '%administrasi%'
            THEN 'Database Administrator'

            -- 5. Data Architect (Buang arsitek kapal, lanskap, interior, konstruksi/BIM)
            WHEN LOWER(job_title) LIKE '%data%architect%' 
              OR (
                  LOWER(job_title) LIKE '%solution%architect%' 
                  AND LOWER(job_title) NOT LIKE '%naval%' 
                  AND LOWER(job_title) NOT LIKE '%landscape%'
                  AND LOWER(job_title) NOT LIKE '%interior%'
                  AND LOWER(job_title) NOT LIKE '%bim%'
                  AND LOWER(job_title) NOT LIKE '%building%'
              )
            THEN 'Data Architect'

            -- Sisanya masuk kategori sampah/non-data
            ELSE 'Other'
        END AS standard_role
    FROM unioned
)

SELECT * 
FROM classified
WHERE standard_role != 'Other'
