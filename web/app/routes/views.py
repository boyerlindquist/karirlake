from flask import Blueprint, render_template, request, session
from web.app.routes.auth import login_required
from web.app.app_db import (
    get_saved_jobs,
    get_user_saved_keys,
    get_funnel_stats,
    VALID_STAGES,
    STAGES_ACTIVE,
    STAGES_SUCCESS,
    STAGES_GHOSTED,
    STAGES_REJECTED,
    VALID_TEST_TYPES
)
from web.app.database import (
    get_overview_kpis,
    get_available_roles,
    get_role_insights,
    get_recent_jobs,
)

views_bp = Blueprint("views", __name__)

@views_bp.route("/")
def index():
    """Main Analytics Dashboard Route."""
    kpis = get_overview_kpis()
    roles = get_available_roles()
    default_role = "Data Engineer" if "Data Engineer" in roles else (roles[0] if roles else "Data Engineer")
    initial_insights = get_role_insights(default_role)

    return render_template(
        "index.html",
        kpis=kpis,
        roles=roles,
        current_role=default_role,
        initial_insights=initial_insights,
        active_page="dashboard"
    )

@views_bp.route("/jobs")
def jobs():
    """Live Job Explorer Table Route with Fuzzy Search and Multi-field matching."""
    roles = get_available_roles()
    selected_role = request.args.get("role", "All")
    selected_platform = request.args.get("platform", "All")
    selected_work_arrangement = request.args.get("work_arrangement", "All")
    selected_employment_type = request.args.get("employment_type", "All")
    selected_exp_tier = request.args.get("exp_tier", "All")
    search_query = request.args.get("q", "").strip()

    all_jobs = get_recent_jobs(role=selected_role if selected_role != "All" else None, limit=300)

    # Filter platform, work_arrangement, employment_type, exp_tier
    filtered_jobs = []
    for job in all_jobs:
        if selected_platform != "All" and job["source_platform"] != selected_platform:
            continue
        if selected_work_arrangement != "All" and job.get("work_arrangement") != selected_work_arrangement:
            continue
        if selected_employment_type != "All" and job.get("employment_type") != selected_employment_type:
            continue
        if selected_exp_tier != "All" and job.get("experience_tier") != selected_exp_tier:
            continue
        filtered_jobs.append(job)

    # Fuzzy Search filter
    if search_query:
        from rapidfuzz import fuzz
        q = search_query.lower()
        scored_jobs = []

        for job in filtered_jobs:
            title = (job["job_title"] or "").lower()
            company = (job["company_name"] or "").lower()
            city = (job["location_city"] or "").lower()
            role = (job["standard_role"] or "").lower()
            skills = [s.lower() for s in job["skills"]]

            # 1. Direct exact matches get top priority scores
            if q in title:
                score = 100.0
            elif any(q == s or q in s for s in skills):
                score = 98.0
            elif q in role:
                score = 95.0
            elif q in company:
                score = 92.0
            elif q in city:
                score = 90.0
            else:
                # 2. Field-level fuzzy matching across title, role, company, city, skills
                title_score = max(fuzz.partial_ratio(q, title), fuzz.token_set_ratio(q, title))
                role_score = max(fuzz.partial_ratio(q, role), fuzz.token_set_ratio(q, role))
                comp_score = fuzz.ratio(q, company) if len(q) < 6 else fuzz.partial_ratio(q, company)
                city_score = fuzz.ratio(q, city) if len(q) < 6 else fuzz.partial_ratio(q, city)
                skill_score = max([fuzz.ratio(q, s) for s in skills]) if skills else 0

                score = max(title_score, role_score, comp_score, city_score, skill_score)

            # Strict threshold to avoid false positives while allowing typos & close keywords
            min_threshold = 70.0 if len(q) >= 4 else 80.0
            if score >= min_threshold:
                job["match_score"] = round(score, 1)
                scored_jobs.append((score, job))

        # Sort by relevance match score descending
        scored_jobs.sort(key=lambda x: x[0], reverse=True)
        filtered_jobs = [item[1] for item in scored_jobs]

    # Check which jobs are saved by current user
    saved_keys = set()
    if "user_id" in session:
        saved_keys = get_user_saved_keys(session["user_id"])

    for job in filtered_jobs:
        key = f"{job['job_title']}||{job['company_name']}"
        job["is_saved"] = key in saved_keys

    return render_template(
        "jobs.html",
        roles=roles,
        selected_role=selected_role,
        selected_platform=selected_platform,
        selected_work_arrangement=selected_work_arrangement,
        selected_employment_type=selected_employment_type,
        selected_exp_tier=selected_exp_tier,
        search_query=search_query,
        jobs=filtered_jobs,
        total_found=len(filtered_jobs),
        active_page="jobs"
    )

@views_bp.route("/saved-jobs")
@login_required
def saved_jobs():
    """Halaman Saved Jobs: Tracking progres lamaran, scorecards, dan Sankey Chart."""
    status_filter = request.args.get("status", "All")
    user_id = session["user_id"]
    
    # Fetch all saved jobs to allow instant client-side smooth filtering
    jobs = get_saved_jobs(user_id, status_filter=None)
    funnel_data = get_funnel_stats(user_id)
    
    return render_template(
        "saved_jobs.html",
        jobs=jobs,
        stats=funnel_data["scorecards"],
        sankey_data=funnel_data["sankey_data"],
        status_counts=funnel_data["counts"],
        stages=VALID_STAGES,
        stages_active=STAGES_ACTIVE,
        stages_success=STAGES_SUCCESS,
        stages_ghosted=STAGES_GHOSTED,
        stages_rejected=STAGES_REJECTED,
        test_types=VALID_TEST_TYPES,
        selected_status=status_filter,
        active_page="saved_jobs"
    )



