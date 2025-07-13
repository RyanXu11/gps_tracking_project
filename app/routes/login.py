from app.models import Login, User
from app import app
from flask import request, redirect, flash, session, render_template, url_for

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def attempt_login():
    if Login.verify_login(request.form.get('email'), request.form.get('password')):
        # End product should use this. Fetch records specifically related to a user.
        user = User.get_by_email(request.form.get('email'))
        if user:
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        
    flash('Invalid email and password combination')
    return redirect(url_for('login'))