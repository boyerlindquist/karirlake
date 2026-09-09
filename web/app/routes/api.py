from flask import Blueprint, jsonify, request, session
from web.app.database import (
    get_overview_kpis,
    get_available_roles,
    get_role_insights,
)
from web.app.app_db import (
    save_job,
    update_saved_job_status,
    update_saved_job_test_type,
    update_saved_job_notes,
    delete_saved_job,
    get_funnel_stats
)

api_bp = Blueprint("api", __name__)

@api_bp.route("/overview")
def api_overview():
    """Returns global market metrics (KPIs)."""
    try:
        data = get_overview_kpis()
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route("/roles")
def api_roles():
    """Returns available standardized job categories."""
    try:
        roles = get_available_roles()
        return jsonify({"status": "success", "roles": roles})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route("/role-insights/<role>")
def api_role_insights(role):
    """Returns aggregated data marts for a specific role."""
    try:
        insights = get_role_insights(role)
        return jsonify({
            "status": "success",
            "role": role,
            "data": insights
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- APPLICATION TRACKER & SAVED JOBS API ---

@api_bp.route("/jobs/save", methods=["POST"])
def api_save_job():
    """Menyimpan lowongan ke tabel saved_jobs milik user aktif."""
    if "user_id" not in session:
        return jsonify({
            "status": "error",
            "code": "unauthorized",
            "message": "Silakan masuk (login) terlebih dahulu untuk menyimpan lowongan."
        }), 401

    try:
        data = request.get_json() or {}
        res = save_job(session["user_id"], data)
        if res["success"]:
            return jsonify({"status": "success", "id": res["id"]})
        else:
            return jsonify({"status": "error", "message": res["error"]}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route("/saved-jobs/update-status", methods=["POST"])
def api_update_status():
    """Memperbarui tahapan status lamaran (Saved, Applied, Interview, Test, dll)."""
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    try:
        data = request.get_json() or {}
        job_id = data.get("job_id")
        new_status = data.get("status")
        
        if not job_id or not new_status:
            return jsonify({"status": "error", "message": "Missing job_id or status"}), 400

        try:
            job_id = int(job_id)
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "Invalid job_id"}), 400

        res = update_saved_job_status(session["user_id"], job_id, new_status)
        if res["success"]:
            stats = get_funnel_stats(session["user_id"])
            return jsonify({
                "status": "success", 
                "stats": stats,
                "sankey_data": stats.get("sankey_data", [])
            })
        else:
            return jsonify({"status": "error", "message": res.get("error", "Gagal memperbarui status")}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route("/saved-jobs/update-test-type", methods=["POST"])
def api_update_test_type():
    """Memperbarui keterangan jenis tes teknis (Take-home, Live coding, OA, dll)."""
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    try:
        data = request.get_json() or {}
        job_id = data.get("job_id")
        test_type = data.get("test_type")

        if not job_id or not test_type:
            return jsonify({"status": "error", "message": "Missing job_id or test_type"}), 400

        try:
            job_id = int(job_id)
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "Invalid job_id"}), 400

        res = update_saved_job_test_type(session["user_id"], job_id, test_type)
        if res["success"]:
            stats = get_funnel_stats(session["user_id"])
            return jsonify({"status": "success", "stats": stats})
        else:
            return jsonify({"status": "error", "message": res.get("error", "Gagal memperbarui tipe tes")}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route("/saved-jobs/update-notes", methods=["POST"])
def api_update_notes():
    """Menyimpan catatan persiapan/interview pada lowongan tertentu."""
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    try:
        data = request.get_json() or {}
        job_id = data.get("job_id")
        notes = data.get("notes", "")

        if not job_id:
            return jsonify({"status": "error", "message": "Missing job_id"}), 400

        try:
            job_id = int(job_id)
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "Invalid job_id"}), 400

        res = update_saved_job_notes(session["user_id"], job_id, notes)
        return jsonify({"status": "success" if res["success"] else "error"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route("/saved-jobs/<int:job_id>", methods=["DELETE"])
def api_delete_saved_job(job_id):
    """Menghapus lowongan dari tracker."""
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    try:
        res = delete_saved_job(session["user_id"], job_id)
        if res["success"]:
            stats = get_funnel_stats(session["user_id"])
            return jsonify({
                "status": "success", 
                "stats": stats,
                "sankey_data": stats.get("sankey_data", [])
            })
        else:
            return jsonify({"status": "error", "message": "Data tidak ditemukan"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route("/saved-jobs/stats")
def api_saved_jobs_stats():
    """Mengambil stats scorecards dan sankey data secara live."""
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    try:
        stats = get_funnel_stats(session["user_id"])
        return jsonify({"status": "success", "data": stats})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
