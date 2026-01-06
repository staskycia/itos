from app.extensions import db

class Person(db.Model):
    __tablename__ = "persons"
    
    id = db.Column(db.Integer, primary_key=True)
    
    login = db.Column(db.String(50), nullable=False)
    
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    
    ldap_group = db.Column(db.String(10), nullable=False)
    
    user = db.relationship("User", back_populates="person", uselist=False)
    
    def __repr__(self):
        return f"{self.first_name} {self.last_name} ({self.login})"