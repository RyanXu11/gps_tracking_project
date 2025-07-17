# Course: CST8276
# File: tests\test_database.py
# Author: Ryan Xu
# Created: 2025-07-17
# Description: Unit test for database CRUD operation by Pytest

import pytest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app, get_db_connection

from app.models import User

print("\n\033[94mPytest for database CRUD operation, cst8276 Group 2\033[0m")

@pytest.fixture
def client():
    """This fixutre provides test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
        
@pytest.fixture
def db_conn():
    """This fixutre provides database connection"""
    conn = get_db_connection()
    conn.autocommit = True
    yield conn
    conn.close()
    

def test_signup_creates_user(client, db_conn):
    data = {
        "username": "pytestuser",
        "email": "pytest@example.com",
        "password": "123456",
        "confirmPassword": "123456"
    }
    
    # delete the test data if it exists
    cur = db_conn.cursor()
    cur.execute("DELETE FROM users WHERE username = %s", (data["username"],))
    db_conn.commit()
    
    # signup test
    response = client.post('/signup', data=data, follow_redirects=True)
    assert response.status_code == 200

    # check insert
    cur = db_conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", (data["username"],))
    user = cur.fetchone()
    assert user is not None
    assert user["email"] == "pytest@example.com"


def test_read_user(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", ('carrie',))
    user = cur.fetchone()
    assert user is not None
    assert user['username'] == 'carrie'


def test_update_user_email(db_conn):
    username = "pytestuser"
    new_email = "pytest_updated@example.com"

    cur = db_conn.cursor()

    # check if the user exists or not
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    assert user is not None

    # update email
    cur.execute("UPDATE users SET email = %s WHERE username = %s", (new_email, username))
    db_conn.commit()

    # check the user status
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    updated_user = cur.fetchone()
    assert updated_user is not None
    assert updated_user["email"] == new_email


def test_delete_user(db_conn):
    username = "pytestuser"

    cur = db_conn.cursor()

    # check if the user exists or not
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    assert user is not None

    # delete the test user
    cur.execute("DELETE FROM users WHERE username = %s", (username,))
    db_conn.commit()

    # check the user status
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user_after_delete = cur.fetchone()
    assert user_after_delete is None
