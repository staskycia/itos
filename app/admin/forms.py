from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, EmailField, TextAreaField
from wtforms.validators import DataRequired, Email

class SendMailForm(FlaskForm):
    recipient = EmailField(validators=[DataRequired(message="Pole wymagane"), Email(message="Wprowadź prawidłowy adres email")])
    title = StringField(validators=[DataRequired(message="Pole wymagane")])
    content = TextAreaField(validators=[DataRequired(message="Pole wymagane")])
    
    submit = SubmitField("Wyślij")