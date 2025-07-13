from app import app
from app.models import Register
from flask import request, redirect, flash, render_template, url_for


@app.route('/signup', methods=['GET'])
def signup():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def attempt_signup():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm = request.form.get('confirmPassword')

    # Basic validation
    if not username:
        flash('Username is required.', 'error')
        return redirect(url_for('signup'))
    elif not email:
        flash('Email is required.', 'error')
        return redirect(url_for('signup'))
    elif not password:
        flash('Password is required.', 'error')
        return redirect(url_for('signup'))
    elif not confirm:
        flash('Please confirm your password.', 'error')
        return redirect(url_for('signup'))
    elif password != confirm:
        flash('Passwords do not match. Please try again.', 'error')
        return redirect(url_for('signup'))
    elif Register.verify_registration(email):
        flash('This email is already in use. Please try another.', 'error')
        return redirect(url_for('signup'))

    # Register user
    Register.register_user(username, email, password)
    flash('Account created successfully! You can now log in.', 'success')
    return redirect(url_for('login'))