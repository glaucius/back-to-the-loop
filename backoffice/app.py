import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database configuration
DB_HOST = os.environ.get('DB_HOST', 'mariadb')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_USER = os.environ.get('DB_USER', 'btl_user')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'btl_password')
DB_NAME = os.environ.get('DB_NAME', 'btl_db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import models first
from models import db, Backend_Users, Profile, Organizacao, Backyard

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return Backend_Users.query.get(int(user_id))

# Decorators for role-based access
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.profile.nome != 'Admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def organizador_or_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.profile.nome not in ['Admin', 'Organizador']:
            flash('Access denied. Insufficient privileges.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
@login_required
def index():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Backend_Users.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user, remember=True)
            flash(f'Welcome back, {user.nome}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get statistics for dashboard
    stats = {
        'total_users': Backend_Users.query.count(),
        'total_organizacoes': Organizacao.query.count(),
        'total_backyards': Backyard.query.count(),
    }
    
    # Filter based on user role
    if current_user.profile.nome == 'Organizador':
        # Show only organizations and backyards related to this user
        user_orgs = Organizacao.query.filter_by(organizador=current_user.id).all()
        org_ids = [org.id for org in user_orgs]
        stats['my_organizacoes'] = len(user_orgs)
        stats['my_backyards'] = Backyard.query.filter(Backyard.organizador.in_(org_ids)).count() if org_ids else 0
    
    return render_template('dashboard.html', stats=stats)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

# Import and register blueprints
from views.users import users_bp
from views.profiles import profiles_bp
from views.organizacoes import organizacoes_bp
from views.backyards import backyards_bp

app.register_blueprint(users_bp, url_prefix='/users')
app.register_blueprint(profiles_bp, url_prefix='/profiles')
app.register_blueprint(organizacoes_bp, url_prefix='/organizacoes')
app.register_blueprint(backyards_bp, url_prefix='/backyards')

# Database initialization is handled by init_db.py

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
