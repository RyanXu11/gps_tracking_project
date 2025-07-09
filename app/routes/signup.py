from app import app
from app.models import Register
from flask import request, redirect, flash
@app.route('/signup', methods=['POST'])
def attempt_signup():
    if not Register.verify_registration(request.form.get('email')):
        Register.register_user(request.form.get('username'),request.form.get('email'),request.form.get('password'))
        flash('Account Created. Returning to Login Page')
        return redirect('/login')
    else:
        flash('This email is already in use. Please Try again')
        return redirect(request.url)