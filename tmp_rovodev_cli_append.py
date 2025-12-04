
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
