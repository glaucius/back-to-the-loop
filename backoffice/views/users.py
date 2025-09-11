from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, Backend_Users, Profile
from services.password_service import PasswordService
from functools import wraps

users_bp = Blueprint('users', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@users_bp.route('/')
@login_required
@admin_required
def list_users():
    page = request.args.get('page', 1, type=int)
    users = Backend_Users.query.paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('users/list.html', users=users)

@users_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        password = request.form['password']
        profile_id = request.form['profile_id']
        
        # Check if email already exists
        existing_user = Backend_Users.query.filter_by(email=email).first()
        if existing_user:
            flash('Email já existe!', 'danger')
            profiles = Profile.query.all()
            return render_template('users/create.html', profiles=profiles)
        
        # Validate password
        password_service = PasswordService()
        is_valid, errors = password_service.validate_for_flask(password, username=nome, email=email)
        if not is_valid:
            for error in errors:
                flash(f'Erro na senha: {error}', 'danger')
            profiles = Profile.query.all()
            return render_template('users/create.html', profiles=profiles)
        
        user = Backend_Users(
            nome=nome,
            email=email,
            password=generate_password_hash(password),
            profile_id=profile_id
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            flash(f'User {nome} created successfully!', 'success')
            return redirect(url_for('users.list_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'danger')
    
    profiles = Profile.query.all()
    return render_template('users/create.html', profiles=profiles)

@users_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    user = Backend_Users.query.get_or_404(id)
    
    if request.method == 'POST':
        user.nome = request.form['nome']
        user.email = request.form['email']
        user.profile_id = request.form['profile_id']
        
        # Only update password if provided
        if request.form['password']:
            user.password = generate_password_hash(request.form['password'])
        
        try:
            db.session.commit()
            flash(f'User {user.nome} updated successfully!', 'success')
            return redirect(url_for('users.list_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'danger')
    
    profiles = Profile.query.all()
    return render_template('users/edit.html', user=user, profiles=profiles)

@users_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    user = Backend_Users.query.get_or_404(id)
    
    # Prevent deleting the current user
    if user.id == current_user.id:
        flash('You cannot delete your own account!', 'danger')
        return redirect(url_for('users.list_users'))
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.nome} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
    
    return redirect(url_for('users.list_users'))
