import os
import sys
from alembic.config import main

def run():
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    os.environ[key] = value
    sys.argv[0] = 'alembic'
    main(sys.argv[1:])

if __name__ == "__main__":
    run()
