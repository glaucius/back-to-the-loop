"""
BTL Frontend - Profile Views
Views para perfil do atleta logado
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime
from models import db, Atleta, AtletaBackyard, Backyard
from services.password_service import PasswordService
from services.image_service import ImageService

# Create blueprint
profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard do atleta"""
    try:
        # Buscar backyards em que o atleta está inscrito
        inscricoes = AtletaBackyard.query.filter_by(atleta_id=current_user.id).all()
        
        # Estatísticas do atleta
        stats = {
            'total_inscricoes': len(inscricoes),
            'backyards_ativas': len([i for i in inscricoes if i.backyard.status.value == 'ATIVO']),
            'backyards_concluidas': len([i for i in inscricoes if i.backyard.status.value == 'FINALIZADO'])
        }
        
        return render_template('profile/dashboard.html', 
                             inscricoes=inscricoes,
                             stats=stats)
    
    except Exception as e:
        print(f"Erro no dashboard: {e}")
        return render_template('profile/dashboard.html', 
                             inscricoes=[],
                             stats={'total_inscricoes': 0, 'backyards_ativas': 0, 'backyards_concluidas': 0})

@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    """Editar perfil do atleta"""
    if request.method == 'POST':
        try:
            # Get form data
            nome = request.form.get('nome')
            email = request.form.get('email')
            cpf = request.form.get('cpf')
            data_nascimento = request.form.get('data_nascimento')
            sexo = request.form.get('sexo')
            endereco = request.form.get('endereco')
            cidade = request.form.get('cidade')
            estado = request.form.get('estado')
            pais = request.form.get('pais')
            
            # Validations
            if not nome or not email:
                flash('Nome e email são obrigatórios.', 'danger')
                return render_template('profile/edit.html')
            
            # Check if email is being changed and already exists
            if email != current_user.email:
                if Atleta.query.filter_by(email=email).first():
                    flash('Este email já está sendo usado por outro atleta.', 'danger')
                    return render_template('profile/edit.html')
            
            # Check if CPF is being changed and already exists
            if cpf and cpf != current_user.cpf:
                if Atleta.query.filter_by(cpf=cpf).first():
                    flash('Este CPF já está sendo usado por outro atleta.', 'danger')
                    return render_template('profile/edit.html')
            
            # Parse birth date
            data_nascimento_obj = None
            if data_nascimento:
                try:
                    data_nascimento_obj = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
                except ValueError:
                    flash('Data de nascimento inválida.', 'danger')
                    return render_template('profile/edit.html')
            
            # Handle profile image upload (optional)
            if 'imagem_perfil' in request.files:
                file = request.files['imagem_perfil']
                if file and file.filename:
                    try:
                        image_service = ImageService()
                        
                        # Delete old image if exists
                        if current_user.imagem_perfil:
                            image_service.delete_image(current_user.imagem_perfil)
                        
                        upload_result = image_service.upload_image(
                            file, 
                            image_type='profile_picture',
                            folder='atletas'
                        )
                        if upload_result['success']:
                            current_user.imagem_perfil = upload_result['file_path']
                        else:
                            for error in upload_result.get('errors', []):
                                flash(f'Erro no upload da imagem: {error}', 'warning')
                    except Exception as e:
                        flash('Erro ao fazer upload da imagem.', 'warning')
            
            # Update atleta data
            current_user.nome = nome
            current_user.email = email
            current_user.cpf = cpf if cpf else None
            current_user.data_nascimento = data_nascimento_obj
            current_user.sexo = sexo if sexo else None
            current_user.endereco = endereco if endereco else None
            current_user.cidade = cidade if cidade else None
            current_user.estado = estado if estado else None
            current_user.pais = pais if pais else None
            current_user.data_ultima_atualizacao = datetime.utcnow()
            
            db.session.commit()
            flash('Perfil atualizado com sucesso!', 'success')
            return redirect(url_for('profile.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao atualizar perfil: {e}")
            flash('Erro interno do servidor. Tente novamente.', 'danger')
    
    return render_template('profile/edit.html')

@profile_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Alterar senha do atleta"""
    if request.method == 'POST':
        try:
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # Validations
            if not all([current_password, new_password, confirm_password]):
                flash('Todos os campos são obrigatórios.', 'danger')
                return render_template('profile/change_password.html')
            
            # Check current password
            from werkzeug.security import check_password_hash
            if not check_password_hash(current_user.password, current_password):
                flash('Senha atual incorreta.', 'danger')
                return render_template('profile/change_password.html')
            
            # Check if new passwords match
            if new_password != confirm_password:
                flash('As novas senhas não coincidem.', 'danger')
                return render_template('profile/change_password.html')
            
            # Validate new password
            password_service = PasswordService()
            is_valid, errors = password_service.validate_for_flask(
                new_password, 
                username=current_user.nome, 
                email=current_user.email
            )
            if not is_valid:
                for error in errors:
                    flash(f'Erro na nova senha: {error}', 'danger')
                return render_template('profile/change_password.html')
            
            # Update password
            current_user.password = generate_password_hash(new_password)
            current_user.data_ultima_atualizacao = datetime.utcnow()
            db.session.commit()
            
            flash('Senha alterada com sucesso!', 'success')
            return redirect(url_for('profile.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao alterar senha: {e}")
            flash('Erro interno do servidor. Tente novamente.', 'danger')
    
    return render_template('profile/change_password.html')

@profile_bp.route('/my-backyards')
@login_required
def my_backyards():
    """Minhas inscrições em backyards"""
    try:
        inscricoes = AtletaBackyard.query.filter_by(atleta_id=current_user.id).all()
        return render_template('profile/my_backyards.html', inscricoes=inscricoes)
    
    except Exception as e:
        print(f"Erro ao buscar backyards: {e}")
        return render_template('profile/my_backyards.html', inscricoes=[])
