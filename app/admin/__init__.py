from flask_admin.contrib.sqla import ModelView
from app.extensions import db, admin
from app.models import User, Person, Post, Tag, File, UserRole
from flask import redirect, url_for
from flask_login import current_user
from wtforms import PasswordField
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

class AdminModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and (current_user.role == UserRole.superadmin or current_user.role == UserRole.admin)

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("panel.panel_home"))
    
    # column_display_pk = True
    
class AdminOnlyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.admin

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("panel.panel_home"))
    
    # column_display_pk = True
    
class SuperAdminModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.superadmin

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("panel.panel_home"))
    
    # column_display_pk = True


class UserModelView(SuperAdminModelView):
    column_exclude_list = ["password_hash"]
    column_searchable_list = ["first_name", "last_name", "email", "ldap_group"]
    column_filters = ["ldap_group", "role"]
    
    column_formatters = {
        "space_used": lambda v, c, m, p: f"{round(m.space_used / (1024*1024), 2)} MB"
    }
    create_modal = True
    edit_modal = True
    
    # form_choices = {
    # "role": [
    #     ("user", "user"),
    #     (UserRole.admin, UserRole.admin),
    #     (UserRole.superadmin, UserRole.superadmin),
    # ]
    # }
    
    form_extra_fields = {
        "password": PasswordField("New Password")
    }
    def on_model_change(self, form, model, is_created):
        if hasattr(form, "password") and form.password.data:
            model.password_hash = generate_password_hash(form.password.data)
    
    can_export = True
    export_types = ["csv", "xlsx", "json"]
    
    column_editable_list = ["reputation"]
    form_excluded_columns = ["password_hash"]
    
    column_labels = {"ldap_group" : "Group", "first_name" : "First Name", "last_name" : "Last Name", "email" : "Email"}
    
class BasicUserModelView(AdminOnlyModelView):
    column_exclude_list = ["password_hash"]
    column_searchable_list = ["first_name", "last_name", "email", "ldap_group"]
    column_filters = ["ldap_group", "role"]
    
    create_modal = True
    edit_modal = True
    
    # form_choices = {
    # "role": [
    #     ("user", "user"),
    #     (UserRole.admin, UserRole.admin),
    #     (UserRole.superadmin, UserRole.superadmin),
    # ]
    # }
    
    form_extra_fields = {
        "password": PasswordField("New Password")
    }
    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.password_hash = generate_password_hash(form.password.data)
            
    can_delete = False
    can_create = False
    column_editable_list = ["reputation"]
    form_columns = ["reputation", "quota"]
    
    column_labels = {"ldap_group" : "Group", "first_name" : "First Name", "last_name" : "Last Name", "email" : "Email"}
    

from flask_admin.contrib.fileadmin import FileAdmin
from os import path

class StaticFilesView(FileAdmin):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.superadmin

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("auth.signin"))

class PersonModelView(SuperAdminModelView):
    column_searchable_list = ["first_name", "last_name", "login", "ldap_group"]
    column_filters = ["ldap_group"]
    
    create_modal = True
    edit_modal = True
    
    page_size = 50
    
    can_export = True
    export_types = ["csv", "xlsx", "json"]
    
    column_labels = {"ldap_group" : "Group", "first_name" : "First Name", "last_name" : "Last Name", "login" : "Login"}
    
class PostModelView(AdminModelView):
    column_searchable_list = ["title", "content", "author.first_name", "author.last_name"]
    column_filters = ["author", "status"]
    
    create_modal = True
    edit_modal = True
    
    # form_choices = {
    # "status": [
    #     ("visible", "visible"),
    #     ("pending", "pending"),
    #     ("hidden", "hidden"),
    # ]
    # }

    @property
    def can_export(self):
        return current_user.role == UserRole.superadmin
    export_types = ["csv", "xlsx", "json"]
    
    column_formatters = {
        "created_at": lambda v, c, m, p: m.created_at.strftime("%Y-%m-%d %H:%M")
    }
    
    column_editable_list = ["status"]
    column_labels = {"title" : "Title", "content" : "Content", "author.first_name" : "Author's First Name", "author.last_name" : "Author's Last Name"}
    
class PendingPostModelView(PostModelView):
    def get_query(self):
        return super().get_query().filter(self.model.status == "pending").order_by(self.model.created_at.asc())

    def get_count_query(self):
        return super().get_count_query().filter(self.model.status == "pending")
    
class RecentPostModelView(PostModelView):
    def get_query(self):
        return super().get_query().filter(self.model.status == "visible").order_by(self.model.created_at.desc())

    def get_count_query(self):
        return super().get_count_query().filter(self.model.status == "visible")
    
class TagModelView(AdminModelView):
    create_modal = True
    edit_modal = True

    @property
    def can_export(self):
        return current_user.role == UserRole.superadmin
    export_types = ["csv", "xlsx", "json"]
    
    column_labels = {"title" : "Title", "content" : "Content", "author.first_name" : "Author's First Name", "author.last_name" : "Author's Last Name"}

from markupsafe import Markup

class FileModelView(AdminModelView):
    create_modal = True
    edit_modal = True
    
    @property
    def can_export(self):
        return current_user.role == UserRole.superadmin
    export_types = ["csv", "xlsx", "json"]
    
    column_formatters = {
        "created_at": lambda v, c, m, p: m.created_at.strftime("%Y-%m-%d %H:%M"),
        "filename": lambda v, c, m, p: Markup(
            f"""<a href="{url_for("main.userfile", filename=m.filename)}" target="_blank">{m.filename}</a>"""
        )
    }
    
    column_editable_list = ["status"]
    
class PendingFileModelView(FileModelView):
    def get_query(self):
        return super().get_query().filter(self.model.status == "pending").order_by(self.model.created_at.asc())

    def get_count_query(self):
        return super().get_count_query().filter(self.model.status == "pending")
    
class RecentFileModelView(FileModelView):
    def get_query(self):
        return super().get_query().filter(self.model.status == "visible").order_by(self.model.created_at.desc())

    def get_count_query(self):
        return super().get_count_query().filter(self.model.status == "visible")
    
class UserFilesView(FileAdmin):
    def is_accessible(self):
        return current_user.is_authenticated and (current_user.role == UserRole.superadmin or current_user.role == UserRole.admin)

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("auth.signin"))


import os.path as op
from flask_admin.base import MenuLink
def init_admin():
    admin.add_view(UserModelView(User, db.session, name="Users"))
    admin.add_view(BasicUserModelView(User, db.session, name="Users", endpoint="basic_users"))
    admin.add_view(PersonModelView(Person, db.session, name="People"))
    admin.add_view(PostModelView(Post, db.session, name="All", category="Posts"))
    admin.add_view(PendingPostModelView(Post, db.session, name="Pending", endpoint="pending_posts", category="Posts"))
    admin.add_view(RecentPostModelView(Post, db.session, name="Recent", endpoint="recent_posts", category="Posts"))
    admin.add_view(TagModelView(Tag, db.session, name="Tags"))
    admin.add_view(FileModelView(File, db.session, name="All", category="Files"))
    admin.add_view(PendingFileModelView(File, db.session, name="Pending", endpoint="pending_files", category="Files"))
    admin.add_view(RecentFileModelView(File, db.session, name="Recent", endpoint="recent_files", category="Files"))
    admin.add_view(UserFilesView(op.join(op.dirname(__file__), "..", "uploads"), "/uploads/", name="Uploads"))
    admin.add_view(StaticFilesView(op.join(op.dirname(__file__), "..", "static"), "/static/", name="Static Files"))
    
    admin.add_link(MenuLink(name="Logout", url="/auth/logout"))
    admin.add_link(MenuLink(name="Site", url="/", category="Go to"))
    admin.add_link(MenuLink(name="User Panel", url="/panel", category="Go to"))