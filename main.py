from flask import Flask, jsonify, request, render_template, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

# Initialize the Flask app
app = Flask(__name__)

# Configure the app
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
app.config['SECRET_KEY'] = 'your_secret_key'

# Initialize the SQLAlchemy database
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)  # Used by students and admins
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin', 'lecture', or 'student'
    school_number = db.Column(db.String(80), unique=True, nullable=True)  # Used only by lectures

    def __repr__(self):
        return f'<User {self.username}>'

class Timetable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(50))
    batch = db.Column(db.String(50))
    subject = db.Column(db.String(100))
    lecture = db.Column(db.String(100))  # Changed from 'lecturer' to 'lecture'
    room = db.Column(db.String(50))
    time = db.Column(db.String(50))

    def __repr__(self):
        return f'<Timetable {self.batch} {self.subject} {self.lecture}>'  # Changed from 'lecturer' to 'lecture'

class Batch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Batch {self.name}>'

class Lecturer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f'<Lecturer {self.name}>'

# Initialize database and create the tables
with app.app_context():
    db.create_all()

    # Predefine admin users
    admin1 = User(username="admin1", password=generate_password_hash("adminpass1"), role="admin")
    admin2 = User(username="admin2", password=generate_password_hash("adminpass2"), role="admin")

    # Predefine lecture users with unique usernames
    lecturer1 = User(username="lecturer1", password=generate_password_hash("lecturerpass1"), role="lecture", school_number="dmi001")
    lecturer2 = User(username="lecturer2", password=generate_password_hash("lecturerpass2"), role="lecture", school_number="dmi002")

    # Add users only if they don't already exist
    if not User.query.filter_by(username="admin1").first():
        db.session.add(admin1)
    if not User.query.filter_by(username="admin2").first():
        db.session.add(admin2)
    if not User.query.filter_by(school_number="dmi001").first():
        db.session.add(lecturer1)
    if not User.query.filter_by(school_number="dmi002").first():
        db.session.add(lecturer2)

    db.session.commit()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        school_number = request.form['school_number']
        role = 'student'  # Only students can register

        # Check if the username already exists
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash('Username already exists. Please choose a different username.', 'danger')
            return redirect(url_for('register'))

        # Check if the school_number already exists (optional)
        existing_school_number = User.query.filter_by(school_number=school_number).first()

        if existing_school_number:
            flash('School number already exists. Please check your details.', 'danger')
            return redirect(url_for('register'))

        # Create a new user
        hashed_password = generate_password_hash(password, method='scrypt')
        new_user = User(username=username, password=hashed_password, role=role, school_number=school_number)

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful. You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get the login credentials from the form
        username = request.form['username']
        password = request.form['password']
        
        # Find the user in the database
        user = User.query.filter_by(username=username).first()
        
        # Check if user exists and password is correct
        if user and check_password_hash(user.password, password):  # Use check_password_hash
            session['user_id'] = user.id  # Store user ID in session
            session['role'] = user.role  # Store user role in session
            
            # Redirect based on user role
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard
            elif user.role == 'lecture':
                return redirect(url_for('lecture_dashboard'))  # Redirect to lecture dashboard
            elif user.role == 'student':
                return redirect(url_for('student_dashboard'))  # Redirect to student dashboard
        else:
            flash('Invalid credentials. Please try again.')

    # Pass the role variable to the template; default to '' if not logged in
    role = session.get('role', '') 
    return render_template('login.html', role=role)

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    return redirect(url_for('login'))

# Home route
@app.route('/')
def home():
    return render_template('home.html')

# Admin dashboard route
@app.route('/admin_dash')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    users = User.query.all()  # Fetch all users from the database
    return render_template('admin_dashboard.html', users=users)

@app.route('/delete_user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return '', 403  # Forbidden

    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return '', 204  # No Content
    return '', 404  # Not Found

@app.route('/edit_user/<int:user_id>', methods=['PUT'])
def edit_user(user_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return '', 403  # Forbidden

    user = User.query.get(user_id)
    if user:
        data = request.get_json()
        user.username = data.get('username', user.username)
        user.role = data.get('role', user.role)  # Allow role change, e.g., to 'admin'
        db.session.commit()
        return '', 204  # No Content
    return '', 404  # Not Found

@app.route('/add_user', methods=['POST'])
def add_user():
    if 'user_id' not in session or session['role'] != 'admin':
        return '', 403  # Forbidden

    data = request.json
    username = data.get('username')
    role = data.get('role')
    registration_number = data.get('registration_number')  # Registration number used as password

    # Check if the username already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'message': 'Username already exists.'}), 400  # Bad Request

    # Create a new user
    hashed_password = generate_password_hash(registration_number)  # Hash the registration number
    new_user = User(username=username, password=hashed_password, role=role, school_number=registration_number)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User added successfully!'}), 201 

# Lecture dashboard route
@app.route('/lecture_dash')
def lecture_dashboard():
    if 'user_id' not in session or session['role'] != 'lecture':
        return redirect(url_for('login'))
    
    lecture = User.query.get(session['user_id'])
    timetables = Timetable.query.filter_by(lecture=lecture.username).all()  # Get timetable entries for this lecture

    return render_template('lecture_dashboard.html', timetables=timetables)

# Student dashboard route
@app.route('/student_dash')
def student_dashboard():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    
    return render_template('student_dashboard.html')

@app.route('/admin_timetable', methods=['GET', 'POST'])
def admin_timetable():
    if request.method == 'POST':
        day = request.form['day']
        batch = request.form['batch']
        subject = request.form['subject']
        lecture = request.form['lecture'] 
        room = request.form['room']
        time = request.form['time']

        # Create a new timetable entry
        new_entry = Timetable(day=day, batch=batch, subject=subject, lecture=lecture, room=room, time=time)
        db.session.add(new_entry)
        db.session.commit()

        flash('Timetable entry added successfully!', 'success')
        return redirect(url_for('admin_timetable'))

    # Fetch all batches and lecturers for the dropdown
    batches = Batch.query.all()
    lecturers = User.query.filter_by(role='lecture').all()  # Only get lectures
    
    # Fetch existing timetable entries to display
    timetable_entries = Timetable.query.all()  # Fetch all entries from the database
    return render_template('admin_timetable.html', batches=batches, lecturers=lecturers, timetable=timetable_entries)

if __name__ == '__main__':
    app.run(debug=True)
