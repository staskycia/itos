import logging
from logging.handlers import RotatingFileHandler

import re

ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')

class StripANSIFormatter(logging.Formatter):
    def format(self, record):
        original = super().format(record)
        return ANSI_ESCAPE.sub('', original)

class FilterStaticRequests(logging.Filter):
    def filter(self, record):
        return "/static/" not in record.getMessage()
    
def init_logging(app):
    formater = StripANSIFormatter("[%(asctime)s] %(levelname)s in %(name)s: %(message)s")
    
    file_handler = RotatingFileHandler("itos.log", maxBytes=50_000_000, backupCount=5)
    
    file_handler.setFormatter(formater)
    file_handler.setLevel(logging.INFO)
    
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.propagate = False
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

    file_handler.addFilter(FilterStaticRequests())

    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.setLevel(logging.INFO)

    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.orm").setLevel(logging.WARNING)

    logging.getLogger("smtplib").setLevel(logging.WARNING)
    logging.getLogger("mail").setLevel(logging.INFO)

    logging.getLogger("flask_admin").setLevel(logging.INFO)

import logging
from flask import request, current_app
from flask_login import current_user
from datetime import datetime

def log_action(msg, status=200):
    ip = request.remote_addr or "-"
    user_id = getattr(current_user, "id", "ANONYMOUS")

    timestamp = datetime.utcnow().strftime("%d/%b/%Y %H:%M:%S")

    message = (
    f'{ip} - user={user_id} '
    f'[{timestamp}] "{msg}"'
    )

    current_app.logger.info(message)