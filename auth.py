from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Note
from flask_login import login_user
from app import db

import binascii
import os

auth = Blueprint('auth', __name__)

def generate_key():
    return binascii.hexlify(os.urandom(20)).decode()

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    # check if user actually exists
    # take the user supplied password, hash it, and compare it to the hashed password in database
    if not user or not check_password_hash(user.password, password):
        return render_template('login.html', login_failed=True)    
     
    login_user(user, remember=remember)
    db.session.commit()

    return redirect(url_for('main.dashboard'))
    
@auth.route('/register')
def register():
    return render_template('register.html')

@auth.route('/register', methods=['POST'])    
def register_post():
    email = request.form.get('email')
    username = request.form.get('username')
    name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

    if user: # if a user is found, we want to redirect back to register page so user can try again
        return redirect(url_for('auth.register'))

    # create new user with the form data. Hash the password so plaintext version isn't saved.
    new_user = User(email=email, username=username, name=name, password=generate_password_hash(password, method='sha256'), avatar_name='profile.png')

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    if user:
        flash('Email address already exists')
        return redirect(url_for('auth.register'))    

    return redirect(url_for('auth.login'))

@auth.route('/logout')
def logout():
    return redirect(url_for('auth.login'))