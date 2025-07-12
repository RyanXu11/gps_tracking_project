from app.models import Login, User
from app import app
from flask import request, redirect, flash
@app.route('/login', methods=['POST'])
def attempt_login():
    if Login.verify_login(request.form.get('email'), request.form.get('password')):
        # End product should use this. Fetch records specifically related to a user.
        user = User.get_by_email(request.form.get('email'))
        return redirect('/main')
    else:
        flash('Invalid email and password conbination')
        return redirect(request.url)