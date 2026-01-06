from app.extensions import db

post_files = db.Table(
    "post_files",
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True),
    db.Column("file_id", db.Integer, db.ForeignKey("files.id", ondelete="CASCADE"), primary_key=True),
)