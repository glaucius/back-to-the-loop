from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import login_required, current_user
from models import db, Backyard, Organizacao, AtletaBackyard, Atleta, Loop, AtletaLoop
from services.image_service import ImageService
from functools import wraps
from sqlalchemy import func, or_, case
from datetime import datetime, date
import csv
import json
import io

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
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)
    status_filter = request.args.get('status', '', type=str)
    show_past = request.args.get('show_past', False, type=bool)
    date_from = request.args.get('date_from', '', type=str)
    date_to = request.args.get('date_to', '', type=str)
    
    # Base query with athlete count
    query = db.session.query(
        Backyard,
        func.count(AtletaBackyard.id).label('total_atletas')
    ).outerjoin(AtletaBackyard).group_by(Backyard.id)
    
    # Apply search filter if provided
    if search:
        search_filter = or_(
            Backyard.nome.ilike(f'%{search}%'),
            Backyard.cidade.ilike(f'%{search}%'),
            Backyard.estado.ilike(f'%{search}%'),
            Backyard.descricao.ilike(f'%{search}%')
        )
        query = query.filter(search_filter)
    
    # Apply status filter if provided
    if status_filter:
        if status_filter == 'ATIVO':
            query = query.filter(Backyard.status == 'ATIVO')
        elif status_filter == 'PREPARACAO':
            query = query.filter(Backyard.status == 'PREPARACAO')
        elif status_filter == 'FINALIZADO':
            query = query.filter(Backyard.status == 'FINALIZADO')
        elif status_filter == 'CANCELADO':
            query = query.filter(Backyard.status == 'CANCELADO')
    
    # Apply date filters
    hoje = date.today()
    
    # Parse date filters if provided
    date_from_obj = None
    date_to_obj = None
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
        except ValueError:
            pass
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Apply date range filter if provided
    if date_from_obj:
        query = query.filter(func.date(Backyard.data_evento) >= date_from_obj)
    if date_to_obj:
        query = query.filter(func.date(Backyard.data_evento) <= date_to_obj)
    
    # If not showing past events and no specific date filter, hide past events
    if not show_past and not date_from_obj and not date_to_obj:
        query = query.filter(
            or_(
                Backyard.data_evento.is_(None),  # Events without date
                func.date(Backyard.data_evento) >= hoje,  # Future events
                Backyard.status == 'ATIVO'  # Active events (regardless of date)
            )
        )
    
    # Apply user role permissions
    if current_user.is_admin():
        # Admin can see all backyards
        pass
    else:
        # Organizador can only see backyards from their organizations
        user_orgs = Organizacao.query.filter_by(organizador=current_user.id).all()
        org_ids = [org.id for org in user_orgs]
        
        if org_ids:
            query = query.filter(Backyard.organizador.in_(org_ids))
        else:
            # If no organizations, return empty results
            query = query.filter(Backyard.id == -1)
    
    # Smart ordering: Active events first, then by date (closest first)
    query = query.order_by(
        # Priority 1: Active events first
        case(
            (Backyard.status == 'ATIVO', 0),
            else_=1
        ),
        # Priority 2: Events with dates, ordered chronologically
        case(
            (Backyard.data_evento.is_(None), 1),  # Events without date go last
            else_=0
        ),
        Backyard.data_evento.asc(),  # Closest dates first (MySQL/MariaDB compatible)
        Backyard.data_criacao.desc()  # Fallback: newest first
    )
    
    # Paginate results
    backyards = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('backyards/list.html', 
                         backyards=backyards, 
                         search=search, 
                         status_filter=status_filter,
                         show_past=show_past,
                         date_from=date_from,
                         date_to=date_to,
                         per_page=per_page,
                         hoje=hoje)

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
        
        # Parse bib number configuration
        capacidade = None
        if request.form.get('capacidade'):
            try:
                capacidade = int(request.form.get('capacidade'))
            except ValueError:
                flash('Invalid capacity value', 'warning')
        
        numero_inicial = None
        if request.form.get('numero_inicial'):
            try:
                numero_inicial = int(request.form.get('numero_inicial'))
            except ValueError:
                flash('Invalid starting bib number value', 'warning')
        
        backyard = Backyard(
            nome=nome,
            organizador=organizador,
            descricao=descricao,
            endereco=endereco,
            cidade=cidade,
            estado=estado,
            pais=pais,
            data_evento=data_evento,
            capacidade=capacidade,
            numero_inicial=numero_inicial
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
    
    # Parse bib number configuration
    if request.form.get('capacidade'):
        try:
            backyard.capacidade = int(request.form.get('capacidade'))
        except ValueError:
            flash('Invalid capacity value', 'warning')
    else:
        backyard.capacidade = None
    
    if request.form.get('numero_inicial'):
        try:
            backyard.numero_inicial = int(request.form.get('numero_inicial'))
        except ValueError:
            flash('Invalid starting bib number value', 'warning')
    else:
        backyard.numero_inicial = None
    
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
    
    # Estatísticas dos números de peito
    total_inscricoes = AtletaBackyard.query.filter_by(backyard_id=id).count()
    inscricoes_com_numero = AtletaBackyard.query.filter_by(backyard_id=id).filter(AtletaBackyard.numero_peito.isnot(None)).count()
    inscricoes_sem_numero = total_inscricoes - inscricoes_com_numero
    
    # Lista de atletas inscritos com números
    atletas_inscritos = db.session.query(AtletaBackyard, Atleta).join(
        Atleta, AtletaBackyard.atleta_id == Atleta.id
    ).filter(AtletaBackyard.backyard_id == id).order_by(AtletaBackyard.numero_peito.asc()).all()
    
    return render_template('backyards/view.html', 
                         backyard=backyard, 
                         profile_picture_url=profile_picture_url,
                         logo_url=logo_url,
                         can_delete=can_delete,
                         total_inscricoes=total_inscricoes,
                         inscricoes_com_numero=inscricoes_com_numero,
                         inscricoes_sem_numero=inscricoes_sem_numero,
                         atletas_inscritos=atletas_inscritos)

@backyards_bp.route('/<int:id>/gerar-numeros', methods=['POST'])
@login_required
@organizador_or_admin_required
def gerar_numeros_peito(id):
    """Gera números de peito para atletas inscritos que não possuem número"""
    try:
        backyard = Backyard.query.get_or_404(id)
        
        # Check if organizador can manage this backyard
        if not current_user.is_admin():
            user_orgs = Organizacao.query.filter_by(organizador=current_user.id).all()
            org_ids = [org.id for org in user_orgs]
            
            if backyard.organizador not in org_ids:
                return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        # Gerar números usando o método do modelo
        numeros_gerados = backyard.gerar_numeros_peito()
        
        if numeros_gerados > 0:
            return jsonify({
                'success': True, 
                'message': f'{numeros_gerados} números de peito gerados com sucesso!',
                'numeros_gerados': numeros_gerados
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'Nenhum número foi gerado. Todos os atletas já possuem números ou a capacidade foi esgotada.'
            })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao gerar números: {str(e)}'}), 500

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
        
        # Delete related records in the correct order to avoid foreign key constraints
        
        # 1. Delete atleta_loops records for all loops of this backyard
        from models import Loop, AtletaLoop
        loops = Loop.query.filter_by(backyard_id=id).all()
        loop_ids = [loop.id for loop in loops]
        
        if loop_ids:
            # Delete from atleta_loops table (now correctly mapped in the model)
            AtletaLoop.query.filter(AtletaLoop.loop_id.in_(loop_ids)).delete(synchronize_session=False)
        
        # 2. Delete loops
        Loop.query.filter_by(backyard_id=id).delete()
        
        # 3. Delete atleta_backyard registrations
        AtletaBackyard.query.filter_by(backyard_id=id).delete()
        
        # 4. Finally delete the backyard itself
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

@backyards_bp.route('/export/<int:id>')
@login_required
@organizador_or_admin_required
def export_backyard_data(id):
    """Exportar dados da backyard em formato CSV ou JSON"""
    backyard = Backyard.query.get_or_404(id)
    
    # Verificar permissão
    if not current_user.is_admin():
        user_orgs = Organizacao.query.filter_by(organizador=current_user.id).all()
        org_ids = [org.id for org in user_orgs]
        
        if backyard.organizador not in org_ids:
            flash('Access denied. You can only export data from your organizations.', 'danger')
            return redirect(url_for('backyards.list_backyards'))
    
    # Buscar dados completos
    atletas_inscritos = db.session.query(AtletaBackyard, Atleta).join(
        Atleta, AtletaBackyard.atleta_id == Atleta.id
    ).filter(AtletaBackyard.backyard_id == id).order_by(AtletaBackyard.numero_peito.asc()).all()
    
    # Buscar loops se existirem
    loops = Loop.query.filter_by(backyard_id=id).order_by(Loop.numero_loop).all()
    
    # Buscar dados dos atletas em loops
    atletas_loops = {}
    for loop in loops:
        atletas_no_loop = AtletaLoop.query.filter_by(loop_id=loop.id).all()
        atletas_loops[loop.id] = atletas_no_loop
    
    format_type = request.args.get('format', 'csv').lower()
    
    if format_type == 'csv':
        return _export_csv(backyard, atletas_inscritos, loops, atletas_loops)
    elif format_type == 'json':
        return _export_json(backyard, atletas_inscritos, loops, atletas_loops)
    else:
        flash('Formato de exportação inválido!', 'danger')
        return redirect(url_for('backyards.view_backyard', id=id))

def _export_csv(backyard, atletas_inscritos, loops, atletas_loops):
    """Exportar dados em formato CSV"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Cabeçalho do arquivo
    writer.writerow(['# DADOS DA BACKYARD'])
    writer.writerow(['Nome', backyard.nome])
    writer.writerow(['Organizacao', backyard.organizacao.nome])
    writer.writerow(['Data do Evento', backyard.data_evento.strftime('%d/%m/%Y %H:%M') if backyard.data_evento else 'Não definida'])
    writer.writerow(['Status', backyard.status.value])
    writer.writerow(['Cidade', backyard.cidade or 'Não informada'])
    writer.writerow(['Estado', backyard.estado or 'Não informado'])
    writer.writerow(['Capacidade', str(backyard.capacidade)])
    writer.writerow([''])  # Linha em branco
    
    # Cabeçalho dos atletas
    writer.writerow(['# ATLETAS INSCRITOS'])
    writer.writerow([
        'Numero_Peito', 'Nome_Atleta', 'CPF', 'Email', 
        'Data_Nascimento', 'Cidade', 'Estado', 'Status_Inscricao', 'Data_Inscricao'
    ])
    
    # Dados dos atletas
    for inscricao, atleta in atletas_inscritos:
        writer.writerow([
            inscricao.numero_peito or '',
            atleta.nome,
            atleta.cpf or '',
            atleta.email or '',
            atleta.data_nascimento.strftime('%d/%m/%Y') if atleta.data_nascimento else '',
            atleta.cidade or '',
            atleta.estado or '',
            inscricao.status_inscricao,
            inscricao.data_inscricao.strftime('%d/%m/%Y %H:%M') if inscricao.data_inscricao else ''
        ])
    
    # Se existirem loops, adicionar dados dos loops
    if loops:
        writer.writerow([''])  # Linha em branco
        writer.writerow(['# HISTORICO DE LOOPS'])
        writer.writerow([
            'Numero_Loop', 'Status_Loop', 'Data_Inicio', 'Data_Fim', 
            'Tempo_Limite_Segundos', 'Distancia_KM', 'Total_Participantes'
        ])
        
        for loop in loops:
            participantes = len(atletas_loops.get(loop.id, []))
            writer.writerow([
                loop.numero_loop,
                loop.status.value,
                loop.data_inicio.strftime('%d/%m/%Y %H:%M') if loop.data_inicio else '',
                loop.data_fim.strftime('%d/%m/%Y %H:%M') if loop.data_fim else '',
                loop.tempo_limite or '',
                loop.distancia_km or '',
                participantes
            ])
    
    csv_data = output.getvalue()
    output.close()
    
    filename = f"backyard_{backyard.id}_{backyard.nome.replace(' ', '_')}_dados.csv"
    
    response = Response(csv_data, mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

def _export_json(backyard, atletas_inscritos, loops, atletas_loops):
    """Exportar dados em formato JSON"""
    
    # Dados da backyard
    backyard_data = {
        'id': backyard.id,
        'nome': backyard.nome,
        'organizacao': {
            'id': backyard.organizacao.id,
            'nome': backyard.organizacao.nome,
            'organizador': backyard.organizacao.user.nome if backyard.organizacao.user else None
        },
        'data_evento': backyard.data_evento.isoformat() if backyard.data_evento else None,
        'status': backyard.status.value,
        'cidade': backyard.cidade,
        'estado': backyard.estado,
        'capacidade': backyard.capacidade,
        'descricao': backyard.descricao,
        'data_criacao': backyard.data_criacao.isoformat() if backyard.data_criacao else None
    }
    
    # Dados dos atletas
    atletas_data = []
    for inscricao, atleta in atletas_inscritos:
        atleta_info = {
            'inscricao': {
                'numero_peito': inscricao.numero_peito,
                'status_inscricao': inscricao.status_inscricao,
                'data_inscricao': inscricao.data_inscricao.isoformat() if inscricao.data_inscricao else None
            },
            'atleta': {
                'id': atleta.id,
                'nome': atleta.nome,
                'cpf': atleta.cpf,
                'email': atleta.email,
                'data_nascimento': atleta.data_nascimento.isoformat() if atleta.data_nascimento else None,
                'cidade': atleta.cidade,
                'estado': atleta.estado,
                'sexo': atleta.sexo
            }
        }
        atletas_data.append(atleta_info)
    
    # Dados dos loops
    loops_data = []
    for loop in loops:
        participantes_loop = atletas_loops.get(loop.id, [])
        participantes_data = []
        
        for atleta_loop in participantes_loop:
            participante = {
                'atleta_id': atleta_loop.atleta_id,
                'status': atleta_loop.status.value,
                'tempo_inicio': atleta_loop.tempo_inicio.isoformat() if atleta_loop.tempo_inicio else None,
                'tempo_fim': atleta_loop.tempo_fim.isoformat() if atleta_loop.tempo_fim else None,
                'tempo_total_segundos': atleta_loop.tempo_total_segundos,
                'observacoes': atleta_loop.observacoes
            }
            participantes_data.append(participante)
        
        loop_info = {
            'id': loop.id,
            'numero_loop': loop.numero_loop,
            'status': loop.status.value,
            'data_inicio': loop.data_inicio.isoformat() if loop.data_inicio else None,
            'data_fim': loop.data_fim.isoformat() if loop.data_fim else None,
            'tempo_limite': loop.tempo_limite,
            'distancia_km': loop.distancia_km,
            'participantes': participantes_data
        }
        loops_data.append(loop_info)
    
    # Estrutura final
    export_data = {
        'backyard': backyard_data,
        'atletas_inscritos': atletas_data,
        'loops_historico': loops_data,
        'estatisticas': {
            'total_inscritos': len(atletas_inscritos),
            'total_loops': len(loops),
            'data_exportacao': datetime.now().isoformat()
        }
    }
    
    json_data = json.dumps(export_data, ensure_ascii=False, indent=2)
    filename = f"backyard_{backyard.id}_{backyard.nome.replace(' ', '_')}_dados.json"
    
    response = Response(json_data, mimetype='application/json')
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
