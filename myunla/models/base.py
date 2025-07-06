import uuid
from enum import Enum

from sqlalchemy import Enum as SQLColumn
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def random_id():
    """Generate a secure random ID using UUID4."""
    return uuid.uuid4().hex[:16]


def EnumColumn(enum_class: Enum, **kwargs):
    enum_values = [e.value for e in enum_class]
    kwargs.setdefault("name", enum_class.__name__.lower())
    return SQLColumn(*enum_values, **kwargs)
