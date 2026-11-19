import sqlite3
from contextlib import contextmanager

import click
from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
            timeout=10,
            isolation_level=None,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.execute("PRAGMA busy_timeout = 5000")
    return g.db


def close_db(_error=None):
    database = g.pop("db", None)
    if database is not None:
        database.close()


def init_db():
    database = get_db()
    database.execute("PRAGMA journal_mode = WAL")
    with current_app.open_resource("schema.sql") as schema_file:
        database.executescript(schema_file.read().decode("utf-8"))
    database.commit()


@contextmanager
def transaction():
    """Run a short write transaction and commit/rollback as one unit."""
    database = get_db()
    database.execute("BEGIN IMMEDIATE")
    try:
        yield database
    except Exception:
        database.rollback()
        raise
    else:
        database.commit()


@click.command("init-db")
def init_db_command():
    init_db()
    click.echo("CampusEvent 数据库已初始化。")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)