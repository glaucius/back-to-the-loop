from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
from models import db, Backyard, Loop, AtletaLoop, Atleta, AtletaBackyard, BackyardStatus, LoopStatus, AtletaLoopStatus
from functools import wraps
import json

# Create blueprint
loops_bp = Blueprint('loops', __name__)
def organizador_or_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.profile.nome not in ['Admin', 'Organizador']:
            flash('Access denied. Insufficient privileges.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

@loops_bp.route('/backyard/<int:backyard_id>')
@login_required
def manage_backyard(backyard_id):
    """Interface principal para gerenciar loops de um backyard"""
    backyard = Backyard.query.get_or_404(backyard_id)
    
    # Buscar loops ordenados por número
    loops = Loop.query.filter_by(backyard_id=backyard_id).order_by(Loop.numero_loop).all()
    
    # Loop atual (último ativo ou em preparação)
    loop_atual = Loop.query.filter_by(backyard_id=backyard_id).filter(
        Loop.status.in_([LoopStatus.ATIVO, LoopStatus.PREPARACAO])
    ).order_by(Loop.numero_loop.desc()).first()
    
    # Se não há loop ativo/preparação, pegar o último finalizado
    if not loop_atual and loops:
        loop_atual = loops[-1]
    
    # Estatísticas gerais do backyard
    total_atletas_inscritos = len(backyard.atletas)
    
    # Estatísticas do loop atual
    atletas_ativos = 0
    atletas_concluidos = 0
    atletas_eliminados = 0
    
    # Buscar atletas do loop atual com seus status
    atletas_loop_atual = []
    if loop_atual:
        # Contar por status
        atletas_ativos = AtletaLoop.query.filter_by(
            loop_id=loop_atual.id,
            status=AtletaLoopStatus.ATIVO
        ).count()
        
        atletas_concluidos = AtletaLoop.query.filter_by(
            loop_id=loop_atual.id,
            status=AtletaLoopStatus.CONCLUIDO
        ).count()
        
        atletas_eliminados = AtletaLoop.query.filter(
            AtletaLoop.loop_id == loop_atual.id,
            AtletaLoop.status.in_([AtletaLoopStatus.ELIMINADO, AtletaLoopStatus.DNF, AtletaLoopStatus.DNS])
        ).count()
        
        # Buscar todos os atletas do loop atual com informações detalhadas incluindo número de peito
        atletas_loop_atual = db.session.query(
            AtletaLoop, Atleta, AtletaBackyard
        ).join(Atleta, AtletaLoop.atleta_id == Atleta.id
        ).join(AtletaBackyard, 
               (AtletaBackyard.atleta_id == Atleta.id) & 
               (AtletaBackyard.backyard_id == backyard_id)
        ).filter(AtletaLoop.loop_id == loop_atual.id
        ).all()
        
        # Ordenar manualmente: primeiro os ativos, depois os concluídos, depois os eliminados
        def sort_key(item):
            atleta_loop, atleta, atleta_backyard = item
            status_priority = {
                AtletaLoopStatus.ATIVO: 1,
                AtletaLoopStatus.CONCLUIDO: 2,
                AtletaLoopStatus.ELIMINADO: 3,
                AtletaLoopStatus.DNF: 3,
                AtletaLoopStatus.DNS: 3
            }
            priority = status_priority.get(atleta_loop.status, 4)
            tempo = atleta_loop.tempo_total_segundos if atleta_loop.tempo_total_segundos else 999999
            return (priority, tempo, atleta.nome)
        
        atletas_loop_atual.sort(key=sort_key)
    
    # Loops anteriores para navegação (últimos 10, em ordem decrescente)
    loops_recentes = (loops[-10:] if len(loops) > 10 else loops)
    loops_recentes = list(reversed(loops_recentes))  # Ordem decrescente (mais recente primeiro)
    total_loops = len(loops)
    
    # Estatísticas históricas
    total_loops_finalizados = len([l for l in loops if l.status == LoopStatus.FINALIZADO])
    ultimo_loop_finalizado = None
    if total_loops_finalizados > 0:
        ultimo_loop_finalizado = max([l for l in loops if l.status == LoopStatus.FINALIZADO], 
                                   key=lambda x: x.numero_loop)
    
    # Estatísticas dos números de peito
    total_inscricoes = AtletaBackyard.query.filter_by(backyard_id=backyard_id).count()
    inscricoes_com_numero = AtletaBackyard.query.filter_by(backyard_id=backyard_id).filter(AtletaBackyard.numero_peito.isnot(None)).count()
    inscricoes_sem_numero = total_inscricoes - inscricoes_com_numero
    
    return render_template('loops/manage_backyard.html',
                         backyard=backyard,
                         loops=loops,
                         loops_recentes=loops_recentes,
                         loop_atual=loop_atual,
                         atletas_loop_atual=atletas_loop_atual,
                         total_loops=total_loops,
                         total_atletas_inscritos=total_atletas_inscritos,
                         atletas_ativos=atletas_ativos,
                         atletas_concluidos=atletas_concluidos,
                         atletas_eliminados=atletas_eliminados,
                         total_loops_finalizados=total_loops_finalizados,
                         ultimo_loop_finalizado=ultimo_loop_finalizado,
                         total_inscricoes=total_inscricoes,
                         inscricoes_com_numero=inscricoes_com_numero,
                         inscricoes_sem_numero=inscricoes_sem_numero)

@loops_bp.route('/backyard/<int:backyard_id>/loop/<int:loop_number>')
@login_required
def view_specific_loop(backyard_id, loop_number):
    """Visualizar um loop específico"""
    backyard = Backyard.query.get_or_404(backyard_id)
    
    # Buscar o loop específico
    loop_especifico = Loop.query.filter_by(
        backyard_id=backyard_id, 
        numero_loop=loop_number
    ).first_or_404()
    
    # Buscar atletas deste loop
    atletas_loop = db.session.query(
        AtletaLoop, Atleta
    ).join(Atleta, AtletaLoop.atleta_id == Atleta.id
    ).filter(AtletaLoop.loop_id == loop_especifico.id
    ).order_by(AtletaLoop.tempo_total_segundos.asc()).all()
    
    # Buscar todos os loops para navegação
    loops = Loop.query.filter_by(backyard_id=backyard_id).order_by(Loop.numero_loop).all()
    
    # Loop anterior e próximo para navegação
    loop_anterior = None
    loop_proximo = None
    
    for i, current_loop in enumerate(loops):
        if current_loop.numero_loop == loop_number:
            if i > 0:
                loop_anterior = loops[i-1]
            if i < len(loops) - 1:
                loop_proximo = loops[i+1]
            break
    
    return render_template('loops/view_specific_loop.html',
                         backyard=backyard,
                         loop=loop_especifico,
                         atletas_loop=atletas_loop,
                         loops=loops,
                         loop_anterior=loop_anterior,
                         loop_proximo=loop_proximo,
                         total_loops=len(loops))

@loops_bp.route('/backyard/<int:backyard_id>/start', methods=['POST'])
@login_required
def start_backyard(backyard_id):
    """Iniciar evento - criar primeiro loop"""
    backyard = Backyard.query.get_or_404(backyard_id)
    
    if backyard.status != BackyardStatus.PREPARACAO:
        flash('Evento já foi iniciado ou finalizado!', 'warning')
        return redirect(url_for('loops.manage_backyard', backyard_id=backyard_id))
    
    # Verificar se há atletas inscritos
    if not backyard.atletas:
        flash('Não há atletas inscritos neste evento!', 'error')
        return redirect(url_for('loops.manage_backyard', backyard_id=backyard_id))
    
    try:
        # Atualizar status do backyard
        backyard.status = BackyardStatus.ATIVO
        
        # Criar primeiro loop
        primeiro_loop = Loop(
            backyard_id=backyard_id,
            numero_loop=1,
            status=LoopStatus.PREPARACAO,
            data_inicio=datetime.utcnow(),
            tempo_limite=3600,  # 1 hora
            distancia_km=6.7
        )
        db.session.add(primeiro_loop)
        db.session.flush()  # Para obter o ID do loop
        
        # Adicionar todos os atletas ao primeiro loop
        for atleta in backyard.atletas:
            atleta_loop = AtletaLoop(
                atleta_id=atleta.id,
                loop_id=primeiro_loop.id,
                status=AtletaLoopStatus.ATIVO,
                tempo_inicio=datetime.utcnow()
            )
            db.session.add(atleta_loop)
        
        db.session.commit()
        flash(f'Evento iniciado! Loop 1 criado com {len(backyard.atletas)} atletas.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao iniciar evento: {str(e)}', 'error')
    
    return redirect(url_for('loops.manage_backyard', backyard_id=backyard_id))

@loops_bp.route('/loop/<int:loop_id>/manage')
@login_required
def manage_loop(loop_id):
    """Interface para gerenciar atletas de um loop específico"""
    loop = Loop.query.get_or_404(loop_id)
    
    # Buscar atletas deste loop com informações completas
    atletas_loop = db.session.query(AtletaLoop, Atleta).join(
        Atleta, AtletaLoop.atleta_id == Atleta.id
    ).filter(AtletaLoop.loop_id == loop_id).order_by(Atleta.nome).all()
    
    # Estatísticas do loop
    stats = {
        'total': len(atletas_loop),
        'ativos': len([al for al, _ in atletas_loop if al.status == AtletaLoopStatus.ATIVO]),
        'concluidos': len([al for al, _ in atletas_loop if al.status == AtletaLoopStatus.CONCLUIDO]),
        'eliminados': len([al for al, _ in atletas_loop if al.status in [AtletaLoopStatus.ELIMINADO, AtletaLoopStatus.DNF, AtletaLoopStatus.DNS]])
    }
    
    return render_template('loops/manage_loop.html',
                         loop=loop,
                         atletas_loop=atletas_loop,
                         stats=stats)

@loops_bp.route('/loop/<int:loop_id>/start', methods=['POST'])
@login_required
def start_loop(loop_id):
    """Iniciar um loop específico"""
    loop = Loop.query.get_or_404(loop_id)
    
    if loop.status != LoopStatus.PREPARACAO:
        return jsonify({'success': False, 'message': 'Loop já foi iniciado!'})
    
    try:
        loop.status = LoopStatus.ATIVO
        loop.data_inicio = datetime.utcnow()
        
        # Atualizar tempo de início para todos os atletas ativos
        AtletaLoop.query.filter_by(
            loop_id=loop_id,
            status=AtletaLoopStatus.ATIVO
        ).update({'tempo_inicio': datetime.utcnow()})
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'Loop {loop.numero_loop} iniciado!'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

@loops_bp.route('/atleta_loop/<int:atleta_loop_id>/finish', methods=['POST'])
@login_required
def finish_atleta_loop(atleta_loop_id):
    """Marcar atleta como concluído no loop"""
    atleta_loop = AtletaLoop.query.get_or_404(atleta_loop_id)
    
    # Obter dados do formulário
    tempo_fim_str = request.form.get('tempo_fim')
    observacoes = request.form.get('observacoes', '')
    
    try:
        # Converter tempo (formato HH:MM:SS)
        if tempo_fim_str:
            tempo_fim = datetime.strptime(tempo_fim_str, '%H:%M:%S').time()
            # Combinar com a data do início do loop
            data_inicio = atleta_loop.tempo_inicio or atleta_loop.loop.data_inicio
            tempo_fim_completo = datetime.combine(data_inicio.date(), tempo_fim)
            
            # Calcular tempo total em segundos
            tempo_total = (tempo_fim_completo - atleta_loop.tempo_inicio).total_seconds()
            
            atleta_loop.tempo_fim = tempo_fim_completo
            atleta_loop.tempo_total_segundos = int(tempo_total)
        else:
            atleta_loop.tempo_fim = datetime.utcnow()
            if atleta_loop.tempo_inicio:
                tempo_total = (atleta_loop.tempo_fim - atleta_loop.tempo_inicio).total_seconds()
                atleta_loop.tempo_total_segundos = int(tempo_total)
        
        atleta_loop.status = AtletaLoopStatus.CONCLUIDO
        atleta_loop.observacoes = observacoes
        atleta_loop.atualizado_em = datetime.utcnow()
        
        db.session.commit()
        flash('Atleta marcado como concluído!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao marcar conclusão: {str(e)}', 'error')
    
    return redirect(url_for('loops.manage_loop', loop_id=atleta_loop.loop_id))

@loops_bp.route('/atleta_loop/<int:atleta_loop_id>/change_status', methods=['POST'])
@login_required
def change_atleta_status(atleta_loop_id):
    """Alterar status de um atleta no loop (desclassificação, correção)"""
    atleta_loop = AtletaLoop.query.get_or_404(atleta_loop_id)
    
    novo_status = request.form.get('status')
    observacoes = request.form.get('observacoes', '')
    
    try:
        # Validar novo status
        if novo_status in [s.value for s in AtletaLoopStatus]:
            atleta_loop.status = AtletaLoopStatus(novo_status)
            atleta_loop.observacoes = observacoes
            atleta_loop.atualizado_em = datetime.utcnow()
            
            # Se mudou para eliminado/dnf/dns, limpar tempos se necessário
            if atleta_loop.status in [AtletaLoopStatus.ELIMINADO, AtletaLoopStatus.DNF, AtletaLoopStatus.DNS]:
                if not atleta_loop.tempo_fim:
                    atleta_loop.tempo_fim = datetime.utcnow()
            
            db.session.commit()
            flash(f'Status alterado para {atleta_loop.status.value}!', 'success')
        else:
            flash('Status inválido!', 'error')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao alterar status: {str(e)}', 'error')
    
    return redirect(url_for('loops.manage_loop', loop_id=atleta_loop.loop_id))

@loops_bp.route('/loop/<int:loop_id>/create_next', methods=['POST'])
@login_required
def create_next_loop(loop_id):
    """Criar próximo loop com atletas que concluíram o atual"""
    loop_atual = Loop.query.get_or_404(loop_id)
    
    if loop_atual.status != LoopStatus.ATIVO:
        return jsonify({'success': False, 'message': 'Loop atual deve estar ativo!'})
    
    # Buscar atletas que concluíram o loop atual
    atletas_qualificados = AtletaLoop.query.filter_by(
        loop_id=loop_id,
        status=AtletaLoopStatus.CONCLUIDO
    ).all()
    
    # REGRA DO BACKYARD ULTRA: Nunca finalizar evento aqui!
    # Mesmo se apenas 1 atleta se qualificou, ele deve fazer um loop solo
    # O evento só termina quando um atleta COMPLETA um loop sozinho
    
    if len(atletas_qualificados) == 0:
        # Se nenhum atleta se qualificou, finalizar evento (todos foram eliminados)
        backyard = loop_atual.backyard
        backyard.status = BackyardStatus.FINALIZADO
        loop_atual.status = LoopStatus.FINALIZADO
        loop_atual.data_fim = datetime.utcnow()
        
        # REGRA DE NEGÓCIO: Atletas que ainda estavam ATIVOS quando o evento foi finalizado devem virar DNF
        atletas_ativos_nao_concluidos = AtletaLoop.query.filter_by(
            loop_id=loop_id,
            status=AtletaLoopStatus.ATIVO
        ).all()
        
        for atleta_loop in atletas_ativos_nao_concluidos:
            atleta_loop.status = AtletaLoopStatus.DNF
            atleta_loop.observacoes = "DNF - Loop finalizado antes da conclusão"
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Evento finalizado! Nenhum atleta se qualificou.',
            'event_finished': True
        })
    
    try:
        # Finalizar loop atual
        loop_atual.status = LoopStatus.FINALIZADO
        loop_atual.data_fim = datetime.utcnow()
        
        # REGRA DE NEGÓCIO: Atletas que ainda estavam ATIVOS quando o loop foi finalizado devem virar DNF
        atletas_ativos_nao_concluidos = AtletaLoop.query.filter_by(
            loop_id=loop_id,
            status=AtletaLoopStatus.ATIVO
        ).all()
        
        for atleta_loop in atletas_ativos_nao_concluidos:
            atleta_loop.status = AtletaLoopStatus.DNF
            atleta_loop.observacoes = "DNF - Loop finalizado antes da conclusão"
        
        # Criar próximo loop
        proximo_loop = Loop(
            backyard_id=loop_atual.backyard_id,
            numero_loop=loop_atual.numero_loop + 1,
            status=LoopStatus.PREPARACAO,
            tempo_limite=3600,
            distancia_km=6.7
        )
        db.session.add(proximo_loop)
        db.session.flush()
        
        # Adicionar atletas qualificados ao próximo loop
        for atleta_loop in atletas_qualificados:
            novo_atleta_loop = AtletaLoop(
                atleta_id=atleta_loop.atleta_id,
                loop_id=proximo_loop.id,
                status=AtletaLoopStatus.ATIVO
            )
            db.session.add(novo_atleta_loop)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Loop {proximo_loop.numero_loop} criado com {len(atletas_qualificados)} atletas!',
            'new_loop_id': proximo_loop.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

@loops_bp.route('/atleta_loop/<int:atleta_loop_id>/edit_time', methods=['POST'])
@login_required
def edit_time(atleta_loop_id):
    """Corrigir tempo de um atleta"""
    atleta_loop = AtletaLoop.query.get_or_404(atleta_loop_id)
    
    novo_tempo = request.form.get('tempo_total')
    observacoes = request.form.get('observacoes', '')
    
    try:
        # Converter tempo (formato HH:MM:SS ou segundos)
        if ':' in novo_tempo:
            # Formato HH:MM:SS
            time_parts = novo_tempo.split(':')
            total_seconds = int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + int(time_parts[2])
        else:
            # Formato segundos
            total_seconds = int(novo_tempo)
        
        atleta_loop.tempo_total_segundos = total_seconds
        
        # Recalcular tempo_fim baseado no novo tempo total
        if atleta_loop.tempo_inicio:
            atleta_loop.tempo_fim = atleta_loop.tempo_inicio + timedelta(seconds=total_seconds)
        
        atleta_loop.observacoes = observacoes
        atleta_loop.atualizado_em = datetime.utcnow()
        
        db.session.commit()
        flash('Tempo corrigido com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao corrigir tempo: {str(e)}', 'error')
    
    return redirect(url_for('loops.manage_loop', loop_id=atleta_loop.loop_id))

@loops_bp.route('/atleta/<int:atleta_loop_id>/concluir', methods=['POST'])
@login_required
def marcar_atleta_concluido(atleta_loop_id):
    """Endpoint AJAX para marcar atleta como concluído rapidamente"""
    print(f"DEBUG: marcar_atleta_concluido chamado com ID: {atleta_loop_id}")
    try:
        atleta_loop = AtletaLoop.query.get_or_404(atleta_loop_id)
        print(f"DEBUG: Atleta encontrado: {atleta_loop.id}, Status: {atleta_loop.status}")
        
        # Calcular tempo real baseado no início do loop
        from datetime import datetime
        tempo_atual = datetime.now()
        loop = atleta_loop.loop
        
        # Verificar se o loop está ativo
        if loop.status != LoopStatus.ATIVO:
            return jsonify({'success': False, 'message': 'Loop não está ativo'}), 400
        
        # Verificar se o atleta está ativo
        if atleta_loop.status != AtletaLoopStatus.ATIVO:
            return jsonify({'success': False, 'message': 'Atleta não está ativo neste loop'}), 400
        
        # Calcular tempo total baseado no início do loop
        if loop.data_inicio:
            tempo_decorrido = tempo_atual - loop.data_inicio
            tempo_total_segundos = int(tempo_decorrido.total_seconds())
            print(f"DEBUG: Usando data_inicio do loop: {loop.data_inicio}")
        else:
            # Se não há data de início, usar tempo desde a criação do loop
            tempo_decorrido = tempo_atual - loop.criado_em
            tempo_total_segundos = int(tempo_decorrido.total_seconds())
            print(f"DEBUG: Usando criado_em do loop: {loop.criado_em}")
        
        print(f"DEBUG: Tempo atual: {tempo_atual}")
        print(f"DEBUG: Tempo decorrido: {tempo_decorrido}")
        print(f"DEBUG: Tempo total em segundos: {tempo_total_segundos}")
        
        atleta_loop.status = AtletaLoopStatus.CONCLUIDO
        atleta_loop.tempo_fim = tempo_atual
        atleta_loop.tempo_total_segundos = tempo_total_segundos
        
        db.session.commit()
        print("DEBUG: Commit realizado com sucesso")
        
        # REGRA DO BACKYARD ULTRA: Verificar se este é um LOOP SOLO COMPLETADO
        # Um loop solo é quando apenas 1 atleta INICIOU o loop (não apenas completou)
        
        # Contar quantos atletas participaram deste loop (todos os status)
        total_atletas_no_loop = AtletaLoop.query.filter_by(loop_id=loop.id).count()
        
        print(f"DEBUG: Total de atletas que participaram do loop {loop.numero_loop}: {total_atletas_no_loop}")
        
        # Se apenas 1 atleta participou do loop E ele completou, temos um vencedor!
        if total_atletas_no_loop == 1:
            atletas_concluidos_no_loop = AtletaLoop.query.filter_by(
                loop_id=loop.id,
                status=AtletaLoopStatus.CONCLUIDO
            ).count()
            
            print(f"DEBUG: Atletas concluídos no loop solo: {atletas_concluidos_no_loop}")
            
            # Se o único atleta do loop completou, ele é o campeão!
            if atletas_concluidos_no_loop == 1:
                backyard = loop.backyard
                backyard.status = BackyardStatus.FINALIZADO
                loop.status = LoopStatus.FINALIZADO
                loop.data_fim = datetime.now()
                
                # Buscar o vencedor
                vencedor_atleta_loop = AtletaLoop.query.filter_by(
                    loop_id=loop.id,
                    status=AtletaLoopStatus.CONCLUIDO
                ).first()
                vencedor = Atleta.query.get(vencedor_atleta_loop.atleta_id)
                
                db.session.commit()
                print(f"DEBUG: EVENTO FINALIZADO! Vencedor: {vencedor.nome} completou loop solo #{loop.numero_loop}")
                
                # Retornar dados atualizados
                tempo_formatado = atleta_loop.get_tempo_formatado()
                
                return jsonify({
                    'success': True, 
                    'message': f'🏆 PARABÉNS! {vencedor.nome} é o CAMPEÃO! Completou o loop #{loop.numero_loop} sozinho!',
                    'tempo_formatado': tempo_formatado,
                    'status': 'CONCLUIDO',
                    'event_finished': True,
                    'winner': vencedor.nome
                })
        
        # Retornar dados atualizados (caso normal)
        tempo_formatado = atleta_loop.get_tempo_formatado()
        print(f"DEBUG: Tempo formatado: {tempo_formatado}")
        
        return jsonify({
            'success': True, 
            'message': 'Atleta marcado como concluído',
            'tempo_formatado': tempo_formatado,
            'status': 'CONCLUIDO'
        })
        
    except Exception as e:
        print(f"DEBUG: Erro: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@loops_bp.route('/atleta/<int:atleta_loop_id>/eliminar', methods=['POST'])
@login_required
@organizador_or_admin_required  
def marcar_atleta_eliminado(atleta_loop_id):
    """Endpoint AJAX para marcar atleta como eliminado rapidamente"""
    try:
        atleta_loop = AtletaLoop.query.get_or_404(atleta_loop_id)
        loop = atleta_loop.loop
        backyard = loop.backyard
        
        # Verificar permissões
        if current_user.profile.nome == 'Organizador' and backyard.organizador != current_user.organizacao_id:
            return jsonify({'success': False, 'message': 'Sem permissão'}), 403
        
        # Verificar se o loop está ativo
        if loop.status != LoopStatus.ATIVO:
            return jsonify({'success': False, 'message': 'Loop não está ativo'}), 400
        
        # Verificar se o atleta está ativo
        if atleta_loop.status != AtletaLoopStatus.ATIVO:
            return jsonify({'success': False, 'message': 'Atleta não está ativo neste loop'}), 400
        
        # Marcar como eliminado
        atleta_loop.status = AtletaLoopStatus.ELIMINADO
        atleta_loop.tempo_fim = datetime.now()
        atleta_loop.tempo_total_segundos = None  # Não completou
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Atleta marcado como eliminado',
            'status': 'ELIMINADO'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
