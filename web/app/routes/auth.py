from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from web.app.app_db import verify_user, create_user, get_user_by_id

auth_bp = Blueprint("auth", __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("views.saved_jobs"))

    error = None
    next_url = request.args.get("next") or url_for("views.saved_jobs")

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            error = "Silakan isi email dan kata sandi Anda."
        else:
            user = verify_user(email, password)
            if user:
                session.permanent = True
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["email"] = user["email"]
                return redirect(next_url)
            else:
                error = "Email atau kata sandi salah. Silakan coba lagi."

    return render_template("login.html", error=error, next_url=next_url)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("views.saved_jobs"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not email or not password:
            error = "Semua field wajib diisi."
        elif len(password) < 6:
            error = "Kata sandi minimal harus 6 karakter."
        elif password != confirm_password:
            error = "Konfirmasi kata sandi tidak cocok."
        else:
            res = create_user(username, email, password)
            if res["success"]:
                session.permanent = True
                session["user_id"] = res["user_id"]
                session["username"] = username
                session["email"] = email
                return redirect(url_for("views.saved_jobs"))
            else:
                error = res["error"]

    return render_template("register.html", error=error)

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("views.index"))
