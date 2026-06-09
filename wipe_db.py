import os
# os.environ["POSTGRES_URL"] = "postgresql+psycopg2://postgres:Athey123@127.0.0.1:5432/adk_state"

from database import engine, Base, Run

print("Dropping all tables...")
Base.metadata.drop_all(bind=engine)
print("Recreating tables...")
Base.metadata.create_all(bind=engine)
print("Database wipe complete.")
