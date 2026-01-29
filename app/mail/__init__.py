from flask import render_template, current_app
from flask_mail import Message

from app.extensions import mail


def send_message(subject, body, recipients, sender_name=None, replay_to=None):
    default_sender_name, default_email = current_app.config["MAIL_DEFAULT_SENDER"]
    if not sender_name:
        sender_name = default_sender_name
    
    if not replay_to:
        replay_to = default_email
    
    msg = Message(
        subject=subject,
        body=body,
        html=render_template("mail/message.html", subject=subject, body=body),
        bcc=recipients,
        reply_to=replay_to,
        sender=(sender_name, default_email)
    )
    mail.send(msg)

def send_button_message(subject, body, recipients, button_text, button_target):
    msg = Message(
        subject=subject,
        body=f"{body}\nPrzycisk nie działa? Otwórz w przeglądarce następujący adres: {button_target}",
        html=render_template(
            "mail/button_message.html",
            subject=subject,
            body=body,
            button_text=button_text,
            button_target=button_target,
        ),
        bcc=recipients,
    )
    mail.send(msg)
