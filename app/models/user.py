from app.extensions import db
from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func, select, Enum
from enum import Enum as PyEnum
from app.models.tag_assigners import tag_assigners

class UserRole(PyEnum):
    user = "user"
    admin = "admin"
    superadmin = "superadmin"

class User(UserMixin, db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=True, unique=True)
    
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    email_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    
    ldap_group = db.Column(db.String(10), nullable=False)
    
    
    role = db.Column(Enum(UserRole, name="user_role", native_enum=True, validate_strings=True), nullable=False, default=UserRole.user, index=True)
    
    quota = db.Column(db.Integer, nullable=False, default = 64)
    
    @hybrid_property
    def space_used(self):
        return sum(f.size for f in self.files)

    @space_used.expression
    def space_used(cls):
        from app.models.file import File
        return select(
            func.coalesce(func.sum(File.size), 0)
        ).where(File.user_id == cls.id).scalar_subquery()
    
    reputation = db.Column(db.Integer, nullable=False, default=70)
    
    password_hash = db.Column(db.String(255), nullable=False)
    
    person = db.relationship("Person", back_populates="user")
    
    posts = db.relationship("Post", back_populates="author", cascade="all, delete-orphan", lazy="dynamic", order_by="Post.created_at.desc()")
    files = db.relationship("File", back_populates="author", cascade="all, delete-orphan", lazy="dynamic", order_by="File.created_at.desc()")

    force_password_change = db.Column(db.Boolean, nullable=False, default=False)
    
    assignable_tags = db.relationship("Tag", secondary=tag_assigners, back_populates="allowed_users")
    
    def __repr__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"