from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Organizacao, Backend_Users
from functools import wraps

organizacoes_bp = Blueprint('organizacoes', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@organizacoes_bp.route('/')
@login_required
@admin_required
def list_organizacoes():
    page = request.args.get('page', 1, type=int)
    organizacoes = Organizacao.query.paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('organizacoes/list.html', organizacoes=organizacoes)

@organizacoes_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_organizacao():
    if request.method == 'POST':
        nome = request.form['nome']
        organizador = request.form['organizador']
        
        organizacao = Organizacao(
            nome=nome,
            organizador=organizador
        )
        
        try:
            db.session.add(organizacao)
            db.session.commit()
            flash(f'Organization {nome} created successfully!', 'success')
            return redirect(url_for('organizacoes.list_organizacoes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating organization: {str(e)}', 'danger')
    
    # Get users with Organizador profile
    organizadores = Backend_Users.query.join(Backend_Users.profile).filter_by(nome='Organizador').all()
    return render_template('organizacoes/create.html', organizadores=organizadores)

@organizacoes_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_organizacao(id):
    organizacao = Organizacao.query.get_or_404(id)
    
    if request.method == 'POST':
        organizacao.nome = request.form['nome']
        organizacao.organizador = request.form['organizador']
        
        try:
            db.session.commit()
            flash(f'Organization {organizacao.nome} updated successfully!', 'success')
            return redirect(url_for('organizacoes.list_organizacoes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating organization: {str(e)}', 'danger')
    
    # Get users with Organizador profile
    organizadores = Backend_Users.query.join(Backend_Users.profile).filter_by(nome='Organizador').all()
    return render_template('organizacoes/edit.html', organizacao=organizacao, organizadores=organizadores)

@organizacoes_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_organizacao(id):
    organizacao = Organizacao.query.get_or_404(id)
    
    # Check if organization has backyards
    if organizacao.backyards:
        flash(f'Cannot delete organization {organizacao.nome}. It has backyards associated!', 'danger')
        return redirect(url_for('organizacoes.list_organizacoes'))
    
    try:
        db.session.delete(organizacao)
        db.session.commit()
        flash(f'Organization {organizacao.nome} deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting organization: {str(e)}', 'danger')
    
    return redirect(url_for('organizacoes.list_organizacoes'))
