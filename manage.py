import os
from flask.cli import FlaskGroup
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import Person, User, UserRole

def create_app_cli():
    return create_app()

cli = FlaskGroup(create_app=create_app_cli)

@cli.command("add-superadmin-user")
def add_superadmin_user():
    email = "admin@example.com"
    password = "admin"

    admin_user = User(
        email=email,
        password_hash=generate_password_hash(password),
        role=UserRole.superadmin,
        person=None,
        quota=1024,
        reputation=100,
        first_name="Admin",
        last_name="Admin",
        ldap_group="itos",
        email_confirmed=True,
        force_password_change=True
    )

    db.session.add(admin_user)
    db.session.commit()

    print("Superadmin user created")

@cli.command("import-people")
def import_people():
    count_imported = 0
    count_skipped = 0

    with open("people-to-import.csv", "r") as file:
        for line in file:
            data = line.strip().split(";")

            if Person.query.filter_by(login=data[0]).first():
                count_skipped += 1
                continue

            newperson = Person(
                login=data[0],
                first_name=data[1],
                last_name=data[2],
                ldap_group=data[3]
            )

            db.session.add(newperson)
            count_imported += 1

    db.session.commit()
    print(f"{count_imported} people imported, {count_skipped} skipped")

if __name__ == "__main__":
    cli()
