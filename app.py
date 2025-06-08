from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = 'Prat'

# MongoDB Config
app.config["MONGO_URI"] = "mongodb://localhost:27017/clinicDB"
mongo = PyMongo(app)
users_col = mongo.db.users

# Role-based access control
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] != role:
                return abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    if 'user' in session:
        if session['role'] == 'admin':
            return redirect(url_for('admin_panel'))
        elif session['role'] == 'doctor':
            return redirect(url_for('dashboard'))
        elif session['role'] == 'patient':
            return redirect(url_for('patient_dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form['role']
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']

        if users_col.find_one({'username': username}):
            flash("Username already exists.", 'error')
            return redirect(url_for('register'))

        user_data = {
            'role': role,
            'name': name,
            'username': username,
            'password': generate_password_hash(password)
        }

        if role == 'patient':
            user_data.update({
                'gender': request.form.get('gender'),
                'age': int(request.form['age']) if request.form['age'] else None,
                'medical_history': []
            })
        elif role == 'doctor':
            user_data.update({
                'specialization': request.form['specialization'],
                'experience': int(request.form['experience']) if request.form['experience'] else None,
                'qualifications': request.form.get('qualifications', '')
            })

        users_col.insert_one(user_data)
        flash("Registration successful! Please login.", 'success')
        return redirect(url_for('login'))

    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form['role']
        username = request.form['username']
        password = request.form['password']

        user = users_col.find_one({'username': username, 'role': role})
        if user and check_password_hash(user['password'], password):
            session['user'] = user['username']
            session['name'] = user['name']
            session['role'] = role
            session['user_id'] = str(user['_id'])

            flash("Login successful!", 'success')
            return redirect(url_for('index'))

        flash("Invalid credentials.", 'error')
        return redirect(url_for('login'))

    return render_template('auth/login.html')

@app.route('/dashboard')
@role_required('doctor')
def dashboard():
    # Update last_active timestamp for doctor
    users_col.update_one({'_id': ObjectId(session['user_id'])}, {'$set': {'last_active': datetime.utcnow()}})

    patients = list(users_col.find({'role': 'patient'}, {'name': 1, 'medical_history': 1}))
    return render_template('dashboard.html', 
                           name=session.get('name'), 
                           role=session.get('role'),
                           patients=patients)

@app.route('/admin')
@role_required('admin')
def admin_panel():
    users = list(users_col.find({}, {'password': 0}))
    return render_template('admin/admin_panel.html', users=users)

@app.route('/patient/dashboard', methods=['GET', 'POST'])
@role_required('patient')
def patient_dashboard():
    user = users_col.find_one({'_id': ObjectId(session['user_id'])})

    if request.method == 'POST':
        symptom = request.form.get('symptom')
        if symptom:
            entry = {'date': datetime.utcnow(), 'symptom': symptom}
            users_col.update_one({'_id': ObjectId(session['user_id'])}, {'$push': {'medical_history': entry}})
            flash("Symptom added successfully.", "success")
            return redirect(url_for('patient_dashboard'))

    user = users_col.find_one({'_id': ObjectId(session['user_id'])})

    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
    doctors = list(users_col.find({'role': 'doctor'}))

    for doc in doctors:
        last_active = doc.get('last_active')
        doc['online'] = last_active and last_active > five_minutes_ago

    return render_template('patient/dashboard.html', user=user, doctors=doctors)

@app.route('/patient/profile', methods=['GET', 'POST'])
@role_required('patient')
def patient_profile():
    user = users_col.find_one({'_id': ObjectId(session['user_id'])})

    if request.method == 'POST':
        new_username = request.form.get('username')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')

        if not check_password_hash(user['password'], current_password):
            flash("Current password is incorrect.", "error")
            return redirect(url_for('patient_profile'))

        if new_username != user['username'] and users_col.find_one({'username': new_username}):
            flash("Username already taken.", "error")
            return redirect(url_for('patient_profile'))

        update_data = {}
        if new_username:
            update_data['username'] = new_username
        if new_password:
            update_data['password'] = generate_password_hash(new_password)

        if update_data:
            users_col.update_one({'_id': ObjectId(session['user_id'])}, {'$set': update_data})
            if 'username' in update_data:
                session['user'] = update_data['username']
            flash("Profile updated successfully.", "success")
        else:
            flash("No changes made.", "info")

        return redirect(url_for('patient_profile'))

    return render_template('patient/profile.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
