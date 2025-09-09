import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
# Multi-language support - manual implementation
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Multi-language configuration
app.config['LANGUAGES'] = {
    'pt': 'Português (Brasil)',
    'en': 'English',
    'es': 'Español'
}
app.config['DEFAULT_LANGUAGE'] = 'pt'

# Translation dictionaries
TRANSLATIONS = {
    'pt': {
        'Home': 'Home',
        'Dashboard': 'Dashboard',
        'Users': 'Usuários',
        'Profiles': 'Perfis',
        'Organizations': 'Organizações',
        'Backyards': 'Backyards',
        'Athletes': 'Atletas',
        'Logout': 'Sair',
        'Selecionar Idioma': 'Selecionar Idioma'
    },
    'en': {
        'Home': 'Home',
        'Dashboard': 'Dashboard',
        'Users': 'Users',
        'Profiles': 'Profiles',
        'Organizations': 'Organizations',
        'Backyards': 'Backyards',
        'Athletes': 'Athletes',
        'Logout': 'Logout',
        'Selecionar Idioma': 'Select Language'
    },
    'es': {
        'Home': 'Inicio',
        'Dashboard': 'Panel',
        'Users': 'Usuarios',
        'Profiles': 'Perfiles',
        'Organizations': 'Organizaciones',
        'Backyards': 'Backyards',
        'Athletes': 'Atletas',
        'Logout': 'Cerrar Sesión',
        'Selecionar Idioma': 'Seleccionar Idioma'
    }
}

# Translation function
def _(text, lang=None):
    if not lang:
        lang = session.get('language', app.config['DEFAULT_LANGUAGE'])
    return TRANSLATIONS.get(lang, {}).get(text, text)

# Database configuration
DB_HOST = os.environ.get('DB_HOST', 'mariadb')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_USER = os.environ.get('DB_USER', 'btl_user')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'btl_password')
DB_NAME = os.environ.get('DB_NAME', 'btl_db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import models first
from models import db, Backend_Users, Profile, Organizacao, Backyard, Atleta, AtletaBackyard

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

# Language detection function
def get_current_language():
    # 1. Check if user manually selected language via URL parameter
    if request.args.get('lang'):
        session['language'] = request.args.get('lang')
    
    # 2. Return language from session if set
    if 'language' in session and session['language'] in app.config['LANGUAGES']:
        return session['language']
    
    # 3. Check user's browser preferred languages
    return request.accept_languages.best_match(app.config['LANGUAGES'].keys()) or app.config['DEFAULT_LANGUAGE']

# Language switcher route
@app.route('/set_language/<language>')
def set_language(language):
    if language in app.config['LANGUAGES']:
        session['language'] = language
    return redirect(request.referrer or url_for('dashboard'))

# Make language functions and translation available in templates
@app.context_processor
def inject_conf_vars():
    return {
        'LANGUAGES': app.config['LANGUAGES'],
        'CURRENT_LANGUAGE': session.get('language', app.config['DEFAULT_LANGUAGE']),
        '_': _  # Make translation function available in templates
    }

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
        'total_atletas': Atleta.query.count(),
        'total_inscricoes': AtletaBackyard.query.count(),
    }
    
    # Filter based on user role
    if current_user.profile.nome == 'Organizador':
        # Show only organizations and backyards related to this user
        user_orgs = Organizacao.query.filter_by(organizador=current_user.id).all()
        org_ids = [org.id for org in user_orgs]
        stats['my_organizacoes'] = len(user_orgs)
        stats['my_backyards'] = Backyard.query.filter(Backyard.organizador.in_(org_ids)).count() if org_ids else 0
        
        # Count atletas inscribed in organizador's backyards
        if org_ids:
            my_backyard_ids = [b.id for b in Backyard.query.filter(Backyard.organizador.in_(org_ids)).all()]
            stats['my_atletas'] = db.session.query(AtletaBackyard.atleta_id).filter(
                AtletaBackyard.backyard_id.in_(my_backyard_ids)
            ).distinct().count() if my_backyard_ids else 0
            stats['my_inscricoes'] = AtletaBackyard.query.filter(
                AtletaBackyard.backyard_id.in_(my_backyard_ids)
            ).count() if my_backyard_ids else 0
        else:
            stats['my_atletas'] = 0
            stats['my_inscricoes'] = 0
    
    return render_template('dashboard.html', stats=stats)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

# Import and register blueprints
from views.users import users_bp
from views.profiles import profiles_bp
from views.organizacoes import organizacoes_bp
from views.backyards import backyards_bp
from views.atletas import atletas_bp
from views.loops import loops_bp

app.register_blueprint(users_bp, url_prefix='/users')
app.register_blueprint(profiles_bp, url_prefix='/profiles')
app.register_blueprint(organizacoes_bp, url_prefix='/organizacoes')
app.register_blueprint(backyards_bp, url_prefix='/backyards')
app.register_blueprint(atletas_bp, url_prefix='/atletas')
app.register_blueprint(loops_bp, url_prefix='/loops')

# Database initialization is handled by init_db.py

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
