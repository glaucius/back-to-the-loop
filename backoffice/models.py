from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from enum import Enum

# Initialize extension
db = SQLAlchemy()

# Enums for status
class BackyardStatus(Enum):
    PREPARACAO = "PREPARACAO"
    ATIVO = "ATIVO"
    PAUSADO = "PAUSADO"
    FINALIZADO = "FINALIZADO"

class LoopStatus(Enum):
    PREPARACAO = "PREPARACAO"
    ATIVO = "ATIVO"
    FINALIZADO = "FINALIZADO"

class AtletaLoopStatus(Enum):
    ATIVO = "ATIVO"
    CONCLUIDO = "CONCLUIDO"
    ELIMINADO = "ELIMINADO"
    DNF = "DNF"  # Did Not Finish
    DNS = "DNS"  # Did Not Start

class Profile(db.Model):
    __tablename__ = 'profiles'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(255), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_ultima_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('Backend_Users', backref='profile', lazy=True)
    
    def __repr__(self):
        return f'<Profile {self.nome}>'

class Backend_Users(UserMixin, db.Model):
    __tablename__ = 'backend_users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id'), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_ultima_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organizacoes = db.relationship('Organizacao', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<Backend_Users {self.email}>'
    
    def is_admin(self):
        return self.profile.nome == 'Admin'
    
    def is_organizador(self):
        return self.profile.nome == 'Organizador'

class Organizacao(db.Model):
    __tablename__ = 'organizacoes'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(255), nullable=False)
    organizador = db.Column(db.Integer, db.ForeignKey('backend_users.id'), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_ultima_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    backyards = db.relationship('Backyard', backref='organizacao', lazy=True)
    
    def __repr__(self):
        return f'<Organizacao {self.nome}>'

class Backyard(db.Model):
    __tablename__ = 'backyards'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(255), nullable=False)
    organizador = db.Column(db.Integer, db.ForeignKey('organizacoes.id'), nullable=False)
    descricao = db.Column(db.Text)
    endereco = db.Column(db.String(255))
    cidade = db.Column(db.String(255))
    estado = db.Column(db.String(255))
    pais = db.Column(db.String(255))
    profile_picture_path = db.Column(db.String(255))  # Foto principal da backyard
    logo_path = db.Column(db.String(255))  # Logo da backyard
    data_evento = db.Column(db.DateTime)  # Data e hora do início do evento
    status = db.Column(db.Enum(BackyardStatus), nullable=False, default=BackyardStatus.PREPARACAO)
    
    # Configuração de números de peito
    capacidade = db.Column(db.Integer, nullable=False, default=100)  # Quantidade máxima de atletas
    numero_inicial = db.Column(db.Integer, nullable=False, default=1)  # Primeiro número de peito disponível
    
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_ultima_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    atletas = db.relationship('Atleta', secondary='atleta_backyard', back_populates='backyards')
    
    @property
    def numero_final(self):
        """Calcula o número final baseado no inicial + capacidade - 1"""
        return self.numero_inicial + self.capacidade - 1
    
    def get_proximo_numero_peito(self):
        """Retorna o próximo número de peito disponível"""
        # Buscar o maior número já atribuído
        ultimo_numero = db.session.query(db.func.max(AtletaBackyard.numero_peito)).filter_by(backyard_id=self.id).scalar()
        
        if ultimo_numero is None:
            return self.numero_inicial
        
        proximo = ultimo_numero + 1
        if proximo > self.numero_final:
            return None  # Capacidade esgotada
        
        return proximo
    
    def gerar_numeros_peito(self):
        """Gera números de peito para todos os atletas inscritos que não têm número"""
        inscricoes_sem_numero = AtletaBackyard.query.filter_by(
            backyard_id=self.id, 
            numero_peito=None
        ).order_by(AtletaBackyard.data_inscricao).all()
        
        numero_atual = self.numero_inicial
        numeros_atribuidos = 0
        
        for inscricao in inscricoes_sem_numero:
            if numero_atual <= self.numero_final:
                inscricao.numero_peito = numero_atual
                numero_atual += 1
                numeros_atribuidos += 1
            else:
                break  # Capacidade esgotada
        
        if numeros_atribuidos > 0:
            db.session.commit()
        
        return numeros_atribuidos
    
    def __repr__(self):
        return f'<Backyard {self.nome}>'

class Atleta(UserMixin, db.Model):
    __tablename__ = 'atletas'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(255), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    data_nascimento = db.Column(db.Date)
    sexo = db.Column(db.String(50))  # masculino, feminino, nao_binario, prefiro_nao_informar
    imagem_perfil = db.Column(db.String(255))
    endereco = db.Column(db.String(255))
    cidade = db.Column(db.String(255))
    estado = db.Column(db.String(255))
    pais = db.Column(db.String(255))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    backyards = db.relationship('Backyard', secondary='atleta_backyard', back_populates='atletas')
    
    def __repr__(self):
        return f'<Atleta {self.nome}>'

# Tabela de associação Many-to-Many entre Atleta e Backyard
class AtletaBackyard(db.Model):
    __tablename__ = 'atleta_backyard'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    atleta_id = db.Column(db.Integer, db.ForeignKey('atletas.id'), nullable=False)
    backyard_id = db.Column(db.Integer, db.ForeignKey('backyards.id'), nullable=False)
    numero_peito = db.Column(db.Integer, nullable=True)  # Número do peito/bib do atleta nesta prova
    data_inscricao = db.Column(db.DateTime, default=datetime.utcnow)
    status_inscricao = db.Column(db.String(50), default='inscrito')  # inscrito, cancelado, finalizado
    posicao_final = db.Column(db.Integer)  # Posição final na corrida (1 = vencedor, 2 = segundo, etc.)
    voltas_completadas = db.Column(db.Integer, default=0)  # Número de voltas completadas
    tempo_total = db.Column(db.Time)  # Tempo total de corrida
    
    # Relationships
    atleta = db.relationship('Atleta', backref='inscricoes')
    backyard = db.relationship('Backyard', backref='inscricoes')
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('backyard_id', 'numero_peito', name='unique_numero_peito_por_backyard'),
        db.UniqueConstraint('atleta_id', 'backyard_id', name='unique_atleta_por_backyard'),
    )
    
    def __repr__(self):
        numero = f"#{self.numero_peito}" if self.numero_peito else "sem número"
        return f'<AtletaBackyard {self.atleta_id}-{self.backyard_id} ({numero})>'

class Loop(db.Model):
    __tablename__ = 'loops'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    backyard_id = db.Column(db.Integer, db.ForeignKey('backyards.id'), nullable=False)
    numero_loop = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum(LoopStatus), nullable=False, default=LoopStatus.PREPARACAO)
    data_inicio = db.Column(db.DateTime)
    data_fim = db.Column(db.DateTime)
    tempo_limite = db.Column(db.Integer, nullable=False)
    distancia_km = db.Column(db.Float, nullable=False)
    criado_em = db.Column(db.DateTime)
    
    # Relationships
    backyard = db.relationship('Backyard', backref='loops')
    atletas = db.relationship('AtletaLoop', backref='loop', lazy=True)
    

    def get_atletas_ativos(self):
        """Retorna lista de atletas ativos neste loop"""
        return [atleta_loop for atleta_loop in self.atletas if atleta_loop.status == AtletaLoopStatus.ATIVO]
    
    def get_atletas_concluidos(self):
        """Retorna lista de atletas que concluíram este loop"""
        return [atleta_loop for atleta_loop in self.atletas if atleta_loop.status == AtletaLoopStatus.CONCLUIDO]
    
    def get_atletas_eliminados(self):
        """Retorna lista de atletas eliminados neste loop"""
        return [atleta_loop for atleta_loop in self.atletas if atleta_loop.status in [AtletaLoopStatus.ELIMINADO, AtletaLoopStatus.DNF, AtletaLoopStatus.DNS]]
    
    def __repr__(self):
        return f'<Loop {self.numero_loop} - Backyard {self.backyard_id}>'

class AtletaLoop(db.Model):
    __tablename__ = 'atleta_loops'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    atleta_id = db.Column(db.Integer, db.ForeignKey('atletas.id'), nullable=False)
    loop_id = db.Column(db.Integer, db.ForeignKey('loops.id'), nullable=False)
    status = db.Column(db.Enum(AtletaLoopStatus), nullable=False, default=AtletaLoopStatus.ATIVO)
    tempo_inicio = db.Column(db.DateTime)
    tempo_fim = db.Column(db.DateTime)
    tempo_total_segundos = db.Column(db.Integer)
    observacoes = db.Column(db.Text)
    criado_em = db.Column(db.DateTime)
    atualizado_em = db.Column(db.DateTime)
    
    # Relationships
    atleta = db.relationship('Atleta', backref='loops_participados')
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('atleta_id', 'loop_id', name='unique_atleta_por_loop'),
    )
    
    def get_tempo_formatado(self):
        """Retorna o tempo formatado em MM:SS"""
        if not self.tempo_total_segundos:
            return "-"
        
        minutos = self.tempo_total_segundos // 60
        segundos = self.tempo_total_segundos % 60
        return f"{minutos:02d}:{segundos:02d}"
    
    def __repr__(self):
        return f'<AtletaLoop atleta_id={self.atleta_id} loop_id={self.loop_id} status={self.status}>'
