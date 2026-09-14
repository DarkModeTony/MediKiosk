import os
import sys
from sqlalchemy import text
from app.database import engine

def load_env():
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_file):
        print("ERROR: .env file not found!")
        sys.exit(1)
        
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key] = value

def redact_url(url):
    # e.g., postgresql://user:pass@host:port/db
    if not url:
        return None
    try:
        parts = url.split("@")
        auth = parts[0]
        host = parts[1]
        scheme, userpass = auth.split("://")
        user = userpass.split(":")[0]
        return f"{scheme}://{user}:****@{host}"
    except Exception:
        return "REDACTED_INVALID_FORMAT"

def verify():
    load_env()
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL is empty in .env")
        sys.exit(1)
        
    print(f"Loaded DATABASE_URL: {redact_url(db_url)}")
    
    # Reload engine to use the newly set environment variable
    # Since database.py is evaluated at import, we need to create a new engine
    from sqlalchemy import create_engine
    new_engine = create_engine(db_url)
    
    try:
        with new_engine.connect() as conn:
            res = conn.execute(text("SELECT 1"))
            print(f"SUCCESS: Connected to database! Result: {res.fetchone()[0]}")
    except Exception as e:
        print(f"FAILED TO CONNECT: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    verify()
