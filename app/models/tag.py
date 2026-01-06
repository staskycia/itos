from app.extensions import db
from flask_login import UserMixin
from sqlalchemy import Enum
from enum import Enum as PyEnum
from app.models.tag_assigners import tag_assigners

from app.models.post_tags import post_tags

class TagColor(PyEnum):
    red = "red"
    orange = "orange"
    amber = "amber"
    yellow = "yellow"
    lime = "lime"
    green = "green"
    emerald = "emerald"
    teal = "teal"
    cyan = "cyan"
    sky = "sky"
    blue = "blue"
    indigo = "indigo"
    violet = "violet"
    purple = "purple"
    fuchsia = "fuchsia"
    pink = "pink"
    rose = "rose"

class Tag(db.Model):
    __tablename__ = "tags"
    
    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(db.String(120), unique=False, nullable=False)
    color = db.Column(Enum(TagColor, name="tag_color", native_enum=True, validate_strings=True), nullable=False, default=TagColor.blue, index=True)
    
    posts = db.relationship("Post", secondary=post_tags, back_populates="tags", lazy="select")

    is_restricted = db.Column(db.Boolean, default=False, nullable=False)
    allowed_users = db.relationship("User", secondary=tag_assigners, back_populates="assignable_tags")
    
    def __repr__(self):
        return self.name