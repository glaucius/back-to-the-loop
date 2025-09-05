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
    
    def __repr__(self):
        return f'<Backyard {self.nome}>'

# Note: Atleta model is commented out as per requirements
# class Atleta(db.Model):
#     __tablename__ = 'atletas'
#     
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     nome = db.Column(db.String(255), nullable=False)
#     data_nascimento = db.Column(db.Date)
#     sexo = db.Column(db.String(50))
#     cpf = db.Column(db.String(14), unique=True)
#     email = db.Column(db.String(255), nullable=False, unique=True)
#     password = db.Column(db.String(255), nullable=False)
#     endereco = db.Column(db.String(255))
#     cidade = db.Column(db.String(255))
#     estado = db.Column(db.String(255))
#     pais = db.Column(db.String(255))
#     profile_picture_path = db.Column(db.String(255))
#     data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
#     data_ultima_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
#     
#     def __repr__(self):
#         return f'<Atleta {self.nome}>'
