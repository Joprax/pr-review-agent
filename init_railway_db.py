import os
from sqlalchemy import create_engine
from backend.models import Base

# Paste your DATABASE_PUBLIC_URL directly here temporarily
DATABASE_PUBLIC_URL = "postgresql://postgres:YFxGmlImbYpMAfBrBkgivDAKhMgNKTaM@thomas.proxy.rlwy.net:37328/railway"

engine = create_engine(DATABASE_PUBLIC_URL)
Base.metadata.create_all(engine)
print("✅ Tables created successfully on Railway PostgreSQL")