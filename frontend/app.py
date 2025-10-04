#!/usr/bin/env python3

"""
BTL Frontend Application
Aplicação frontend para atletas e público geral
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from models import db, Atleta, Backyard, AtletaBackyard, BackyardStatus
from services.image_service import ImageService
from services.password_service import PasswordService

def create_app():
    """Application factory"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database configuration (same as backoffice)
    db_host = os.environ.get('DB_HOST', 'mariadb')
    db_port = os.environ.get('DB_PORT', '3306')
    db_user = os.environ.get('DB_USER', 'btl_user')
    db_password = os.environ.get('DB_PASSWORD', 'btl_password')
    db_name = os.environ.get('DB_NAME', 'btl_db')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    
    # Setup Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return Atleta.query.get(int(user_id))
    
    # Register blueprints
    from views.home import home_bp
    from views.auth import auth_bp
    from views.profile import profile_bp
    from views.backyards import backyards_bp
    
    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    app.register_blueprint(backyards_bp, url_prefix='/backyards')
    
    # Custom Jinja2 filters
    @app.template_filter('minio_url')
    def minio_url_filter(file_path):
        """Generate MinIO URL for a file path"""
        if not file_path:
            return None
        image_service = ImageService()
        return image_service.get_public_url(file_path)
    
    # Context processors for templates
    @app.context_processor
    def inject_globals():
        return {
            'current_user': current_user,
            'datetime': datetime
        }
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'btl-frontend',
            'timestamp': datetime.now().isoformat()
        })
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=os.environ.get('FLASK_ENV') == 'development'
    )
