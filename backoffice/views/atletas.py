from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import db, Atleta, Backyard, AtletaBackyard
from services.image_service import ImageService
import os

# Create blueprint
atletas_bp = Blueprint('atletas', __name__)

# Initialize image service
image_service = ImageService()

def admin_required(f):
    """Decorator to require admin access"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.profile.nome != 'Admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def organizador_or_admin_required(f):
    """Decorator to require organizador or admin access"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.profile.nome not in ['Admin', 'Organizador']:
            flash('Access denied. Insufficient privileges.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@atletas_bp.route('/')
@login_required
@organizador_or_admin_required
def list():
    """List all atletas"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Build query based on user role
    if current_user.profile.nome == 'Admin':
        # Admin can see all atletas
        atletas = Atleta.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
    else:
        # Organizador can see atletas inscribed in their backyards
        user_orgs = [org.id for org in current_user.organizacoes]
        atletas_ids = db.session.query(AtletaBackyard.atleta_id).join(Backyard).filter(
            Backyard.organizador.in_(user_orgs)
        ).distinct().subquery()
        
        atletas = Atleta.query.filter(
            Atleta.id.in_(atletas_ids)
        ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('atletas/list.html', atletas=atletas)

@atletas_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    """Create new atleta"""
    if request.method == 'POST':
        try:
            # Get form data
            nome = request.form['nome']
            cpf = request.form['cpf']
            email = request.form['email']
            password = request.form['password']
            data_nascimento = request.form.get('data_nascimento')
            endereco = request.form.get('endereco')
            cidade = request.form.get('cidade')
            estado = request.form.get('estado')
            pais = request.form.get('pais')
            
            # Validate required fields
            if not nome or not cpf or not email or not password:
                flash('Nome, CPF, email e password são obrigatórios.', 'danger')
                return render_template('atletas/create.html')
            
            # Check if email or CPF already exists
            if Atleta.query.filter_by(email=email).first():
                flash('Email já cadastrado.', 'danger')
                return render_template('atletas/create.html')
            
            if Atleta.query.filter_by(cpf=cpf).first():
                flash('CPF já cadastrado.', 'danger')
                return render_template('atletas/create.html')
            
            # Handle image upload
            imagem_perfil = None
            
            # Check if we have a cropped image (base64 data)
            cropped_image = request.form.get('cropped_image')
            if cropped_image and cropped_image.startswith('data:image/'):
                try:
                    # Process base64 cropped image
                    import base64
                    
                    # Extract base64 data
                    header, data = cropped_image.split(',', 1)
                    image_data = base64.b64decode(data)
                    
                    # Upload the cropped image data directly
                    upload_result = image_service.upload_image_data(image_data, 'cropped_profile.jpg', 'profile_picture', 'atletas')
                    
                    if upload_result.get('success'):
                        imagem_perfil = upload_result['file_path']
                    else:
                        flash(f'Erro no upload da imagem cortada: {", ".join(upload_result.get("errors", ["Erro desconhecido"]))}', 'warning')
                        
                except Exception as e:
                    flash(f'Erro ao processar imagem cortada: {str(e)}', 'warning')
                    
            # Fallback to regular file upload if no cropped image
            elif 'imagem_perfil' in request.files:
                file = request.files['imagem_perfil']
                if file and file.filename != '':
                    try:
                        upload_result = image_service.upload_image(file, 'profile_picture', 'atletas')
                        if upload_result.get('success'):
                            imagem_perfil = upload_result['file_path']
                        else:
                            flash(f'Erro no upload da imagem: {", ".join(upload_result.get("errors", ["Erro desconhecido"]))}', 'warning')
                    except Exception as e:
                        flash(f'Erro no upload da imagem: {str(e)}', 'warning')
            
            # Parse date
            data_nascimento_obj = None
            if data_nascimento:
                try:
                    data_nascimento_obj = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
                except ValueError:
                    flash('Formato de data inválido.', 'danger')
                    return render_template('atletas/create.html')
            
            # Create new atleta
            atleta = Atleta(
                nome=nome,
                cpf=cpf,
                email=email,
                password=generate_password_hash(password),
                data_nascimento=data_nascimento_obj,
                imagem_perfil=imagem_perfil,
                endereco=endereco,
                cidade=cidade,
                estado=estado,
                pais=pais
            )
            
            db.session.add(atleta)
            db.session.commit()
            
            flash('Atleta criado com sucesso!', 'success')
            return redirect(url_for('atletas.list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar atleta: {str(e)}', 'danger')
    
    return render_template('atletas/create.html')

@atletas_bp.route('/<int:id>')
@login_required
@organizador_or_admin_required
def view(id):
    """View atleta details"""
    atleta = Atleta.query.get_or_404(id)
    
    # Check if user can view this atleta
    if current_user.profile.nome != 'Admin':
        # Organizador can only view atletas inscribed in their backyards
        user_orgs = [org.id for org in current_user.organizacoes]
        atleta_in_orgs = db.session.query(AtletaBackyard).join(Backyard).filter(
            AtletaBackyard.atleta_id == id,
            Backyard.organizador.in_(user_orgs)
        ).first()
        
        if not atleta_in_orgs:
            flash('Access denied.', 'danger')
            return redirect(url_for('atletas.list'))
    
    # Get atleta's backyard inscriptions
    inscricoes = db.session.query(AtletaBackyard, Backyard).join(
        Backyard, AtletaBackyard.backyard_id == Backyard.id
    ).filter(AtletaBackyard.atleta_id == id).all()
    
    return render_template('atletas/view.html', atleta=atleta, inscricoes=inscricoes)

@atletas_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(id):
    """Edit atleta"""
    atleta = Atleta.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Get form data
            nome = request.form['nome']
            cpf = request.form['cpf']
            email = request.form['email']
            data_nascimento = request.form.get('data_nascimento')
            endereco = request.form.get('endereco')
            cidade = request.form.get('cidade')
            estado = request.form.get('estado')
            pais = request.form.get('pais')
            
            # Validate required fields
            if not nome or not cpf or not email:
                flash('Nome, CPF e email são obrigatórios.', 'danger')
                return render_template('atletas/edit.html', atleta=atleta)
            
            # Check if email or CPF already exists (excluding current atleta)
            existing_email = Atleta.query.filter(Atleta.email == email, Atleta.id != id).first()
            if existing_email:
                flash('Email já cadastrado por outro atleta.', 'danger')
                return render_template('atletas/edit.html', atleta=atleta)
            
            existing_cpf = Atleta.query.filter(Atleta.cpf == cpf, Atleta.id != id).first()
            if existing_cpf:
                flash('CPF já cadastrado por outro atleta.', 'danger')
                return render_template('atletas/edit.html', atleta=atleta)
            
            # Handle image upload
            # Check if we have a cropped image (base64 data)
            cropped_image = request.form.get('cropped_image')
            if cropped_image and cropped_image.startswith('data:image/'):
                try:
                    # Process base64 cropped image
                    import base64
                    
                    # Extract base64 data
                    header, data = cropped_image.split(',', 1)
                    image_data = base64.b64decode(data)
                    
                    # Upload the cropped image data directly
                    upload_result = image_service.upload_image_data(image_data, 'cropped_profile.jpg', 'profile_picture', 'atletas')
                    
                    if upload_result.get('success'):
                        # Delete old image if exists
                        if atleta.imagem_perfil:
                            image_service.delete_image(atleta.imagem_perfil)
                        
                        atleta.imagem_perfil = upload_result['file_path']
                    else:
                        flash(f'Erro no upload da imagem cortada: {", ".join(upload_result.get("errors", ["Erro desconhecido"]))}', 'warning')
                        
                except Exception as e:
                    flash(f'Erro ao processar imagem cortada: {str(e)}', 'warning')
                    
            # Fallback to regular file upload if no cropped image
            elif 'imagem_perfil' in request.files:
                file = request.files['imagem_perfil']
                if file and file.filename != '':
                    try:
                        upload_result = image_service.upload_image(file, 'profile_picture', 'atletas')
                        if upload_result.get('success'):
                            # Delete old image if exists
                            if atleta.imagem_perfil:
                                image_service.delete_image(atleta.imagem_perfil)
                            
                            atleta.imagem_perfil = upload_result['file_path']
                        else:
                            flash(f'Erro no upload da imagem: {", ".join(upload_result.get("errors", ["Erro desconhecido"]))}', 'warning')
                    except Exception as e:
                        flash(f'Erro no upload da imagem: {str(e)}', 'warning')
            
            # Parse date
            data_nascimento_obj = None
            if data_nascimento:
                try:
                    data_nascimento_obj = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
                except ValueError:
                    flash('Formato de data inválido.', 'danger')
                    return render_template('atletas/edit.html', atleta=atleta)
            
            # Update password if provided
            password = request.form.get('password')
            if password:
                atleta.password = generate_password_hash(password)
            
            # Update atleta
            atleta.nome = nome
            atleta.cpf = cpf
            atleta.email = email
            atleta.data_nascimento = data_nascimento_obj
            atleta.endereco = endereco
            atleta.cidade = cidade
            atleta.estado = estado
            atleta.pais = pais
            
            db.session.commit()
            flash('Atleta atualizado com sucesso!', 'success')
            return redirect(url_for('atletas.view', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar atleta: {str(e)}', 'danger')
    
    return render_template('atletas/edit.html', atleta=atleta)

@atletas_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete(id):
    """Delete atleta"""
    try:
        atleta = Atleta.query.get_or_404(id)
        
        # Delete image if exists
        if atleta.imagem_perfil:
            try:
                image_service.delete_image(atleta.imagem_perfil)
            except:
                pass  # Continue even if image deletion fails
        
        # Delete related inscriptions first
        AtletaBackyard.query.filter_by(atleta_id=id).delete()
        
        db.session.delete(atleta)
        db.session.commit()
        
        flash('Atleta excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir atleta: {str(e)}', 'danger')
    
    return redirect(url_for('atletas.list'))

@atletas_bp.route('/<int:id>/inscricoes')
@login_required
@organizador_or_admin_required
def inscricoes(id):
    """Manage atleta inscriptions in backyards"""
    atleta = Atleta.query.get_or_404(id)
    
    # Check if user can manage this atleta
    if current_user.profile.nome != 'Admin':
        # Organizador can only manage atletas inscribed in their backyards
        user_orgs = [org.id for org in current_user.organizacoes]
        atleta_in_orgs = db.session.query(AtletaBackyard).join(Backyard).filter(
            AtletaBackyard.atleta_id == id,
            Backyard.organizador.in_(user_orgs)
        ).first()
        
        if not atleta_in_orgs:
            flash('Access denied.', 'danger')
            return redirect(url_for('atletas.list'))
    
    # Get available backyards for inscription
    if current_user.profile.nome == 'Admin':
        available_backyards = Backyard.query.all()
    else:
        user_orgs = [org.id for org in current_user.organizacoes]
        available_backyards = Backyard.query.filter(Backyard.organizador.in_(user_orgs)).all()
    
    # Get current inscriptions
    current_inscricoes = db.session.query(AtletaBackyard, Backyard).join(
        Backyard, AtletaBackyard.backyard_id == Backyard.id
    ).filter(AtletaBackyard.atleta_id == id).all()
    
    return render_template('atletas/inscricoes.html', 
                         atleta=atleta, 
                         available_backyards=available_backyards,
                         current_inscricoes=current_inscricoes)

@atletas_bp.route('/<int:atleta_id>/inscrever/<int:backyard_id>', methods=['POST'])
@login_required
@organizador_or_admin_required
def inscrever_backyard(atleta_id, backyard_id):
    """Inscribe atleta in backyard"""
    try:
        # Check if already inscribed
        existing = AtletaBackyard.query.filter_by(
            atleta_id=atleta_id, 
            backyard_id=backyard_id
        ).first()
        
        if existing:
            flash('Atleta já inscrito neste backyard.', 'warning')
        else:
            inscricao = AtletaBackyard(
                atleta_id=atleta_id,
                backyard_id=backyard_id,
                status_inscricao='inscrito'
            )
            db.session.add(inscricao)
            db.session.commit()
            flash('Atleta inscrito com sucesso!', 'success')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao inscrever atleta: {str(e)}', 'danger')
    
    return redirect(url_for('atletas.inscricoes', id=atleta_id))

@atletas_bp.route('/inscricao/<int:inscricao_id>/cancelar', methods=['POST'])
@login_required
@organizador_or_admin_required
def cancelar_inscricao(inscricao_id):
    """Cancel atleta inscription"""
    try:
        inscricao = AtletaBackyard.query.get_or_404(inscricao_id)
        inscricao.status_inscricao = 'cancelado'
        db.session.commit()
        flash('Inscrição cancelada com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao cancelar inscrição: {str(e)}', 'danger')
    
    return redirect(url_for('atletas.inscricoes', id=inscricao.atleta_id))

@atletas_bp.route('/image/<int:atleta_id>')
@login_required
@organizador_or_admin_required
def get_image(atleta_id):
    """Get image URL for an atleta"""
    try:
        atleta = Atleta.query.get_or_404(atleta_id)
        
        # Check access permissions
        if current_user.profile.nome != 'Admin':
            # Organizador can only view atletas inscribed in their backyards
            user_orgs = [org.id for org in current_user.organizacoes]
            atleta_in_orgs = db.session.query(AtletaBackyard).join(Backyard).filter(
                AtletaBackyard.atleta_id == atleta_id,
                Backyard.organizador.in_(user_orgs)
            ).first()
            
            if not atleta_in_orgs:
                return '', 403
        
        if atleta.imagem_perfil:
            image_service = ImageService()
            url = image_service.get_image_url(atleta.imagem_perfil)
            if url:
                return redirect(url)
        
        # Return placeholder or 404
        return '', 404
    except Exception as e:
        return '', 500
