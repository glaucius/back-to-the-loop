from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# Initialize extension
db = SQLAlchemy()

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
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_ultima_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - Many-to-Many with Atleta
    atletas = db.relationship('Atleta', secondary='atleta_backyard', back_populates='backyards')
    
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
    imagem_perfil = db.Column(db.String(255))
    endereco = db.Column(db.String(255))
    cidade = db.Column(db.String(255))
    estado = db.Column(db.String(255))
    pais = db.Column(db.String(255))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - Many-to-Many with Backyard
    backyards = db.relationship('Backyard', secondary='atleta_backyard', back_populates='atletas')
    
    def __repr__(self):
        return f'<Atleta {self.nome}>'

# Tabela de associação Many-to-Many entre Atleta e Backyard
class AtletaBackyard(db.Model):
    __tablename__ = 'atleta_backyard'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    atleta_id = db.Column(db.Integer, db.ForeignKey('atletas.id'), nullable=False)
    backyard_id = db.Column(db.Integer, db.ForeignKey('backyards.id'), nullable=False)
    data_inscricao = db.Column(db.DateTime, default=datetime.utcnow)
    status_inscricao = db.Column(db.String(50), default='inscrito')  # inscrito, cancelado, finalizado
    posicao_final = db.Column(db.Integer)  # Posição final na corrida (1 = vencedor, 2 = assist, etc.)
    voltas_completadas = db.Column(db.Integer, default=0)  # Número de voltas completadas
    tempo_total = db.Column(db.Time)  # Tempo total de corrida
    
    # Relationships
    atleta = db.relationship('Atleta', backref='inscricoes')
    backyard = db.relationship('Backyard', backref='inscricoes')
    
    def __repr__(self):
        return f'<AtletaBackyard {self.atleta_id}-{self.backyard_id}>'
