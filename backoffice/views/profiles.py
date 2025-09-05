from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Profile
from functools import wraps

profiles_bp = Blueprint('profiles', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@profiles_bp.route('/')
@login_required
@admin_required
def list_profiles():
    profiles = Profile.query.all()
    return render_template('profiles/list.html', profiles=profiles)

@profiles_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_profile():
    if request.method == 'POST':
        nome = request.form['nome']
        
        # Check if profile already exists
        existing_profile = Profile.query.filter_by(nome=nome).first()
        if existing_profile:
            flash('Profile already exists!', 'danger')
            return render_template('profiles/create.html')
        
        profile = Profile(nome=nome)
        
        try:
            db.session.add(profile)
            db.session.commit()
            flash(f'Profile {nome} created successfully!', 'success')
            return redirect(url_for('profiles.list_profiles'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating profile: {str(e)}', 'danger')
    
    return render_template('profiles/create.html')

@profiles_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile(id):
    profile = Profile.query.get_or_404(id)
    
    if request.method == 'POST':
        nome = request.form['nome']
        
        # Check if another profile with this name exists
        existing_profile = Profile.query.filter(Profile.nome == nome, Profile.id != id).first()
        if existing_profile:
            flash('Profile name already exists!', 'danger')
            return render_template('profiles/edit.html', profile=profile)
        
        profile.nome = nome
        
        try:
            db.session.commit()
            flash(f'Profile {profile.nome} updated successfully!', 'success')
            return redirect(url_for('profiles.list_profiles'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')
    
    return render_template('profiles/edit.html', profile=profile)

@profiles_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_profile(id):
    profile = Profile.query.get_or_404(id)
    
    # Prevent deleting if users are using this profile
    if profile.users:
        flash(f'Cannot delete profile {profile.nome}. Users are still assigned to it!', 'danger')
        return redirect(url_for('profiles.list_profiles'))
    
    try:
        db.session.delete(profile)
        db.session.commit()
        flash(f'Profile {profile.nome} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting profile: {str(e)}', 'danger')
    
    return redirect(url_for('profiles.list_profiles'))
