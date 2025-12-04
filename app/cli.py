from app import app, db
from app.models import Questions, User
import click

@app.cli.command("initdb")
def initdb():
    """Create database tables based on current models (useful for quick start)."""
    db.create_all()
    print("Database tables created (if not existing).")

@app.cli.command("seed")
def seed():
    """Seed the database with a few example questions."""
    sample = [
        {
            "q_id": 1,
            "ques": "What is the capital of France?",
            "a": "Berlin",
            "b": "Madrid",
            "c": "Paris",
            "d": "Rome",
            "ans": "Paris",
            "time_limit": 60,
        },
        {
            "q_id": 2,
            "ques": "Which planet is known as the Red Planet?",
            "a": "Earth",
            "b": "Mars",
            "c": "Jupiter",
            "d": "Saturn",
            "ans": "Mars",
            "time_limit": 60,
        },
        {
            "q_id": 3,
            "ques": "What is 2 + 2?",
            "a": "3",
            "b": "4",
            "c": "5",
            "d": "22",
            "ans": "4",
            "time_limit": 60,
        },
    ]
    inserted = 0
    for s in sample:
        if not Questions.query.filter_by(q_id=s["q_id"]).first():
            q = Questions(**s)
            db.session.add(q)
            inserted += 1
    db.session.commit()
    print(f"Seed complete. Inserted {inserted} new questions.")


@app.cli.command("create-admin")
@click.argument("username")
@click.argument("email")
@click.password_option(help="Admin password")
def create_admin(username, email, password):
    """Create an admin user with the given credentials."""
    if User.query.filter((User.username==username)|(User.email==email)).first():
        click.echo("User with that username or email already exists.")
        return
    u = User(username=username, email=email, is_admin=True)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    click.echo(f"Admin created: {username} <{email}>")
