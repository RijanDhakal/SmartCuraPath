from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
from functools import wraps
from flask import jsonify

app = Flask(__name__)
app.secret_key = 'Prat1234'  

# Database setup
client = MongoClient('mongodb://localhost:27017/')
db = client['tetraman']
patients_col = db.patients
doctors_col = db.doctors
admins_col = db.admins

if not admins_col.find_one({'username': 'admin'}):
    admins_col.insert_one({
        'username': 'admin',
        'password': generate_password_hash('Prat000'),
        'role': 'admin',
        'name': 'Administrator'
    })

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or 'role' not in session:
            flash("Please log in first.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'user_id' not in session or 'role' not in session:
        return None
    
    if session['role'] == 'admin':
        return admins_col.find_one({"_id": ObjectId(session['user_id'])})
    elif session['role'] == 'doctor':
        return doctors_col.find_one({"_id": ObjectId(session['user_id'])})
    else:
        return patients_col.find_one({"_id": ObjectId(session['user_id'])})

@app.route('/')
def home():
    if 'user_id' in session and 'role' in session:
        return redirect(url_for(f"{session['role']}_dashboard"))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            role = request.form.get('role')
            name = request.form.get('name', '').strip()
            username = request.form.get('username', '').strip().lower()
            password = request.form.get('password')
            confirm = request.form.get('confirm_password')
            gender = request.form.get('gender')

            if not all([role, name, username, password, confirm, gender]):
                flash("Please fill in all required fields.", "error")
                return render_template('auth/register.html')

            if len(username) < 4:
                flash("Username must be at least 4 characters long.", "error")
                return render_template('auth/register.html')

            if not password.isalnum():
                flash("Password must be alphanumeric (letters and numbers only).", "error")
                return render_template('auth/register.html')

            if password != confirm:
                flash("Passwords do not match.", "error")
                return render_template('auth/register.html')

            if role in ['patient', 'doctor']:
                col = patients_col if role == 'patient' else doctors_col
                if col.find_one({'username': username}):
                    flash("Username already taken.", "error")
                    return render_template('auth/register.html')

            if role == 'admin':
                flash("Admin registration not allowed.", "error")
                return render_template('auth/register.html')

            user = {
                "role": role,
                "name": name,
                "username": username,
                "password": generate_password_hash(password),
                "gender": gender
            }

            if role == 'patient':
                user['age'] = request.form.get('age')
                patients_col.insert_one(user)
            else:
                user['specialization'] = request.form.get('specialization')
                user['experience'] = request.form.get('experience')
                user['availableTimeFrom'] = request.form.get('availableTimeFrom')
                user['availableTimeTo'] = request.form.get('availableTimeTo')
                doctors_col.insert_one(user)

            flash("Registration successful. Please login.", "success")
            return redirect(url_for('login'))

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
            return render_template('auth/register.html')

    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session and 'role' in session:
        return redirect(url_for(f"{session['role']}_dashboard"))
    
    if request.method == 'POST':
        role = request.form['role']
        username = request.form['username'].strip().lower()
        password = request.form['password']

        if not all([role, username, password]):
            flash("Please fill in all fields.", "error")
            return redirect(url_for('login'))

        # Check credentials based on role
        if role == 'admin':
            user = admins_col.find_one({'username': username})
        elif role == 'doctor':
            user = doctors_col.find_one({'username': username})
        elif role == 'patient':
            user = patients_col.find_one({'username': username})
        else:
            flash("Invalid role selected.", "error")
            return redirect(url_for('login'))

        if not user or not check_password_hash(user['password'], password):
            flash("Invalid username or password.", "error")
            return redirect(url_for('login'))

        # Set session and redirect to appropriate dashboard
        session['user_id'] = str(user['_id'])
        session['role'] = role
        return redirect(url_for(f"{role}_dashboard"))

    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))

@app.route('/patient/dashboard')
@login_required
def patient_dashboard():
    if session['role'] != 'patient':
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))
    user = get_current_user()
    return render_template('patient/dashboard.html', user=user)

@app.route('/patient/profile', methods=['GET', 'POST'])
@login_required
def patient_profile():
    if session['role'] != 'patient':
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))
    
    user = get_current_user()
    
    if request.method == 'POST':
        if 'edit_profile' in request.form:
            patients_col.update_one({'_id': user['_id']}, {
                '$set': {
                    'name': request.form['name'],
                    'username': request.form['username'],
                    'gender': request.form['gender'],
                    'age': request.form.get('age')
                }
            })
            flash("Profile updated successfully.", "success")
            return redirect(url_for('patient_profile'))
        elif 'change_password' in request.form:
            current_password = request.form['current_password']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']
            
            if not check_password_hash(user['password'], current_password):
                flash("Wrong current password.", "error")
            elif new_password != confirm_password:
                flash("New passwords do not match.", "error")
            else:
                patients_col.update_one({'_id': user['_id']}, {
                    '$set': {'password': generate_password_hash(new_password)}
                })
                flash("Password changed successfully.", "success")
                return redirect(url_for('patient_profile'))

    return render_template('patient/profile.html', user=user)

@app.route('/doctor/dashboard')
@login_required
def doctor_dashboard():
    if session['role'] != 'doctor':
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))
    user = get_current_user()
    return render_template('doctor/dashboard.html', user=user)

@app.route('/doctor/profile', methods=['GET', 'POST'])
@login_required
def doctor_profile():
    if session['role'] != 'doctor':
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))
    
    user = get_current_user()
    
    if request.method == 'POST':
        if 'edit_profile' in request.form:
            doctors_col.update_one({'_id': user['_id']}, {
                '$set': {
                    'name': request.form['name'],
                    'username': request.form['username'],
                    'specialization': request.form.get('specialization'),
                    'experience': request.form.get('experience'),
                    'availableTimeFrom': request.form.get('availableTimeFrom'),
                    'availableTimeTo': request.form.get('availableTimeTo')
                }
            })
            flash("Profile updated successfully.", "success")
            return redirect(url_for('doctor_profile'))
        elif 'change_password' in request.form:
            current_password = request.form['current_password']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']
            
            if not check_password_hash(user['password'], current_password):
                flash("Wrong current password.", "error")
            elif new_password != confirm_password:
                flash("New passwords do not match.", "error")
            else:
                doctors_col.update_one({'_id': user['_id']}, {
                    '$set': {'password': generate_password_hash(new_password)}
                })
                flash("Password changed successfully.", "success")
                return redirect(url_for('doctor_profile'))

    return render_template('doctor/profile.html', user=user)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if session['role'] != 'admin':
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))
    
    doctors_count = doctors_col.count_documents({})
    patients_count = patients_col.count_documents({})
    return render_template('admin/dashboard.html', 
                         doctors_count=doctors_count, 
                         patients_count=patients_count)

@app.route('/admin/doctors')
@login_required
def admin_doctors():
    if session['role'] != 'admin':
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))
    
    doctors = list(doctors_col.find())
    return render_template('admin/doctors.html', doctors=doctors)

@app.route('/admin/patients')
@login_required
def admin_patients():
    if session['role'] != 'admin':
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))
    
    patients = list(patients_col.find())
    return render_template('admin/patients.html', patients=patients)

@app.route('/admin/delete_user/<role>/<user_id>', methods=['POST'])
@login_required
def admin_delete_user(role, user_id):
    if session.get('role') != 'admin':
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    try:
        if role == 'doctor':
            doctors_col.delete_one({'_id': ObjectId(user_id)})
        elif role == 'patient':
            patients_col.delete_one({'_id': ObjectId(user_id)})
        else:
            flash("Invalid user type.", "error")
            return redirect(url_for('admin_dashboard'))

        flash("User deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting user: {str(e)}", "error")

    return redirect(url_for(f'admin_{role}s'))

if __name__ == '__main__':
    app.run(debug=True)