import os
import psycopg2
from dotenv import load_dotenv

# --- FIX: Explicitly tell Python where .env is ---
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

def get_db_connection():
    # Debug: Check if variables are actually loaded
    if not os.environ.get('DB_HOST'):
        raise RuntimeError(f"❌ Error: Could not find .env file at {env_path} or it is empty.")

    return psycopg2.connect(
        host=os.environ['DB_HOST'],
        database=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        port=os.environ['DB_PORT']
    )

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        with open('schema.sql', 'r') as f:
            cur.execute(f.read())
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    init_db()