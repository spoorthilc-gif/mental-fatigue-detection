import sqlite3
import re
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from utils.analytics import DB_PATH

# Initialize Auth Blueprint
auth = Blueprint('auth', __name__)

# Regular expression for email validation
EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'

class User(UserMixin):
    """User class implementing UserMixin for Flask-Login integration."""
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

    @staticmethod
    def get(user_id):
        """Retrieve a user by their numerical ID."""
        if not user_id:
            return None
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return User(id=row[0], username=row[1], email=row[2])

    @staticmethod
    def get_by_username(username):
        """Retrieve a user by username."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return User(id=row[0], username=row[1], email=row[2])

    @staticmethod
    def get_by_email(email):
        """Retrieve a user by email address."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return User(id=row[0], username=row[1], email=row[2])

    @staticmethod
    def verify_password(username_or_email, password):
        """Verify password against hashed DB values, returning user object if matching."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Allows logging in with either username or email
        cursor.execute("SELECT id, username, email, password_hash FROM users WHERE username = ? OR email = ?", 
                       (username_or_email, username_or_email))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        
        id, username, email, password_hash = row
        if check_password_hash(password_hash, password):
            return User(id=id, username=username, email=email)
        return None


# Helper to bind LoginManager
login_manager = LoginManager()

def init_login_manager(app):
    """Initialize LoginManager configurations on the Flask app."""
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.unauthorized_handler
    def unauthorized():
        """Return 401 JSON for API/AJAX requests, redirect for page requests."""
        from flask import request as req, jsonify as j
        if req.path.startswith('/api/') or req.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return j({"error": "unauthorized", "message": "Please log in to access this resource."}), 401
        return redirect(url_for('auth.login', next=req.url))

@login_manager.user_loader
def load_user(user_id):
    """Load user callback for Flask-Login."""
    return User.get(user_id)


# Authentication Routes
@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user profile."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validations
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')

        if len(username) < 3:
            flash('Username must be at least 3 characters long.', 'error')
            return render_template('register.html')

        if not re.match(EMAIL_REGEX, email):
            flash('Invalid email address format.', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        # Check unique constraints
        if User.get_by_username(username):
            flash('Username is already registered.', 'error')
            return render_template('register.html')

        if User.get_by_email(email):
            flash('Email is already registered.', 'error')
            return render_template('register.html')

        # Hash password and store in SQLite users table
        password_hash = generate_password_hash(password)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", 
                           (username, email, password_hash))
            conn.commit()
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash(f'An error occurred during registration: {e}', 'error')
        finally:
            conn.close()

    return render_template('register.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Authenticate and log in an existing user."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email', '').strip()
        password = request.form.get('password', '')
        remember = True if request.form.get('remember') else False

        if not username_or_email or not password:
            flash('All fields are required.', 'error')
            return render_template('login.html')

        user = User.verify_password(username_or_email, password)
        if user:
            login_user(user, remember=remember)
            # Redirect to next parameter if exists, safe checks are handled
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard')
            return redirect(next_page)
        else:
            flash('Invalid username/email or password.', 'error')

    return render_template('login.html')


@auth.route('/logout')
@login_required
def logout():
    """Log out the current authenticated user."""
    logout_user()
    flash('You have logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth.route('/demo-login')
def demo_login():
    """Directly log in as the demo recruiter account."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email FROM users WHERE username = ?", ('demo',))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        from werkzeug.security import generate_password_hash
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        password_hash = generate_password_hash('demo123')
        try:
            cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                           ('demo', 'demo@fatigueai.ai', password_hash))
            conn.commit()
            cursor.execute("SELECT id, username, email FROM users WHERE username = ?", ('demo',))
            row = cursor.fetchone()
        except Exception as e:
            flash(f"Failed to auto-generate demo account: {e}", "error")
            return redirect(url_for('auth.login'))
        finally:
            conn.close()
            
    if row:
        user = User(id=row[0], username=row[1], email=row[2])
        login_user(user, remember=True)
        flash('Logged in successfully as Recruiter Demo!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Demo account creation failed.', 'error')
        return redirect(url_for('auth.login'))
