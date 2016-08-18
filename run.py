import click
from website import app, db

@app.cli.command()
def initdb():
    db.create_all()
    click.echo('Made a database.')

if __name__ == '__main__':
    app.run(debug=True)
