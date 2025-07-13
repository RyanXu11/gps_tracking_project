from flask import Flask
import psycopg2
from psycopg2.extras import RealDictCursor
from settings.config import Config
from settings.constants import GOOGLE_MAPS_API_KEY
import os

app = Flask(__name__, static_folder='../static')
app.config.from_object(Config)
app.config['GOOGLE_MAPS_API_KEY'] = GOOGLE_MAPS_API_KEY


print(f"Static folder path: {app.static_folder}")
print(f"Static folder exists: {os.path.exists(app.static_folder)}")
print(f"CSS file exists: {os.path.exists(os.path.join(app.static_folder, 'css/upload_success.css'))}")

@app.context_processor
def inject_config():
    return dict(config=app.config)


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
from app.routes import main, upload, speed, api, animation, login, signup

print("Registered routes:")
for rule in app.url_map.iter_rules():
    print(f"  {rule.rule} -> {rule.endpoint}")