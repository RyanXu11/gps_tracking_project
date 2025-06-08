from flask import Flask
import psycopg2
from psycopg2.extras import RealDictCursor
from settings.config import Config

app = Flask(__name__, static_folder='../static')
app.config.from_object(Config)

import os
print(f"Static folder path: {app.static_folder}")
print(f"Static folder exists: {os.path.exists(app.static_folder)}")
print(f"CSS file exists: {os.path.exists(os.path.join(app.static_folder, 'css/upload_success.css'))}")

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

# Import routes after app initialization to avoid circular imports
from app.routes import main, upload, track, api

print("Registered routes:")
for rule in app.url_map.iter_rules():
    print(f"  {rule.rule} -> {rule.endpoint}")