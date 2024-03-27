from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, EmailField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from alba.models import Usuario
from flask_login import current_user


class FormCriarConta(FlaskForm):
    username = StringField("Nome de usuário", validators=[DataRequired(), Length(min=3)])
    nome = StringField("Nome", validators=[DataRequired(), Length(min=3, max=50)])
    email = EmailField("E-mail", validators=[DataRequired(), Email()])
    senha = PasswordField("Senha", validators=[DataRequired(), Length(8, 20)])
    confirmacao = PasswordField("Confirmação da senha", validators=[EqualTo("senha")])
    botao_submit_criar_conta = SubmitField("Criar conta")

    def validate_email(self, email):
        usuario = Usuario.query.filter_by(email=email.data).first()
        if usuario:
            raise ValidationError("Já existe um usuário cadastrado com esse e-mail")

    def validate_username(self, username):
        usuario = Usuario.query.filter_by(username=username.data).first()
        if usuario:
            raise ValidationError("Alguém já está usando esse nome de usuário")


class FormLogin(FlaskForm):
    email = StringField("E-mail", validators=[DataRequired(), Email()])
    senha = PasswordField("Senha", validators=[DataRequired(), Length(8, 20)])
    lembrar_dados = BooleanField("Lembrar meus dados de acesso")
    botao_submit_login = SubmitField("Fazer login")


class FormEditarPerfil(FlaskForm):
    username = StringField("Nome de usuário", validators=[DataRequired(), Length(min=3)])
    nome = StringField("Nome", validators=[DataRequired(), Length(min=3, max=50)])
    email = EmailField("E-mail", validators=[DataRequired(), Email()])
    foto_perfil = FileField("Foto de perfil", validators=[FileAllowed(['jpg', 'png', 'jpeg', 'svg'])])
    botao_submit_editar_perfil = SubmitField("Salvar alterações")

    def validate_email(self, email):
        if current_user.email != email.data:
            usuario = Usuario.query.filter_by(email=email.data).first()
            if usuario:
                raise ValidationError("Já existe um usuário cadastrado com esse e-mail")

    def validate_username(self, username):
        if current_user.username != username.data:
            usuario = Usuario.query.filter_by(username=username.data).first()
            if usuario:
                raise ValidationError("Alguém já está usando esse nome de usuário")


class FormCriarPost(FlaskForm):
    titulo = StringField("Título do post", validators=[DataRequired(), Length(min=1, max=140)])
    corpo = TextAreaField("Post", validators=[DataRequired(), Length(min=1, max=256)])
    botao_submit_criar_post = SubmitField("Postar")


class FormComentarPost(FlaskForm):
    corpo = TextAreaField("Comentário", validators=[DataRequired(), Length(min=1, max=256)])
    botao_submit_comentar_post = SubmitField("Comentar")

