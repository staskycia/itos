from flask import render_template
from flask_mail import Message
from app.extensions import mail

def send_message(subject, body, recipients):
    msg = Message(subject=subject, body=body, html=render_template("mail/message.html", subject=subject, body=body), bcc=recipients)
    mail.send(msg)
    
def send_button_message(subject, body, recipients, button_text, button_target):
    msg = Message(subject=subject, body=f"{body}\nPrzycisk nie działa? Otwórz w przeglądarce następujący adres: {button_target}", html=render_template("mail/button_message.html", subject=subject, body=body, button_text=button_text, button_target=button_target), bcc=recipients)
    mail.send(msg)