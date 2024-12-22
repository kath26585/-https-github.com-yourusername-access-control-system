from flask import Flask, render_template_string, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

# Initialize the Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a more secure key in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///access_control.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database models
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    profile_pic = db.Column(db.String(200), nullable=True)
    
    role = db.relationship('Role', backref=db.backref('users', lazy=True))

# Initialize database
@app.before_request
def init_db():
    db.create_all()

    if not Role.query.filter_by(name='Admin').first():
        admin_role = Role(name='Admin')
        db.session.add(admin_role)
        db.session.commit()

    if not Role.query.filter_by(name='User').first():
        user_role = Role(name='User')
        db.session.add(user_role)
        db.session.commit()

    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', password_hash=generate_password_hash('admin1234'), role_id=1)
        db.session.add(admin_user)
        db.session.commit()

    if not User.query.filter_by(username='user').first():
        user_user = User(username='user', password_hash=generate_password_hash('user1234'), role_id=2)
        db.session.add(user_user)
        db.session.commit()

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))

        flash('Invalid credentials. Please try again.', 'danger')

    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Login</title>
            <style>
                body {
                    background-image: url('https://via.placeholder.com/1200x800'); /* Add your background image */
                    background-size: cover;
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .container {
                    background-color: rgba(255, 255, 255, 0.8);
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                    width: 400px;
                }
                h1 {
                    text-align: center;
                    color: #333;
                }
                label {
                    display: block;
                    margin-top: 10px;
                    font-size: 16px;
                }
                input {
                    width: 100%;
                    padding: 10px;
                    margin: 10px 0;
                    border-radius: 5px;
                    border: 1px solid #ccc;
                }
                button {
                    width: 100%;
                    padding: 10px;
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                }
                button:hover {
                    background-color: #0056b3;
                }
                .flash-message {
                    color: red;
                    font-size: 14px;
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Login</h1>
                <form method="POST">
                    <label for="username">Username</label>
                    <input type="text" name="username" required>

                    <label for="password">Password</label>
                    <input type="password" name="password" required>

                    <button type="submit">Login</button>
                </form>

                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        <ul class="flash-message">
                        {% for category, message in messages %}
                            <li>{{ message }}</li>
                        {% endfor %}
                        </ul>
                    {% endif %}
                {% endwith %}
            </div>
        </body>
        </html>
    ''')

# Route for dashboard (protected)
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Dashboard</title>
            <style>
                body {
                    background-image: url('https://via.placeholder.com/1200x800'); /* Add your background image */
                    background-size: cover;
                    font-family: Arial, sans-serif;
                    color: white;
                    text-align: center;
                    padding: 50px;
                }
                .profile {
                    margin-top: 20px;
                    background-color: rgba(0, 0, 0, 0.6);
                    padding: 20px;
                    border-radius: 10px;
                    display: inline-block;
                }
                .profile img {
                    border-radius: 50%;
                    width: 100px;
                    height: 100px;
                }
                .profile h2 {
                    margin-top: 10px;
                    font-size: 24px;
                }
                a {
                    color: white;
                    text-decoration: none;
                    margin-top: 10px;
                    display: inline-block;
                }
                a:hover {
                    color: #ffcc00;
                }
            </style>
        </head>
        <body>
            <h1>Welcome to the Dashboard</h1>
            <div class="profile">
                {% if current_user.profile_pic %}
                    <img src="{{ url_for('static', filename='uploads/' + current_user.profile_pic) }}" alt="Profile Picture">
                {% else %}
                    <img src="https://via.placeholder.com/100" alt="Profile Picture">
                {% endif %}
                <h2>{{ current_user.username }}</h2>
                <p>Role: {{ current_user.role.name }}</p>
                <a href="{{ url_for('profile') }}">Edit Profile</a> |
                <a href="{{ url_for('logout') }}">Logout</a>
            </div>
        </body>
        </html>
    ''')

# Route to logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Route for profile page (protected)
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        new_username = request.form['username']
        new_password = request.form['password']
        
        if new_username:
            current_user.username = new_username

        if new_password:
            current_user.password_hash = generate_password_hash(new_password)

        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                current_user.profile_pic = filename

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Profile</title>
            <style>
                body {
                    background-color: #f4f4f4;
                    font-family: Arial, sans-serif;
                }
                .container {
                    max-width: 600px;
                    margin: 50px auto;
                    background-color: white;
                    padding: 20px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                    border-radius: 10px;
                }
                h1 {
                    text-align: center;
                    margin-bottom: 20px;
                }
                label {
                    font-size: 16px;
                }
                input {
                    width: 100%;
                    padding: 10px;
                    margin: 10px 0;
                    border-radius: 5px;
                    border: 1px solid #ccc;
                }
                button {
                    width: 100%;
                    padding: 10px;
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                }
                button:hover {
                    background-color: #0056b3;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Update Profile</h1>
                <form method="POST" enctype="multipart/form-data">
                    <label for="username">Username</label>
                    <input type="text" name="username" value="{{ current_user.username }}" required>

                    <label for="password">New Password (Leave blank to keep current)</label>
                    <input type="password" name="password">

                    <label for="profile_pic">Profile Picture</label>
                    <input type="file" name="profile_pic">

                    <button type="submit">Update Profile</button>
                </form>
                {% if current_user.profile_pic %}
                    <h3>Current Profile Picture:</h3>
                    <img src="{{ url_for('static', filename='uploads/' + current_user.profile_pic) }}" alt="Profile Picture" width="100">
                {% endif %}
            </div>
        </body>
        </html>
    ''')

# Helper function to check file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Main entry point to run the app
if __name__ == "__main__":
    app.run(debug=True)
