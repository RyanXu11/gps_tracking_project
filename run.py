from app import app, test_db_connection

if __name__ == '__main__':
    # Test the database connection
    if test_db_connection():
        print("Database connection successful!")
    else:
        print("Database connection failed!")
    
    app.run(debug=True)