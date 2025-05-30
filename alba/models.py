from sqlalchemy import UniqueConstraint, desc, Enum
from alba import database, login_manager
from datetime import datetime
from flask_login import UserMixin
import enum


class TipoUsuario(enum.Enum):
    COMUM = 'COMUM'
    TESTE = 'TESTE'


@login_manager.user_loader
def load_usuario(id_usuario):
    return Usuario.query.get(int(id_usuario))


class Usuario(database.Model, UserMixin):
    id = database.Column(database.Integer, primary_key=True)
    nome = database.Column(database.String(50), nullable=False)
    username = database.Column(database.String, nullable=False, unique=True)
    email = database.Column(database.String, nullable=False, unique=True)
    senha = database.Column(database.String, nullable=False)
    foto_perfil = database.Column(database.String, default='default.svg')
    tipo_usuario = database.Column(Enum(TipoUsuario), nullable=False, default=TipoUsuario.COMUM)
    posts = database.Relationship('Post', backref='autor', lazy=True)
    comentarios = database.Relationship('Comentario', backref='autor', lazy=True)
    seguidores = database.relationship('Seguidor', foreign_keys='Seguidor.id_seguido', backref='seguidores', lazy='dynamic')

    def contar_posts(self):
        return len(self.posts)

    def contar_curtidas(self):
        total = 0
        for post in self.posts:
            total += post.curtidas.count()
        return total

    def segue_usuario(self, id_usuario):
        if self.seguidores.filter_by(id_seguidor=int(id_usuario)).first():
            return True
        else:
            return False

    def buscar_seguidores(self):
        seguidores = []
        for seguidor in self.seguidores.all():
            seguidores.append(Usuario.query.filter_by(id=seguidor.id).first())
        return seguidores


class Post(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    titulo = database.Column(database.String, nullable=False)
    corpo = database.Column(database.Text, nullable=False)
    data_criacao = database.Column(database.DateTime, nullable=False, default=datetime.utcnow)
    editado = database.Column(database.Boolean, nullable=False, default=False)
    id_usuario = database.Column(database.Integer, database.ForeignKey('usuario.id'), nullable=False)
    curtidas = database.Relationship('Curtida', backref='post_curtido', lazy='dynamic')
    comentarios = database.Relationship('Comentario', backref='comentario', lazy=True)

    def serialize(self):
        return {
            'id': self.id,
            'titulo': self.titulo,
            'corpo': self.corpo,
            'data_criacao': self.data_criacao,
            'editado': self.editado,
            'id_usuario': self.id_usuario
        }

    def contar_comentarios(self):
        return len(self.comentarios)

    def exibir_comentarios(self):
        return Comentario.query.filter_by(id_post=self.id).order_by(desc(Comentario.data_comentario)).all()

    def curtiu_post(self, id_usuario):
        if self.curtidas.filter_by(id_usuario=id_usuario).first():
            return True
        else:
            return False


class Seguidor(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    id_seguido = database.Column(database.Integer, database.ForeignKey('usuario.id'), nullable=False)
    id_seguidor = database.Column(database.Integer, database.ForeignKey('usuario.id'), nullable=False)

    __table_args__ = (
        UniqueConstraint('id_seguido', 'id_seguidor', name='unico_seguidor'),
    )


class Curtida(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    id_usuario = database.Column(database.Integer, database.ForeignKey('usuario.id'), nullable=False)
    id_post = database.Column(database.Integer, database.ForeignKey('post.id'), nullable=False)


class Comentario(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    id_usuario = database.Column(database.Integer, database.ForeignKey('usuario.id'), nullable=False)
    id_post = database.Column(database.Integer, database.ForeignKey('post.id'), nullable=False)
    corpo = database.Column(database.Text, nullable=False)
    data_comentario = database.Column(database.DateTime, nullable=False, default=datetime.utcnow)
    editado = database.Column(database.Boolean, nullable=False, default=False)

