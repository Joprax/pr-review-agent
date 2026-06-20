# backend/init_db.py
from backend.models import create_tables

if __name__ == "__main__":
    create_tables()
    print("✅ Tables created successfully")