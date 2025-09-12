"""
BTL Frontend - Authentication Views
Views para login, registro e autenticação de atletas
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from models import db, Atleta
from services.password_service import PasswordService
from services.image_service import ImageService

# Create blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login de atletas"""
    if current_user.is_authenticated:
        return redirect(url_for('home.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        if not email or not password:
            flash('Email e senha são obrigatórios.', 'danger')
            return render_template('auth/login.html')
        
        # Buscar atleta pelo email
        atleta = Atleta.query.filter_by(email=email).first()
        
        if atleta and check_password_hash(atleta.password, password):
            login_user(atleta, remember=remember)
            flash(f'Bem-vindo, {atleta.nome}!', 'success')
            
            # Redirecionar para a página solicitada ou dashboard
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('profile.dashboard'))
        else:
            flash('Email ou senha incorretos.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registro de novos atletas"""
    if current_user.is_authenticated:
        return redirect(url_for('home.index'))
    
    if request.method == 'POST':
        try:
            # Get form data
            nome = request.form.get('nome')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            cpf = request.form.get('cpf')
            data_nascimento = request.form.get('data_nascimento')
            sexo = request.form.get('sexo')
            endereco = request.form.get('endereco')
            cidade = request.form.get('cidade')
            estado = request.form.get('estado')
            pais = request.form.get('pais', 'Brasil')
            
            # Validations
            if not all([nome, email, password, confirm_password]):
                flash('Nome, email e senha são obrigatórios.', 'danger')
                return render_template('auth/register.html')
            
            if password != confirm_password:
                flash('As senhas não coincidem.', 'danger')
                return render_template('auth/register.html')
            
            # Check if email already exists
            if Atleta.query.filter_by(email=email).first():
                flash('Este email já está cadastrado.', 'danger')
                return render_template('auth/register.html')
            
            # Check if CPF already exists (if provided)
            if cpf and Atleta.query.filter_by(cpf=cpf).first():
                flash('Este CPF já está cadastrado.', 'danger')
                return render_template('auth/register.html')
            
            # Validate password
            password_service = PasswordService()
            is_valid, errors = password_service.validate_for_flask(password, username=nome, email=email)
            if not is_valid:
                for error in errors:
                    flash(f'Erro na senha: {error}', 'danger')
                return render_template('auth/register.html')
            
            # Parse birth date
            data_nascimento_obj = None
            if data_nascimento:
                try:
                    data_nascimento_obj = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
                except ValueError:
                    flash('Data de nascimento inválida.', 'danger')
                    return render_template('auth/register.html')
            
            # Handle profile image upload (optional)
            imagem_perfil = None
            if 'imagem_perfil' in request.files:
                file = request.files['imagem_perfil']
                if file and file.filename:
                    try:
                        image_service = ImageService()
                        upload_result = image_service.upload_image(
                            file, 
                            image_type='profile_picture',
                            folder='atletas'
                        )
                        if upload_result['success']:
                            imagem_perfil = upload_result['file_path']
                        else:
                            for error in upload_result.get('errors', []):
                                flash(f'Erro no upload da imagem: {error}', 'warning')
                    except Exception as e:
                        flash('Erro ao fazer upload da imagem. Continuando sem imagem.', 'warning')
            
            # Create new atleta
            atleta = Atleta(
                nome=nome,
                email=email,
                password=generate_password_hash(password),
                cpf=cpf if cpf else None,
                data_nascimento=data_nascimento_obj,
                sexo=sexo if sexo else None,
                endereco=endereco if endereco else None,
                cidade=cidade if cidade else None,
                estado=estado if estado else None,
                pais=pais,
                imagem_perfil=imagem_perfil
            )
            
            db.session.add(atleta)
            db.session.commit()
            
            flash('Cadastro realizado com sucesso! Você já pode fazer login.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Erro no cadastro: {e}")
            flash('Erro interno do servidor. Tente novamente.', 'danger')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout do atleta"""
    logout_user()
    flash('Você saiu com sucesso.', 'info')
    return redirect(url_for('home.index'))
