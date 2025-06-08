from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'Prat'  

app.config["MONGO_URI"] = "mongodb://localhost:27017/tertaman"
mongo = PyMongo(app)
users_col = mongo.db.users


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

        # Check if username already exists
        if users_col.find_one({'username': username}):
            flash("Username already exists.")
            return redirect(url_for('register'))

        user_data = {
            'role': role,
            'name': name,
            'username': username,
            'password': generate_password_hash(password)
        }

        if role == 'patient':
            user_data['gender'] = request.form['gender']
            user_data['age'] = int(request.form['age']) if request.form['age'] else None
        elif role == 'doctor':
            user_data['specialization'] = request.form['specialization']
            user_data['experience'] = int(request.form['experience']) if request.form['experience'] else None

        users_col.insert_one(user_data)
        flash("Registration successful! Please login.")
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

    return render_template('dashboard.html', name=session.get('name'), role=session.get('role'))

@app.route('/admin')
def admin_panel():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    users = list(users_col.find({}, {'password': 0}))
    return render_template('admin/admin_panel.html', users=users)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ========== RUN ==========

if __name__ == '__main__':
    app.run(debug=True)
