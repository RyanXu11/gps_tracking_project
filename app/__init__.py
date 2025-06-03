from flask import Flask
import psycopg2
from psycopg2.extras import RealDictCursor
from settings.config import Config

app = Flask(__name__, static_folder='../static')
app.config.from_object(Config)

def get_db_connection():
    """connect to database"""
    conn = psycopg2.connect(
        app.config['DATABASE_URL'],
        cursor_factory=RealDictCursor
    )
    return conn

def test_db_connection():
    """test the database connection"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

from app import routes

print("Registered routes:")
for rule in app.url_map.iter_rules():
    print(f"  {rule.rule} -> {rule.endpoint}")