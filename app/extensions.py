from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

from flask_migrate import Migrate
migrate = Migrate()

from flask_login import LoginManager, current_user
from app.models import User, File, Post, Tag, Person, UserRole

login_manager = LoginManager()
login_manager.login_view = "auth.signin"
login_manager.login_message = "Zaloguj się, aby wyświtlić stronę!"
login_manager.login_message_category = "error"

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

from flask_mail import Mail
mail = Mail()

from flask_admin import Admin, AdminIndexView
from flask_admin.theme import Bootstrap4Theme
from flask import redirect, url_for

class ItosIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and (current_user.role == UserRole.superadmin or current_user.role == UserRole.admin)
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("auth.signin"))
    
admin = Admin(name="ITOS Admin", theme=Bootstrap4Theme(swatch="slate"), index_view=ItosIndexView(name="Home"))