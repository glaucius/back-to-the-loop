"""
BTL Frontend - Home Views
Views para a página inicial e navegação principal
"""

from flask import Blueprint, render_template, request
from flask_login import current_user
from models import Backyard, BackyardStatus
from sqlalchemy import desc

# Create blueprint
home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def index():
    """Página inicial do frontend"""
    try:
        # Buscar backyards recentes e ativas para exibir na home
        backyards_recentes = Backyard.query.filter(
            Backyard.status.in_([BackyardStatus.ATIVO, BackyardStatus.PREPARACAO])
        ).order_by(desc(Backyard.data_criacao)).limit(6).all()
        
        # Estatísticas para exibir na home
        stats = {
            'total_backyards': Backyard.query.count(),
            'backyards_ativas': Backyard.query.filter_by(status=BackyardStatus.ATIVO).count(),
            'backyards_proximas': Backyard.query.filter_by(status=BackyardStatus.PREPARACAO).count()
        }
        
        return render_template('home/index.html', 
                             backyards=backyards_recentes,
                             stats=stats)
    
    except Exception as e:
        print(f"Erro na página inicial: {e}")
        return render_template('home/index.html', 
                             backyards=[],
                             stats={'total_backyards': 0, 'backyards_ativas': 0, 'backyards_proximas': 0})

@home_bp.route('/about')
def about():
    """Página sobre"""
    return render_template('home/about.html')

@home_bp.route('/contact')
def contact():
    """Página de contato"""
    return render_template('home/contact.html')


