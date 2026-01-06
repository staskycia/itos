from app.extensions import db

tag_assigners = db.Table(
    "tag_assigners",
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)