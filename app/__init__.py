from flask import Flask, flash, render_template, request
from flask_login import current_user

from app.extensions import admin, cache, db, login_manager, mail, migrate, csrf
from app.models import (
    FileStatus,
    Person,
    Post,
    PostStatus,
    Setting,
    Tag,
    User,
    UserRole,
    post_tags,
)
from config import Config


def create_app(config_class=Config):
    app = Flask(__name__)

    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    admin.init_app(app)
    cache.init_app(app)
    csrf.init_app(app)

    from app.admin import init_admin

    with app.app_context():
        init_admin()

    @app.errorhandler(404)
    def error404(e):
        return render_template("404.html")

    @app.context_processor
    def inject_enums():
        return dict(UserRole=UserRole, FileStatus=FileStatus, PostStatus=PostStatus)

    from app.main import bp as main_bp

    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")

    from app.panel import bp as panel_bp

    app.register_blueprint(panel_bp, url_prefix="/panel")

    @app.before_request
    def maintenance_mode():
        if not Setting.get("maintenance_mode"):
            return
        if request.endpoint == "static":
            return
        if current_user.is_authenticated and current_user.role == UserRole.superadmin:
            return
        if request.endpoint == "auth.signin":
            return
        return render_template("maintenance.html"), 503

    return app
