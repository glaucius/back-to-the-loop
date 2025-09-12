"""
Scheduler para tarefas automáticas do BTL
Inclui verificação de tempo limite dos loops
"""

import threading
import time
from datetime import datetime
from models import db, Loop, LoopStatus
from views.loops import eliminar_atletas_por_tempo

class BTLScheduler:
    """Classe para gerenciar tarefas agendadas do BTL"""
    
    def __init__(self, app=None):
        self.app = app
        self.running = False
        self.thread = None
        
    def init_app(self, app):
        """Inicializa o scheduler com a aplicação Flask"""
        self.app = app
        
    def start(self):
        """Inicia o scheduler em thread separada"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        print("BTL Scheduler iniciado!")
        
    def stop(self):
        """Para o scheduler"""
        self.running = False
        if self.thread:
            self.thread.join()
        print("BTL Scheduler parado!")
        
    def _run_scheduler(self):
        """Loop principal do scheduler"""
        while self.running:
            try:
                with self.app.app_context():
                    self._check_time_limits()
                    
                # Verificar a cada 30 segundos
                time.sleep(30)
                
            except Exception as e:
                print(f"ERRO no scheduler: {str(e)}")
                time.sleep(60)  # Esperar mais tempo em caso de erro
                
    def _check_time_limits(self):
        """Verificar tempo limite de todos os loops ativos"""
        try:
            # Buscar todos os loops ativos
            loops_ativos = Loop.query.filter_by(status=LoopStatus.ATIVO).all()
            
            total_eliminados = 0
            
            for loop in loops_ativos:
                if not loop.data_inicio:
                    continue
                    
                # Verificar se excedeu tempo limite
                tempo_atual = datetime.utcnow()
                tempo_decorrido = tempo_atual - loop.data_inicio
                tempo_total_segundos = int(tempo_decorrido.total_seconds())
                
                # Se excedeu o tempo limite, eliminar atletas ativos
                if tempo_total_segundos > loop.tempo_limite:
                    eliminados = eliminar_atletas_por_tempo(loop.id)
                    total_eliminados += eliminados
                    
                    if eliminados > 0:
                        print(f"SCHEDULER: {eliminados} atletas eliminados automaticamente no loop {loop.id} "
                              f"(tempo: {tempo_total_segundos}s > {loop.tempo_limite}s)")
            
            # Log apenas se houver eliminações
            if total_eliminados > 0:
                print(f"SCHEDULER: Total de {total_eliminados} atletas eliminados por tempo limite")
                
        except Exception as e:
            print(f"ERRO ao verificar tempo limite: {str(e)}")

# Instância global do scheduler
scheduler = BTLScheduler()

def init_scheduler(app):
    """Função para inicializar o scheduler com a aplicação"""
    scheduler.init_app(app)
    scheduler.start()
    return scheduler

def stop_scheduler():
    """Função para parar o scheduler"""
    scheduler.stop()
