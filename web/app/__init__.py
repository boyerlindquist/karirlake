import os
from flask import Flask

def create_app():
    """Application Factory for TalentLake Web Application."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    # Configuration
    from datetime import timedelta
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "talentlake-secret-key-2026")
    app.config["SESSION_COOKIE_NAME"] = "talentlake_session"
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_REFRESH_EACH_REQUEST"] = True

    # Initialize Application SQLite DB
    from web.app.app_db import init_app_db
    init_app_db()

    # Register Blueprints
    from web.app.routes.views import views_bp
    from web.app.routes.api import api_bp
    from web.app.routes.auth import auth_bp

    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # Inject authentication status to all Jinja templates
    @app.context_processor
    def inject_user():
        from flask import session
        from web.app.app_db import get_user_by_id
        user = None
        if "user_id" in session:
            user = get_user_by_id(session["user_id"])
        return dict(current_user=user)

    return app
