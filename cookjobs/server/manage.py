#!/usr/bin/env python

import os
import click
import app_cfg
from werkzeug.serving import run_simple

from app import  api, Base


@click.group()
def cli():
    pass


@cli.command()
def runserver():
    run_simple("0.0.0.0", app_cfg.OPEN_PORT, api, use_debugger=True, use_reloader=True)


@cli.command()
def initdb():
    if os.path.isfile("data.sqlite"):
        click.echo(
            "You have database file in the current directory"
            "to createad it run dropdb, initdb commands respectively."
        )
    else:
        click.echo("initializing database...")
        from sqlalchemy import create_engine
        engine = create_engine(app_cfg.DB_CONFIG)
        Base.metadata.create_all(engine)


@cli.command()
def dropdb():
    filename = "data.sqlite"
    if os.path.isfile(filename):
        os.remove(filename)
        click.echo("dropping database...")
    else:
        click.echo("The database doesn't exists")


if __name__ == "__main__":
    cli()