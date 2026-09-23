from sqlalchemy import inspect
from sqlalchemy.orm import Session


def test_migration_creates_tables(db: Session) -> None:
    names = set(inspect(db.get_bind()).get_table_names())
    assert {"admin_users", "events", "registrations"} <= names
