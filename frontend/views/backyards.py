"""
BTL Frontend - Backyards Views
Views para listagem e visualização de backyards públicas
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from models import db, Backyard, BackyardStatus, AtletaBackyard, Loop, LoopStatus, AtletaLoop, AtletaLoopStatus
from sqlalchemy import desc, asc

# Create blueprint
backyards_bp = Blueprint('backyards', __name__)

@backyards_bp.route('/')
def list_backyards():
    """Lista pública de backyards"""
    try:
        # Parâmetros de filtro
        status_filter = request.args.get('status', '')
        cidade_filter = request.args.get('cidade', '')
        search = request.args.get('search', '')
        
        # Base query - backyards públicas (ativas, em preparação e finalizadas)
        query = Backyard.query.filter(
            Backyard.status.in_([BackyardStatus.ATIVO, BackyardStatus.PREPARACAO, BackyardStatus.FINALIZADO])
        )
        
        # Aplicar filtros
        if status_filter:
            query = query.filter(Backyard.status == BackyardStatus(status_filter))
        
        if cidade_filter:
            query = query.filter(Backyard.cidade.ilike(f'%{cidade_filter}%'))
        
        if search:
            query = query.filter(
                Backyard.nome.ilike(f'%{search}%') |
                Backyard.cidade.ilike(f'%{search}%') |
                Backyard.estado.ilike(f'%{search}%')
            )
        
        # Ordenação: ativos primeiro, depois em preparação, depois finalizados
        if status_filter == 'FINALIZADO':
            # Para finalizados: mais recentes primeiro
            backyards = query.order_by(
                desc(Backyard.data_evento),
                desc(Backyard.data_criacao)
            ).all()
        else:
            # Para ativos e preparação: prioridade por status, depois por data
            backyards = query.order_by(
                (Backyard.status == BackyardStatus.ATIVO).desc(),
                (Backyard.status == BackyardStatus.PREPARACAO).desc(),
                asc(Backyard.data_evento),
                desc(Backyard.data_criacao)
            ).all()
        
        # Buscar cidades para filtro
        cidades = db.session.query(Backyard.cidade).distinct().filter(
            Backyard.cidade.isnot(None),
            Backyard.status.in_([BackyardStatus.ATIVO, BackyardStatus.PREPARACAO, BackyardStatus.FINALIZADO])
        ).order_by(Backyard.cidade).all()
        cidades = [c[0] for c in cidades if c[0]]
        
        return render_template('backyards/list.html', 
                             backyards=backyards,
                             cidades=cidades,
                             status_filter=status_filter,
                             cidade_filter=cidade_filter,
                             search=search)
    
    except Exception as e:
        print(f"Erro ao listar backyards: {e}")
        return render_template('backyards/list.html', 
                             backyards=[],
                             cidades=[],
                             status_filter='',
                             cidade_filter='',
                             search='')

@backyards_bp.route('/<int:id>')
def view_backyard(id):
    """Visualizar detalhes de uma backyard"""
    try:
        backyard = Backyard.query.get_or_404(id)
        
        # Verificar se o atleta está inscrito (se logado)
        is_inscrito = False
        inscricao = None
        if current_user.is_authenticated:
            inscricao = AtletaBackyard.query.filter_by(
                atleta_id=current_user.id,
                backyard_id=backyard.id
            ).first()
            is_inscrito = inscricao is not None
        
        # Calcular vagas restantes
        vagas_restantes = None
        total_inscritos = 0
        if backyard.capacidade:
            total_inscritos = AtletaBackyard.query.filter_by(backyard_id=backyard.id).count()
            vagas_restantes = backyard.capacidade - total_inscritos
        
        # Buscar loops da backyard (histórico)
        loops_historico = []
        if backyard.status in [BackyardStatus.ATIVO, BackyardStatus.FINALIZADO]:
            loops_historico = Loop.query.filter_by(backyard_id=backyard.id).order_by(
                desc(Loop.numero_loop)
            ).all()
        
        return render_template('backyards/view.html', 
                             backyard=backyard,
                             is_inscrito=is_inscrito,
                             inscricao=inscricao,
                             vagas_restantes=vagas_restantes,
                             total_inscritos=total_inscritos,
                             loops_historico=loops_historico)
    
    except Exception as e:
        print(f"Erro ao visualizar backyard: {e}")
        flash('Backyard não encontrada.', 'danger')
        return redirect(url_for('backyards.list_backyards'))

@backyards_bp.route('/<int:id>/inscrever', methods=['POST'])
@login_required
def inscrever(id):
    """Inscrever atleta em uma backyard"""
    try:
        backyard = Backyard.query.get_or_404(id)
        
        # Verificar se a backyard aceita inscrições
        if backyard.status not in [BackyardStatus.PREPARACAO]:
            flash('Esta backyard não está aceitando inscrições.', 'danger')
            return redirect(url_for('backyards.view_backyard', id=id))
        
        # Verificar se já está inscrito
        inscricao_existente = AtletaBackyard.query.filter_by(
            atleta_id=current_user.id,
            backyard_id=backyard.id
        ).first()
        
        if inscricao_existente:
            flash('Você já está inscrito nesta backyard.', 'warning')
            return redirect(url_for('backyards.view_backyard', id=id))
        
        # Verificar capacidade
        if backyard.capacidade:
            total_inscritos = AtletaBackyard.query.filter_by(backyard_id=backyard.id).count()
            if total_inscritos >= backyard.capacidade:
                flash('Esta backyard está com lotação esgotada.', 'danger')
                return redirect(url_for('backyards.view_backyard', id=id))
        
        # Criar inscrição
        inscricao = AtletaBackyard(
            atleta_id=current_user.id,
            backyard_id=backyard.id,
            data_inscricao=datetime.utcnow()
        )
        
        # Número de peito será atribuído posteriormente pelo administrador via backoffice
        
        db.session.add(inscricao)
        db.session.commit()
        
        flash('Inscrição realizada com sucesso! O número de peito será atribuído pelo organizador.', 'success')
        return redirect(url_for('backyards.view_backyard', id=id))
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro na inscrição: {e}")
        flash('Erro interno do servidor. Tente novamente.', 'danger')
        return redirect(url_for('backyards.view_backyard', id=id))

@backyards_bp.route('/<int:id>/cancelar-inscricao', methods=['POST'])
@login_required
def cancelar_inscricao(id):
    """Cancelar inscrição em uma backyard"""
    try:
        backyard = Backyard.query.get_or_404(id)
        
        # Buscar inscrição
        inscricao = AtletaBackyard.query.filter_by(
            atleta_id=current_user.id,
            backyard_id=backyard.id
        ).first()
        
        if not inscricao:
            flash('Você não está inscrito nesta backyard.', 'warning')
            return redirect(url_for('backyards.view_backyard', id=id))
        
        # Verificar se pode cancelar (apenas se não estiver ativa)
        if backyard.status == BackyardStatus.ATIVO:
            flash('Não é possível cancelar a inscrição em uma backyard ativa.', 'danger')
            return redirect(url_for('backyards.view_backyard', id=id))
        
        db.session.delete(inscricao)
        db.session.commit()
        
        flash('Inscrição cancelada com sucesso.', 'info')
        return redirect(url_for('backyards.view_backyard', id=id))
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao cancelar inscrição: {e}")
        flash('Erro interno do servidor. Tente novamente.', 'danger')
        return redirect(url_for('backyards.view_backyard', id=id))

@backyards_bp.route('/<int:id>/live')
def live_view(id):
    """Visualização em tempo real de uma backyard ativa"""
    try:
        backyard = Backyard.query.get_or_404(id)
        
        # Verificar se a backyard está ativa
        if backyard.status != BackyardStatus.ATIVO:
            flash('Esta backyard não está ativa no momento.', 'warning')
            return redirect(url_for('backyards.view_backyard', id=id))
        
        # Buscar loop atual (último loop ativo ou em preparação)
        loop_atual = Loop.query.filter_by(backyard_id=id).filter(
            Loop.status.in_([LoopStatus.ATIVO, LoopStatus.PREPARACAO])
        ).order_by(desc(Loop.numero_loop)).first()
        
        # Buscar todos os loops da backyard para histórico
        loops_historico = Loop.query.filter_by(backyard_id=id).order_by(
            desc(Loop.numero_loop)
        ).all()
        
        # Estatísticas gerais
        total_inscritos = AtletaBackyard.query.filter_by(backyard_id=id).count()
        
        # Se há loop atual, buscar atletas participantes
        atletas_ativos = []
        atletas_eliminados = []
        if loop_atual:
            # Buscar atletas ativos E concluídos do loop atual
            atletas_ativos_puro = loop_atual.get_atletas_ativos()
            atletas_concluidos = loop_atual.get_atletas_concluidos()
            
            # Combinar e ordenar: concluídos primeiro (por tempo), depois ativos
            atletas_ativos = []
            
            # Adicionar concluídos primeiro, ordenados por tempo
            atletas_concluidos_ordenados = sorted(atletas_concluidos, 
                                                key=lambda x: x.tempo_total_segundos or 0)
            atletas_ativos.extend(atletas_concluidos_ordenados)
            
            # Adicionar ativos depois
            atletas_ativos.extend(atletas_ativos_puro)
            
            # Buscar todos os atletas eliminados em qualquer loop
            atletas_eliminados = AtletaLoop.query.join(Loop).filter(
                Loop.backyard_id == id,
                AtletaLoop.status.in_([AtletaLoopStatus.ELIMINADO, AtletaLoopStatus.DNF, AtletaLoopStatus.DNS])
            ).all()
        
        # Estatísticas do loop atual
        atletas_concluidos_count = len(atletas_concluidos) if loop_atual else 0
        atletas_ativos_puro_count = len(atletas_ativos_puro) if loop_atual else 0
        
        stats = {
            'total_inscritos': total_inscritos,
            'atletas_ativos': atletas_ativos_puro_count,
            'atletas_concluidos': atletas_concluidos_count,
            'atletas_eliminados': len(atletas_eliminados),
            'loop_atual': loop_atual.numero_loop if loop_atual else 0,
            'total_loops': len(loops_historico)
        }
        
        return render_template('backyards/live.html',
                             backyard=backyard,
                             loop_atual=loop_atual,
                             loops_historico=loops_historico,
                             atletas_ativos=atletas_ativos,
                             atletas_eliminados=atletas_eliminados,
                             stats=stats)
    
    except Exception as e:
        print(f"Erro na visualização live: {e}")
        flash('Erro ao carregar visualização em tempo real.', 'danger')
        return redirect(url_for('backyards.view_backyard', id=id))

@backyards_bp.route('/<int:id>/loop/<int:loop_id>')
def view_loop(id, loop_id):
    """Visualizar detalhes específicos de um loop"""
    try:
        backyard = Backyard.query.get_or_404(id)
        loop = Loop.query.filter_by(id=loop_id, backyard_id=id).first_or_404()
        
        # Buscar todos os atletas deste loop
        atletas_loop = AtletaLoop.query.filter_by(loop_id=loop_id).join(
            AtletaLoop.atleta
        ).order_by(AtletaLoop.tempo_total_segundos.asc()).all()
        
        # Separar por status
        atletas_concluidos = [al for al in atletas_loop if al.status == AtletaLoopStatus.CONCLUIDO]
        atletas_eliminados = [al for al in atletas_loop if al.status in [AtletaLoopStatus.ELIMINADO, AtletaLoopStatus.DNF, AtletaLoopStatus.DNS]]
        atletas_ativos = [al for al in atletas_loop if al.status == AtletaLoopStatus.ATIVO]
        
        return render_template('backyards/loop_detail.html',
                             backyard=backyard,
                             loop=loop,
                             atletas_concluidos=atletas_concluidos,
                             atletas_eliminados=atletas_eliminados,
                             atletas_ativos=atletas_ativos)
    
    except Exception as e:
        print(f"Erro ao visualizar loop: {e}")
        flash('Loop não encontrado.', 'danger')
        return redirect(url_for('backyards.live_view', id=id))
