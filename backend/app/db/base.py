"""
Import all models here for Alembic migrations
"""
from app.db.database import Base
from app.models.user import User
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.insight import Insight
from app.models.rule import Rule
from app.models.alert import Alert
