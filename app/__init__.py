from flask import Flask, request, render_template

from config import Config

from app.extensions import db, migrate, login_manager, mail, admin

from app.models import Person, User, Post, Tag, post_tags, UserRole, PostStatus, FileStatus
    
def create_app(config_class = Config):
    app = Flask(__name__)
    
    app.config.from_object(config_class)
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    admin.init_app(app)
    
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
    
    return app