import os
from flask import Blueprint, render_template, request, url_for, redirect, flash, Flask, abort, send_from_directory
from flask_login import login_required, current_user
from xml.dom import minidom
from lxml import etree
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import Note, User
from app import db

import base64

main = Blueprint('main', __name__)


ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'svg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/')
def index():
    return redirect(url_for('auth.login'))

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@main.route('/profile/edit', methods=['POST'])
@login_required
def profile_edit():
    user_id = request.form.get('user_id')
    email = request.form.get('email')
    name = request.form.get('name')
    username = request.form.get('username')
    user = User.query.filter_by(id=user_id).first()
        
    user.name = name
    user.email = email
    user.username = username
    db.session.commit()

    return redirect(url_for('main.profile'))

@main.route('/profile/security', methods=['POST'])
@login_required
def profile_security_edit():
    json_data = request.json
    user_id = json_data['user_id']
    new_password = json_data['new_password']
    confirm_new_password = json_data['confirm_new_password']

    user = User.query.filter_by(id=user_id).first()

    if new_password != confirm_new_password:
         return render_template('profile.html', change_password_failed=True)
    
    user.password = generate_password_hash(new_password, method='sha256')
    db.session.commit()

    return render_template('profile.html', change_password_successfull=True)

@main.route('/delete-account', methods=['GET'])
@login_required
def delete_account():
    user = User.query.filter_by(id=current_user.id).first()

    if user.avatar_name != 'profile.png':
        os.system(f"rm ./uploads/profile/{user.avatar_name}")

    db.session.delete(user)
    db.session.commit()

    return redirect(url_for('auth.register'))

@main.route('/dashboard')
@login_required
def dashboard():
    notes = Note.query.filter_by(user_id=current_user.id)
    all_notes = []
    for note in notes:
        all_notes.append(note)

    total_notes = len(all_notes)

    return render_template('dashboard.html', notes=all_notes, total_notes=total_notes)

@main.route('/note')
@login_required
def view_note():
    if request.method == 'GET':
        note_id = request.args.get('id', '')
        note = Note.query.filter_by(id=note_id).first()
    elif request.method == 'POST':
        note_id = request.form.get('id')
        note = Note.query.filter_by(id=note_id).first()

    notes = Note.query.filter_by(user_id=current_user.id)

    return render_template('note.html', current_note=note)



@main.route('/add-note', methods=['POST'])
@login_required
def add_note_post():
    # create new note with the form data.
    title = request.form.get('note-title')
    content = request.form.get('note-content')
    new_note = Note(title=title, user_id=current_user.id, content=content)

    user = User.query.filter_by(id=current_user.id).first()
    
    db.session.add(new_note)
    db.session.commit()

    return redirect(url_for('main.dashboard'))

@main.route('/delete-note', methods=['GET', 'POST'])
@login_required
def delete_note():
    if request.method == 'GET':
        note_id = request.args.get('id', '')
    elif request.method == 'POST':
        note_id = request.form.get('id')
    
    note = Note.query.filter_by(id=note_id).first()
    if note:
        db.session.delete(note)
        db.session.commit()

    db.session.commit()

    return redirect(url_for('main.dashboard'))

@main.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join('./uploads/profile', filename))

            user = User.query.filter_by(id=current_user.id).first()
            
            if user.avatar_name != 'profile.png':
                os.system(f"rm ./uploads/profile/{user.avatar_name}")

            user.avatar_name = filename
            db.session.commit()

            return redirect(url_for('main.profile'))

@main.route('/uploads/profile/<filename>')
def uploaded_file(filename):
    try:
        file = open(f"./uploads/profile/{filename}")
        file_data = file.read()
        xml = file_data
        parser = etree.XMLParser(no_network=False)
        doc = etree.tostring(etree.fromstring(str(xml), parser))
        return doc
    except Exception as e:
        return send_from_directory('./uploads/profile', filename), 200, {'Content-Type': 'image/jpeg; charset=utf-8'}