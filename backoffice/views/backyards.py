from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Backyard, Organizacao
from services.image_service import ImageService
from functools import wraps

backyards_bp = Blueprint('backyards', __name__)

def organizador_or_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.profile.nome not in ['Admin', 'Organizador']:
            flash('Access denied. Insufficient privileges.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@backyards_bp.route('/')
@login_required
@organizador_or_admin_required
def list_backyards():
    page = request.args.get('page', 1, type=int)
    
    if current_user.is_admin():
        # Admin can see all backyards
        backyards = Backyard.query.paginate(
            page=page, per_page=10, error_out=False
        )
    else:
        # Organizador can only see backyards from their organizations
        user_orgs = Organizacao.query.filter_by(organizador=current_user.id).all()
        org_ids = [org.id for org in user_orgs]
        
        if org_ids:
            backyards = Backyard.query.filter(Backyard.organizador.in_(org_ids)).paginate(
                page=page, per_page=10, error_out=False
            )
        else:
            # If no organizations, return empty pagination
            backyards = Backyard.query.filter(Backyard.id == -1).paginate(
                page=page, per_page=10, error_out=False
            )
    
    return render_template('backyards/list.html', backyards=backyards)

@backyards_bp.route('/create', methods=['GET', 'POST'])
@login_required
@organizador_or_admin_required
def create_backyard():
    if request.method == 'POST':
        nome = request.form['nome']
        organizador = request.form['organizador']
        descricao = request.form.get('descricao', '')
        endereco = request.form.get('endereco', '')
        cidade = request.form.get('cidade', '')
        estado = request.form.get('estado', '')
        pais = request.form.get('pais', '')
        
        # Parse event date/time
        data_evento = None
        if request.form.get('data_evento'):
            from datetime import datetime
            try:
                data_evento = datetime.fromisoformat(request.form.get('data_evento'))
            except ValueError:
                flash('Invalid event date format', 'warning')
        
        backyard = Backyard(
            nome=nome,
            organizador=organizador,
            descricao=descricao,
            endereco=endereco,
            cidade=cidade,
            estado=estado,
            pais=pais,
            data_evento=data_evento
        )
        
        try:
            db.session.add(backyard)
            db.session.commit()
            
            # Handle image uploads
            image_service = ImageService()
            
            # Upload profile picture
            if 'profile_picture' in request.files and request.files['profile_picture'].filename:
                profile_file = request.files['profile_picture']
                result = image_service.upload_image(profile_file, 'profile_picture', f'backyards/{backyard.id}')
                
                if result['success']:
                    backyard.profile_picture_path = result['file_path']
                else:
                    flash(f'Profile picture upload failed: {", ".join(result["errors"])}', 'warning')
            
            # Upload logo
            if 'logo' in request.files and request.files['logo'].filename:
                logo_file = request.files['logo']
                result = image_service.upload_image(logo_file, 'logo', f'backyards/{backyard.id}')
                
                if result['success']:
                    backyard.logo_path = result['file_path']
                else:
                    flash(f'Logo upload failed: {", ".join(result["errors"])}', 'warning')
            
            db.session.commit()
            flash(f'Backyard {nome} created successfully!', 'success')
            return redirect(url_for('backyards.list_backyards'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating backyard: {str(e)}', 'danger')
    
    # Get available organizations based on user role
    if current_user.is_admin():
        organizacoes = Organizacao.query.all()
    else:
        # Organizador can only create backyards for their organizations
        organizacoes = Organizacao.query.filter_by(organizador=current_user.id).all()
    
    return render_template('backyards/create.html', organizacoes=organizacoes)

@backyards_bp.route('/test-form', methods=['GET', 'POST'])
@login_required
def test_form():
    """Simple test form to debug submission issues"""
    if request.method == 'POST':
        print("TEST FORM: POST received successfully!")
        flash('Test form submitted successfully!', 'success')
        return redirect(url_for('backyards.test_form'))
    
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Test Form</title></head>
    <body>
        <h1>Test Form</h1>
        <form method="POST" action="/backyards/test-form">
            <input type="text" name="test_field" placeholder="Test field" required>
            <button type="submit">Submit Test</button>
        </form>
        <script>
            document.querySelector('form').addEventListener('submit', function(e) {
                console.log('Form submitted!');
            });
        </script>
    </body>
    </html>
    '''

@backyards_bp.route('/edit/<int:id>')
@login_required
@organizador_or_admin_required
def edit_backyard(id):
    backyard = Backyard.query.get_or_404(id)
    
    # Check if organizador can edit this backyard
    if not current_user.is_admin():
        user_orgs = Organizacao.query.filter_by(organizador=current_user.id).all()
        org_ids = [org.id for org in user_orgs]
        
        if backyard.organizador not in org_ids:
            flash('Access denied. You can only edit backyards from your organizations.', 'danger')
            return redirect(url_for('backyards.list_backyards'))
    
    # GET request - just show the form
    # Get available organizations based on user role
    if current_user.is_admin():
        organizacoes = Organizacao.query.all()
    else:
        # Organizador can only assign to their organizations
        organizacoes = Organizacao.query.filter_by(organizador=current_user.id).all()
    
    return render_template('backyards/edit.html', backyard=backyard, organizacoes=organizacoes)

@backyards_bp.route('/edit/<int:id>/update', methods=['POST'])
@login_required
@organizador_or_admin_required
def update_backyard(id):
    """Handle POST request for updating backyard"""
    print(f"DEBUG: POST request received for update_backyard {id}")
    print(f"DEBUG: Form data: {dict(request.form)}")
    print(f"DEBUG: Files: {dict(request.files)}")
    
    backyard = Backyard.query.get_or_404(id)
    
    # Check if organizador can edit this backyard
    if not current_user.is_admin():
        user_orgs = Organizacao.query.filter_by(organizador=current_user.id).all()
        org_ids = [org.id for org in user_orgs]
        
        if backyard.organizador not in org_ids:
            flash('Access denied. You can only edit backyards from your organizations.', 'danger')
            return redirect(url_for('backyards.list_backyards'))
    
    backyard.nome = request.form['nome']
    backyard.organizador = request.form['organizador']
    backyard.descricao = request.form.get('descricao', '')
    backyard.endereco = request.form.get('endereco', '')
    backyard.cidade = request.form.get('cidade', '')
    backyard.estado = request.form.get('estado', '')
    backyard.pais = request.form.get('pais', '')
    
    # Parse event date/time
    if request.form.get('data_evento'):
        from datetime import datetime
        try:
            backyard.data_evento = datetime.fromisoformat(request.form.get('data_evento'))
        except ValueError:
            flash('Invalid event date format', 'warning')
    else:
        backyard.data_evento = None
    
    try:
        # Handle image uploads
        image_service = ImageService()
        
        # Upload new profile picture if provided
        if 'profile_picture' in request.files and request.files['profile_picture'].filename:
            # Delete old image if exists
            if backyard.profile_picture_path:
                image_service.delete_image(backyard.profile_picture_path)
            
            profile_file = request.files['profile_picture']
            result = image_service.upload_image(profile_file, 'profile_picture', f'backyards/{backyard.id}')
            
            if result['success']:
                backyard.profile_picture_path = result['file_path']
            else:
                flash(f'Profile picture upload failed: {", ".join(result["errors"])}', 'warning')
        
        # Upload new logo if provided
        if 'logo' in request.files and request.files['logo'].filename:
            # Delete old image if exists
            if backyard.logo_path:
                image_service.delete_image(backyard.logo_path)
            
            logo_file = request.files['logo']
            result = image_service.upload_image(logo_file, 'logo', f'backyards/{backyard.id}')
            
            if result['success']:
                backyard.logo_path = result['file_path']
            else:
                flash(f'Logo upload failed: {", ".join(result["errors"])}', 'warning')
        
        db.session.commit()
        flash(f'Backyard {backyard.nome} updated successfully!', 'success')
        return redirect(url_for('backyards.list_backyards'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating backyard: {str(e)}', 'danger')
        return redirect(url_for('backyards.edit_backyard', id=id))

@backyards_bp.route('/view/<int:id>')
@login_required
@organizador_or_admin_required
def view_backyard(id):
    """View backyard details"""
    backyard = Backyard.query.get_or_404(id)
    
    # Check if organizador can view this backyard
    if not current_user.is_admin():
        user_orgs = Organizacao.query.filter_by(organizador=current_user.id).all()
        org_ids = [org.id for org in user_orgs]
        
        if backyard.organizador not in org_ids:
            flash('Access denied. You can only view backyards from your organizations.', 'danger')
            return redirect(url_for('backyards.list_backyards'))
    
    # Get image URLs
    image_service = ImageService()
    profile_picture_url = None
    logo_url = None
    
    if backyard.profile_picture_path:
        profile_picture_url = image_service.get_image_url(backyard.profile_picture_path)
    
    if backyard.logo_path:
        logo_url = image_service.get_image_url(backyard.logo_path)
    
    # Check if user can delete this backyard
    can_delete = current_user.is_admin()
    if not can_delete and current_user.is_organizador():
        user_orgs = Organizacao.query.filter_by(organizador=current_user.id).all()
        org_ids = [org.id for org in user_orgs]
        can_delete = backyard.organizador in org_ids
    
    return render_template('backyards/view.html', 
                         backyard=backyard, 
                         profile_picture_url=profile_picture_url,
                         logo_url=logo_url,
                         can_delete=can_delete)

@backyards_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@organizador_or_admin_required
def delete_backyard(id):
    backyard = Backyard.query.get_or_404(id)
    
    # Check if organizador can delete this backyard
    if not current_user.is_admin():
        user_orgs = Organizacao.query.filter_by(organizador=current_user.id).all()
        org_ids = [org.id for org in user_orgs]
        
        if backyard.organizador not in org_ids:
            flash('Access denied. You can only delete backyards from your organizations.', 'danger')
            return redirect(url_for('backyards.list_backyards'))
    
    try:
        # Delete images from MinIO
        image_service = ImageService()
        if backyard.profile_picture_path:
            image_service.delete_image(backyard.profile_picture_path)
        if backyard.logo_path:
            image_service.delete_image(backyard.logo_path)
        
        db.session.delete(backyard)
        db.session.commit()
        flash(f'Backyard {backyard.nome} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting backyard: {str(e)}', 'danger')
    
    return redirect(url_for('backyards.list_backyards'))

@backyards_bp.route('/image/<int:backyard_id>/<image_type>')
@login_required
def get_image(backyard_id, image_type):
    """Get image URL for a backyard"""
    try:
        print(f"DEBUG: Starting get_image - backyard_id={backyard_id}, image_type={image_type}")
        
        backyard = Backyard.query.get_or_404(backyard_id)
        print(f"DEBUG: Found backyard: {backyard.nome}")
        
        # Check access permissions
        if not current_user.is_admin():
            print(f"DEBUG: User is not admin, checking permissions")
            user_orgs = Organizacao.query.filter_by(organizador=current_user.id).all()
            org_ids = [org.id for org in user_orgs]
            
            if backyard.organizador not in org_ids:
                print(f"DEBUG: Access denied for user {current_user.id} to backyard {backyard_id}")
                return '', 403
        
        image_service = ImageService()
        
        print(f"DEBUG: Profile picture path: {backyard.profile_picture_path}")
        print(f"DEBUG: Logo path: {backyard.logo_path}")
        
        if image_type == 'profile_picture' and backyard.profile_picture_path:
            url = image_service.get_image_url(backyard.profile_picture_path)
            print(f"DEBUG: Generated profile picture URL: {url}")
            if url:
                return redirect(url)
        elif image_type == 'logo' and backyard.logo_path:
            url = image_service.get_image_url(backyard.logo_path)
            print(f"DEBUG: Generated logo URL: {url}")
            if url:
                return redirect(url)
        
        print(f"DEBUG: No image found for type {image_type}")
        # Return placeholder or 404
        return '', 404
    except Exception as e:
        print(f"DEBUG: Exception in get_image: {str(e)}")
        return '', 500

@backyards_bp.route('/delete-image/<int:id>/<image_type>', methods=['POST'])
@login_required
@organizador_or_admin_required
def delete_image(id, image_type):
    """Delete a specific image from a backyard"""
    backyard = Backyard.query.get_or_404(id)
    
    # Check if organizador can edit this backyard
    if not current_user.is_admin():
        user_orgs = Organizacao.query.filter_by(organizador=current_user.id).all()
        org_ids = [org.id for org in user_orgs]
        
        if backyard.organizador not in org_ids:
            flash('Access denied. You can only edit backyards from your organizations.', 'danger')
            return redirect(url_for('backyards.list_backyards'))
    
    image_service = ImageService()
    
    try:
        if image_type == 'profile_picture' and backyard.profile_picture_path:
            image_service.delete_image(backyard.profile_picture_path)
            backyard.profile_picture_path = None
            flash('Profile picture deleted successfully!', 'success')
        elif image_type == 'logo' and backyard.logo_path:
            image_service.delete_image(backyard.logo_path)
            backyard.logo_path = None
            flash('Logo deleted successfully!', 'success')
        else:
            flash('Image not found.', 'warning')
            return redirect(url_for('backyards.edit_backyard', id=id))
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting image: {str(e)}', 'danger')
    
    return redirect(url_for('backyards.edit_backyard', id=id))
