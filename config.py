import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))

load_dotenv()

class Config:
    SECRET_KEY = os.environ["SECRET_KEY"]

    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = (
        os.environ.get("SQLALCHEMY_TRACK_MODIFICATIONS", "false").lower() == "true"
    )

    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER")

    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"

    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

    MAIL_DEFAULT_SENDER = (
        os.environ.get("MAIL_DEFAULT_NAME"),
        os.environ.get("MAIL_DEFAULT_EMAIL")
    )

    MAIL_MAX_EMAILS = int(os.environ.get("MAIL_MAX_EMAILS", 3))
    
    MAX_CONTENT_LENGTH = 64 * 1024 * 1024 
