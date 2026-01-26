from werkzeug.security import check_password_hash
from flask_login import current_user
from wtforms.validators import ValidationError
from app.models import User, File, Person

class CurrentPassword:
    def __init__(self, message=None):
        self.message = message or "Nieprawidłowe aktualne hasło"
        
    def __call__(self, form, field):
        if not check_password_hash(current_user.password_hash, field.data):
            raise ValidationError(self.message)
        
class EmailNotRegistered:
    def __init__(self, message=None):
        self.message = message or "Konto o podanym adresie email już istnieje"
        
    def __call__(self, form, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(self.message)
        
class EmailRegistered:
    def __init__(self, message=None):
        self.message = message or "Konto o podanym adresie email nie istnieje"
        
    def __call__(self, form, field):
        if not User.query.filter_by(email=field.data).first():
            raise ValidationError(self.message)
        
class FitsQuota:
    def __init__(self, message=None):
        self.message = message or "Za mało miejsca na koncie"
        
    def __call__(self, form, field):
        field.data.stream.seek(0, 2)
        size = field.data.stream.tell()
        field.data.stream.seek(0)
        if size > current_user.quota * 1024 * 1024 - current_user.space_used:
            raise ValidationError(self.message)
        
class FileNameNotInUse:
    def __init__(self, message=None):
        self.message = message or "Masz już plik o tej nazwie"
        
    def __call__(self, form, field):
        if File.query.filter_by(name=field.data, user_id=current_user.id).first():
            raise ValidationError(self.message)
        
class PersonExists:
    def __init__(self, message=None):
        self.message = message or "Nie znaleziono w systemie szkolnym konta o podanym loginie!"
        
        
    def __call__(self, form, field):
        if not Person.query.filter_by(login=field.data).first():
            raise ValidationError(self.message)
        
class PersonNotRegistered:
    def __init__(self, message=None):
        self.message = message or "Z tym kontem szkolnym jest już powiązane konto!"
        
        
    def __call__(self, form, field):
        person = Person.query.filter_by(login=field.data).first()
        if person:
            if User.query.filter_by(person_id=person.id).first():
                raise ValidationError(self.message)