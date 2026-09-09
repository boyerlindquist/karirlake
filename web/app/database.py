import os
import duckdb
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "lakehouse.duckdb"))

def get_db_connection():
    return duckdb.connect(DB_PATH, read_only=True)

def get_overview_kpis():
    con = get_db_connection()
    try:
        # 1. Total Loker Terverifikasi
        total_jobs = con.execute("SELECT COUNT(*) FROM init_all_jobs").fetchone()[0]

        # 2. Rata-rata Gaji Pasar
        avg_salary = con.execute("""
            SELECT COALESCE(AVG(avg_salary_mid), 0) 
            FROM mart_salary_insights
        """).fetchone()[0]

        # 3. Rasio Remote Work (%)
        remote_jobs = con.execute("""
            SELECT COALESCE(SUM(total_jobs), 0) 
            FROM mart_work_arrangement_trends 
            WHERE LOWER(work_type) LIKE '%remote%' OR LOWER(work_type) LIKE '%wfh%'
        """).fetchone()[0]
        remote_pct = (remote_jobs / total_jobs * 100) if total_jobs > 0 else 0

        # 4. Total Perusahaan Merekrut
        total_companies = con.execute("""
            SELECT COUNT(DISTINCT company_name) 
            FROM mart_company_hiring_activity
        """).fetchone()[0]

        return {
            "total_jobs": total_jobs,
            "avg_salary": int(avg_salary),
            "remote_pct": round(remote_pct, 1),
            "total_companies": total_companies
        }
    finally:
        con.close()

def get_available_roles():
    con = get_db_connection()
    try:
        roles = con.execute("""
            SELECT DISTINCT job_category 
            FROM mart_top_skills 
            ORDER BY job_category ASC
        """).fetchall()
        return [r[0] for r in roles]
    finally:
        con.close()

def categorize_experience(min_exp):
    """Categorize minimum experience years into industry-standard seniority tiers."""
    if min_exp is None or str(min_exp).strip() in ("", "Not Specified", "None", "nan"):
        return {
            "tier": "Not Specified",
            "display": "Not Specified",
            "tier_short": "Unspecified",
            "badge_class": "badge-exp-unspecified"
        }
    try:
        val = float(min_exp)
        if val < 1:
            return {
                "tier": "Entry Level",
                "display": "0 thn (Entry)",
                "tier_short": "Entry",
                "badge_class": "badge-exp-entry"
            }
        elif val <= 2:
            return {
                "tier": "Junior",
                "display": f"{int(val)} thn (Junior)",
                "tier_short": "Junior",
                "badge_class": "badge-exp-junior"
            }
        elif val <= 4:
            return {
                "tier": "Mid-Level",
                "display": f"{int(val)} thn (Mid)",
                "tier_short": "Mid",
                "badge_class": "badge-exp-mid"
            }
        elif val <= 7:
            return {
                "tier": "Senior",
                "display": f"{int(val)} thn (Senior)",
                "tier_short": "Senior",
                "badge_class": "badge-exp-senior"
            }
        else:
            return {
                "tier": "Lead / Principal",
                "display": f"{int(val)}+ thn (Lead)",
                "tier_short": "Lead",
                "badge_class": "badge-exp-lead"
            }
    except (ValueError, TypeError):
        return {
            "tier": str(min_exp),
            "display": str(min_exp),
            "tier_short": str(min_exp),
            "badge_class": "badge-exp-unspecified"
        }

def get_role_insights(role="Data Engineer"):
    con = get_db_connection()
    try:
        # 1. Top Skills (Ranking skill paling dicari)
        top_skills = con.execute("""
            SELECT skill_name, total_demand 
            FROM mart_top_skills 
            WHERE LOWER(job_category) = LOWER(?) 
            ORDER BY total_demand DESC 
            LIMIT 12
        """, [role]).fetchall()

        # 2. Salary Benchmark by City (Min, Mid, Max)
        salaries = con.execute("""
            SELECT location_city, avg_salary_min, avg_salary_mid, avg_salary_max 
            FROM mart_salary_insights 
            WHERE LOWER(job_category) = LOWER(?) 
            ORDER BY avg_salary_mid DESC 
            LIMIT 6
        """, [role]).fetchall()

        # 3. Work Arrangements (WFH / Hybrid / Onsite)
        work_arrangements = con.execute("""
            SELECT work_type, total_jobs 
            FROM mart_work_arrangement_trends 
            WHERE LOWER(job_category) = LOWER(?) 
            ORDER BY total_jobs DESC
        """, [role]).fetchall()

        # 4. Employment Types (Full-time, Contract, Internship, Part-time)
        employment_types = con.execute("""
            SELECT employment_type, total_jobs 
            FROM mart_employment_type_trends 
            WHERE LOWER(job_category) = LOWER(?) 
            ORDER BY total_jobs DESC
        """, [role]).fetchall()

        # 5. Education Requirements (Tingkat Pendidikan)
        education_reqs = con.execute("""
            SELECT education_level, SUM(total_jobs) as count
            FROM mart_experience_education_reqs 
            WHERE LOWER(job_category) = LOWER(?) 
            GROUP BY 1
            ORDER BY count DESC
            LIMIT 5
        """, [role]).fetchall()

        # 6. Experience Seniority Tiers
        experience_tiers_raw = con.execute("""
            SELECT 
                CASE 
                    WHEN min_experience IS NULL OR TRIM(min_experience) = '' OR min_experience = 'Not Specified' THEN 'Not Specified'
                    WHEN TRY_CAST(min_experience AS FLOAT) < 1 THEN 'Entry Level'
                    WHEN TRY_CAST(min_experience AS FLOAT) <= 2 THEN 'Junior'
                    WHEN TRY_CAST(min_experience AS FLOAT) <= 4 THEN 'Mid-Level'
                    WHEN TRY_CAST(min_experience AS FLOAT) <= 7 THEN 'Senior'
                    ELSE 'Lead / Principal'
                END AS exp_tier,
                COUNT(*) as count
            FROM init_all_jobs
            WHERE LOWER(standard_role) = LOWER(?)
            GROUP BY 1
            ORDER BY 
                CASE exp_tier
                    WHEN 'Entry Level' THEN 1
                    WHEN 'Junior' THEN 2
                    WHEN 'Mid-Level' THEN 3
                    WHEN 'Senior' THEN 4
                    WHEN 'Lead / Principal' THEN 5
                    ELSE 6
                END ASC
        """, [role]).fetchall()

        # 7. Top Hiring Companies (Perusahaan paling aktif merekrut role ini)
        top_companies = con.execute("""
            SELECT company_name, company_industry, total_openings 
            FROM mart_company_hiring_activity 
            WHERE LOWER(job_category) = LOWER(?) 
            ORDER BY total_openings DESC 
            LIMIT 8
        """, [role]).fetchall()

        # 8. Location Demand (Sebaran kota pembuka lowongan)
        locations = con.execute("""
            SELECT location_city, total_jobs 
            FROM mart_location_demand 
            WHERE LOWER(job_category) = LOWER(?) 
            ORDER BY total_jobs DESC 
            LIMIT 7
        """, [role]).fetchall()

        # 9. Role-specific KPIs
        role_total_jobs = con.execute("""
            SELECT COUNT(*) FROM init_all_jobs WHERE LOWER(standard_role) = LOWER(?)
        """, [role]).fetchone()[0]

        role_avg_salary = con.execute("""
            SELECT COALESCE(AVG(avg_salary_mid), 0) FROM mart_salary_insights WHERE LOWER(job_category) = LOWER(?)
        """, [role]).fetchone()[0]

        role_remote_jobs = con.execute("""
            SELECT COALESCE(SUM(total_jobs), 0) FROM mart_work_arrangement_trends 
            WHERE LOWER(job_category) = LOWER(?) AND (LOWER(work_type) LIKE '%remote%' OR LOWER(work_type) LIKE '%wfh%')
        """, [role]).fetchone()[0]
        role_remote_pct = (role_remote_jobs / role_total_jobs * 100) if role_total_jobs > 0 else 0

        role_companies = con.execute("""
            SELECT COUNT(DISTINCT company_name) FROM mart_company_hiring_activity WHERE LOWER(job_category) = LOWER(?)
        """, [role]).fetchone()[0]

        return {
            "kpis": {
                "total_jobs": role_total_jobs,
                "avg_salary": int(role_avg_salary),
                "remote_pct": round(role_remote_pct, 1),
                "total_companies": role_companies
            },
            "top_skills": [{"name": r[0], "demand": r[1]} for r in top_skills],
            "salaries": [{"city": r[0], "min": r[1], "mid": r[2], "max": r[3]} for r in salaries],
            "work_arrangements": [{"type": r[0], "count": r[1]} for r in work_arrangements],
            "employment_types": [{"type": r[0], "count": r[1]} for r in employment_types],
            "education_reqs": [{"level": r[0], "count": r[1]} for r in education_reqs],
            "experience_tiers": [{"tier": r[0], "count": r[1]} for r in experience_tiers_raw],
            "top_companies": [{"name": r[0], "industry": r[1], "openings": r[2]} for r in top_companies],
            "locations": [{"city": r[0], "count": r[1]} for r in locations]
        }
    finally:
        con.close()

def format_relative_date(dt):
    """Format datetime into friendly relative or localized date string."""
    if not dt:
        return "Not Specified"
    from datetime import datetime
    now = datetime.now()
    diff = now - dt
    days = diff.days
    seconds = diff.seconds
    if days < 0:
        return dt.strftime("%d %b %Y")
    if days == 0:
        hours = seconds // 3600
        if hours < 1:
            minutes = max(1, seconds // 60)
            return f"{minutes}m lalu"
        return f"{hours}j lalu"
    elif days == 1:
        return "Kemarin"
    elif days < 7:
        return f"{days} hr lalu"
    elif days < 30:
        weeks = max(1, days // 7)
        return f"{weeks} mgg lalu"
    elif days < 365:
        months = max(1, days // 30)
        return f"{months} bln lalu"
    else:
        return dt.strftime("%d %b %Y")

def get_recent_jobs(role=None, limit=300):
    """Mengambil daftar lowongan kerja individual untuk tabel Job Explorer lengkap dengan skills, education, experience, dll."""
    con = get_db_connection()
    try:
        query = """
            SELECT 
                job_title,
                company_name,
                standard_role,
                location_city,
                work_arrangement,
                employment_type,
                education_level,
                min_experience,
                salary_min,
                salary_max,
                source_platform,
                company_url,
                posted_at,
                skills,
                job_url
            FROM init_all_jobs
        """
        params = []
        if role and role != "All":
            query += " WHERE standard_role = ?"
            params.append(role)

        query += " ORDER BY posted_at DESC LIMIT ?"
        params.append(limit)

        rows = con.execute(query, params).fetchall()
        jobs = []
        for r in rows:
            posted_at = r[12]
            skills_raw = r[13]
            skills = [s.strip() for s in skills_raw if s and s.strip()] if skills_raw else []

            salary_min = r[8]
            salary_max = r[9]
            if salary_min and salary_max:
                salary_sort_val = (salary_min + salary_max) / 2
            elif salary_min:
                salary_sort_val = salary_min
            else:
                salary_sort_val = 0

            posted_at_iso = posted_at.isoformat() if posted_at else ""
            posted_at_date = posted_at.strftime("%d %b %Y") if posted_at else "Not Specified"
            posted_at_time = posted_at.strftime("%H:%M WIB") if posted_at else ""
            posted_at_formatted = f"{posted_at_date}, {posted_at_time}".strip(", ")
            posted_at_relative = format_relative_date(posted_at) if posted_at else "Not Specified"

            work_arrangement = r[4] or "Onsite"
            employment_type = r[5] or "Full-time"
            education_level = r[6] or "Not Specified"
            min_exp_raw = r[7]
            exp_info = categorize_experience(min_exp_raw)

            jobs.append({
                "job_title": r[0] or "Untitled",
                "company_name": r[1] or "Perusahaan Rahasia / Not Specified",
                "standard_role": r[2] or "Other",
                "location_city": r[3] or "Indonesia / Remote",
                "work_arrangement": work_arrangement,
                "employment_type": employment_type,
                "work_type": work_arrangement,  # Backward compatibility
                "education_level": education_level,
                "min_experience": min_exp_raw,
                "experience_tier": exp_info["tier"],
                "experience_display": exp_info["display"],
                "experience_badge_class": exp_info["badge_class"],
                "salary_min": salary_min,
                "salary_max": salary_max,
                "source_platform": r[10] or "Unknown",
                "company_url": r[11],
                "job_url": r[14],
                "posted_at": posted_at,
                "posted_at_iso": posted_at_iso,
                "posted_at_date": posted_at_date,
                "posted_at_time": posted_at_time,
                "posted_at_formatted": posted_at_formatted,
                "posted_at_relative": posted_at_relative,
                "skills": skills,
                "salary_sort_val": salary_sort_val
            })
        return jobs
    finally:
        con.close()

