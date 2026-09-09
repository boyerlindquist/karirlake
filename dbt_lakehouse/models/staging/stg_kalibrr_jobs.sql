WITH
    raw AS (
        SELECT
            *
        FROM
            {{source ('raw_data', 'kalibrr_jobs')}}
    )
SELECT
    job_id,
    search_keyword,
    title AS job_title,
    company_name,
    company_industry,
    company_url,
    CONCAT(
        'https://www.kalibrr.id/jobs/',
        CAST(job_id AS VARCHAR)
    ) AS job_url,
    city AS location_city,
    -- 1. Status Hubungan Kerja (Tipe Kontrak)
    CASE 
        WHEN LOWER(employment_type) LIKE '%full%' THEN 'Full-time'
        WHEN LOWER(employment_type) LIKE '%contract%' THEN 'Contract'
        WHEN LOWER(employment_type) LIKE '%part%' THEN 'Part-time'
        WHEN LOWER(employment_type) LIKE '%intern%' THEN 'Internship'
        WHEN LOWER(employment_type) LIKE '%freelance%' OR LOWER(employment_type) LIKE '%project%' THEN 'Freelance'
        ELSE COALESCE(employment_type, 'Not Specified')
    END AS employment_type,
    -- 2. Skema Lokasi Kehadiran Fisik
    CASE 
        WHEN is_wfh = TRUE THEN 'Remote'
        WHEN is_hybrid = TRUE THEN 'Hybrid'
        ELSE 'Onsite'
    END AS work_arrangement,
    -- Alias work_type untuk kompatibilitas downstream
    CASE 
        WHEN is_wfh = TRUE THEN 'Remote'
        WHEN is_hybrid = TRUE THEN 'Hybrid'
        ELSE 'Onsite'
    END AS work_type,
    CAST(base_salary AS BIGINT) AS salary_min,
    CAST(max_salary AS BIGINT) AS salary_max,
    salary_currency,
    -- education_level,
    CASE CAST(education_level AS VARCHAR)
        WHEN '550' THEN 'Bachelor'
        WHEN '500' THEN 'Bachelor'
        WHEN '450' THEN 'Diploma'
        WHEN '400' THEN 'Diploma'
        WHEN '200' THEN 'High School'
        WHEN '100' THEN 'High School'
        WHEN '600' THEN 'Master'
        WHEN '700' THEN 'Doctorate'
        ELSE COALESCE(CAST(education_level AS VARCHAR), 'Not Specified')
    END AS education_level,
    -- CASE
    --     WHEN education_level = '200' THEN 'High School'
    --     WHEN education_level = '550' THEN 'Bachelor Degree'
    --     ELSE 'Unknown Degree'
    -- END AS education_level,
    CAST(
        CASE
            WHEN work_experience >= 100 THEN work_experience // 100
            ELSE work_experience
        END AS VARCHAR
    ) AS min_experience,
    -- CAST(work_experience AS VARCHAR) AS min_experience,
    CAST(posted_at AS TIMESTAMP) AS posted_at,
    CAST(deadline_at AS TIMESTAMP) AS deadline_at,
    skills,
    'Kalibrr' AS source_platform
FROM
    raw
QUALIFY
    ROW_NUMBER() OVER (
        PARTITION BY
            job_id
        ORDER BY
            posted_at DESC
    ) = 1