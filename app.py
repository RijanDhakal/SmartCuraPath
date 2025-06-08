from flask import Flask, render_template, request, redirect, url_for, session, flash
from model import init_app, user_exists, create_user, validate_user, get_all_users

app = Flask(__name__)
app.secret_key = 'Prat'
app.config["MONGO_URI"] = "mongodb://localhost:27017/tertaman"

init_app(app)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form['role']
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']

        if user_exists(username):
            flash("Username already exists.")
            return redirect(url_for('register'))

        user_data = {
            'role': role,
            'name': name,
            'username': username,
            'password': password
        }

        if role == 'patient':
            user_data['gender'] = request.form.get('gender')
            user_data['age'] = int(request.form.get('age', 0)) or None
        elif role == 'doctor':
            user_data['specialization'] = request.form.get('specialization')
            user_data['experience'] = int(request.form.get('experience', 0)) or None

        create_user(user_data)
        flash("Registration successful! Please login.")
        return redirect(url_for('login'))

    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form['role']
        username = request.form['username']
        password = request.form['password']

        user = validate_user(role, username, password)
        if user:
            session['user'] = user['username']
            session['name'] = user['name']
            session['role'] = role

            if role == 'admin':
                return redirect(url_for('admin_panel'))
            else:
                return redirect(url_for('dashboard'))

        flash("Invalid credentials.")
        return redirect(url_for('login'))

    return render_template('auth/login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session or session.get('role') == 'admin':
        return redirect(url_for('login'))

    role = session.get('role')
    name = session.get('name')

    if role == 'patient':
        return render_template('patient/dashboard.html', name=name, role=role)
    elif role == 'doctor':
        return render_template('doctor/dashboard.html', name=name, role=role)

    return render_template('dashboard.html', name=name, role=role)

@app.route('/admin')
def admin_panel():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    users = get_all_users()
    return render_template('admin/admin_panel.html', users=users)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
