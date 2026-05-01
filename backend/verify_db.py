from sqlalchemy import inspect
from app.db.database import engine

inspector = inspect(engine)
tables = sorted(inspector.get_table_names())

print("📊 Database Tables:")
for table in tables:
    print(f"  ✅ {table}")

expected = ['alembic_version', 'alerts', 'categories', 'insights', 'rules', 'transactions', 'users']
missing = set(expected) - set(tables)

if missing:
    print(f"\n❌ Missing tables: {missing}")
else:
    print(f"\n✅ All {len(tables)} tables created successfully!")
