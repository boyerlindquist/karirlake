WITH
    raw AS (
        SELECT
            *
        FROM
            {{source ('raw_data', 'glints_jobs')}}
    )
SELECT
    job_id,
    search_keyword,
    job_title,
    company_name,
    company_industry,
    company_url,
    CONCAT(
        'https://glints.com/id/opportunities/jobs/',
        job_id
    ) AS job_url,
    city AS location_city,
    -- 1. Status Hubungan Kerja (Tipe Kontrak)
    CASE UPPER(COALESCE(employment_type, ''))
        WHEN 'FULL_TIME'  THEN 'Full-time'
        WHEN 'CONTRACT'   THEN 'Contract'
        WHEN 'INTERNSHIP' THEN 'Internship'
        WHEN 'PART_TIME'  THEN 'Part-time'
        WHEN 'PROJECT'    THEN 'Freelance'
        ELSE 'Not Specified'
    END AS employment_type,
    -- 2. Skema Lokasi Kehadiran Fisik
    CASE UPPER(COALESCE(work_arrangement, work_type, ''))
        WHEN 'ONSITE' THEN 'Onsite'
        WHEN 'HYBRID' THEN 'Hybrid'
        WHEN 'REMOTE' THEN 'Remote'
        ELSE 'Not Specified'
    END AS work_arrangement,
    -- Alias work_type untuk kompatibilitas downstream
    CASE UPPER(COALESCE(work_arrangement, work_type, ''))
        WHEN 'ONSITE' THEN 'Onsite'
        WHEN 'HYBRID' THEN 'Hybrid'
        WHEN 'REMOTE' THEN 'Remote'
        ELSE 'Not Specified'
    END AS work_type,
    CAST(salary_min AS BIGINT) AS salary_min,
    CAST(salary_max AS BIGINT) AS salary_max,
    currency AS salary_currency,
    -- education_level,
    -- CASE
    --     WHEN education_level = 'BACHELOR_DEGREE' THEN 'Bachelor Degree'
    --     WHEN education_level = 'DIPLOMA' THEN 'Diploma'
    --     WHEN education_level = 'HIGH_SCHOOL' THEN 'High School'
    --     ELSE 'Unknown Degree'
    -- END AS education_level,
    CASE UPPER(education_level)
        WHEN 'BACHELOR_DEGREE' THEN 'Bachelor'
        WHEN 'DIPLOMA' THEN 'Diploma'
        WHEN 'HIGH_SCHOOL' THEN 'High School'
        WHEN 'MASTER_DEGREE' THEN 'Master'
        WHEN 'DOCTORATE' THEN 'Doctorate'
        ELSE COALESCE(education_level, 'Not Specified')
    END AS education_level,
    CAST(min_experience AS VARCHAR) AS min_experience,
    CAST(posted_at AS TIMESTAMP) AS posted_at,
    CAST(deadline_at AS TIMESTAMP) AS deadline_at,
    skills,
    'Glints' AS source_platform
FROM
    raw
QUALIFY
    ROW_NUMBER() OVER (
        PARTITION BY
            job_id
        ORDER BY
            posted_at DESC
    ) = 1