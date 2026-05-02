"""Test db/base.py imports - quick coverage boost."""


def test_base_imports():
    from app.db import base
    assert base is not None


def test_base_has_metadata():
    from app.db.base import Base
    assert Base is not None
    assert hasattr(Base, "metadata")


def test_all_models_registered():
    from app.db.base import Base
    table_names = list(Base.metadata.tables.keys())
    assert "users" in table_names
    assert "transactions" in table_names
