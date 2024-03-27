import json

from flask_sqlalchemy import pagination
from flask_wtf import form

from alba import app, database, bcrypt
from alba.forms import FormLogin, FormCriarConta, FormEditarPerfil, FormCriarPost, FormComentarPost
from flask import render_template, request, redirect, url_for, flash, jsonify
from alba.models import Usuario, Seguidor, Post, Curtida, Comentario
from flask_login import login_user, logout_user, current_user, login_required
import secrets
import os
from PIL import Image


@app.route('/')
@login_required
def homepage():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template('home.html', posts=posts)


@app.route('/usuarios')
@login_required
def usuarios():
    lista_usuarios = Usuario.query.all()
    return render_template('usuarios.html', lista_usuarios=lista_usuarios, titulo='Usuários')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form_login = FormLogin()
    form_criar_conta = FormCriarConta()

    if form_login.validate_on_submit() and 'botao_submit_login' in request.form:
        usuario = Usuario.query.filter_by(email=form_login.email.data).first()
        if usuario and bcrypt.check_password_hash(usuario.senha, form_login.senha.data):
            login_user(usuario, remember=form_login.lembrar_dados.data)
            flash(f'Login feito com sucesso para o e-mail {form_login.email.data}', 'alert-success')
            par_proximo = request.args.get('next')
            if par_proximo:
                return redirect(par_proximo)
            else:
                return redirect(url_for('homepage'))
        else:
            flash('Falha no login. E-mail ou senha incorretos', 'alert-danger')
    if form_criar_conta.validate_on_submit() and 'botao_submit_criar_conta' in request.form:
        senha_cript = bcrypt.generate_password_hash(form_criar_conta.senha.data)
        usuario = Usuario(nome=form_criar_conta.nome.data, username=form_criar_conta.username.data,
                          email=form_criar_conta.email.data, senha=senha_cript)
        database.session.add(usuario)
        database.session.commit()
        flash(f'Conta criada para o e-mail {form_criar_conta.email.data}', 'alert-success')
        return redirect(url_for('homepage'))
    return render_template('login.html', form_login=form_login, form_criar_conta=form_criar_conta)


@app.route('/sair')
@login_required
def sair():
    logout_user()
    flash('Logout feito com sucesso', 'alert-success')
    return redirect(url_for('homepage'))


@app.route('/perfil/<username>')
@login_required
def perfil(username):
    usuario = Usuario.query.filter_by(username=username).first()
    return render_template('perfil.html', usuario=usuario)


@app.route('/perfil/<username>/editar', methods=['GET', 'POST'])
@login_required
def editar_perfil(username):
    if username == current_user.username:
        form_editar_perfil = FormEditarPerfil()
        if form_editar_perfil.validate_on_submit():
            current_user.nome = form_editar_perfil.nome.data
            current_user.email = form_editar_perfil.email.data
            current_user.username = form_editar_perfil.username.data
            if form_editar_perfil.foto_perfil.data:
                imagem = form_editar_perfil.foto_perfil.data
                codigo = secrets.token_hex(8)
                extensao = os.path.splitext(imagem.filename)[1]
                nome_arquivo = codigo + extensao
                caminho = os.path.join(app.root_path, 'static/fotos_perfil', nome_arquivo)
                if extensao != '.svg':
                    tamanho = (400, 400)
                    imagem_reduzida = Image.open(imagem)
                    imagem_reduzida.thumbnail(tamanho)
                    imagem_reduzida.save(caminho)
                else:
                    imagem.save(caminho)
                current_user.foto_perfil = nome_arquivo
            database.session.commit()
            flash(f'Perfil atualizado com sucesso', 'alert-success')
            return redirect(url_for('perfil', username=current_user.username))
        elif request.method == 'GET':
            form_editar_perfil.nome.data = current_user.nome
            form_editar_perfil.username.data = current_user.username
            form_editar_perfil.email.data = current_user.email
        foto_perfil = url_for('static', filename='fotos_perfil/{}'.format(current_user.foto_perfil))
        return render_template('editar_perfil.html', usuario=current_user, foto_perfil=foto_perfil, form_editar_perfil=form_editar_perfil)


@app.route('/perfil/<username>/seguidores')
@login_required
def seguidores_perfil(username):
    usuario = Usuario.query.filter_by(username=username).first()
    lista_usuarios = usuario.buscar_seguidores()
    return render_template('usuarios.html', lista_usuarios=lista_usuarios, titulo=f'Seguidores de {usuario.nome}')


@app.route('/criar-post', methods=['GET', 'POST'])
@login_required
def criar_post():
    form_criar_post = FormCriarPost()
    if form_criar_post.validate_on_submit():
        post = Post(titulo=form_criar_post.titulo.data, corpo=form_criar_post.corpo.data, autor=current_user)
        database.session.add(post)
        database.session.commit()
        flash('Post criado com sucesso', 'alert-success')
        return redirect(url_for('homepage'))
    return render_template('criar_post.html', form_criar_post=form_criar_post)


@app.route('/post/<post_id>', methods=['GET', 'POST'])
@login_required
def exibir_post(post_id):
    post = Post.query.get(post_id)
    return render_template('exibir_post.html', post=post)


@app.route('/post/<post_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_post(post_id):
    post = Post.query.get(post_id)
    if current_user == post.autor:
        form_editar_post = FormCriarPost()
        if request.method == 'GET':
            form_editar_post.titulo.data = post.titulo
            form_editar_post.corpo.data = post.corpo
        elif form_editar_post.validate_on_submit():
            post.titulo = form_editar_post.titulo.data
            post.corpo = form_editar_post.corpo.data
            post.editado = True
            database.session.commit()
            flash('Post atualizado com sucesso', 'alert-success')
            return redirect(url_for('exibir_post', post_id=post_id))
    else:
        return redirect(url_for('exibir_post', post_id=post_id))
    return render_template('editar_post.html', post=post, form_editar_post=form_editar_post)


@app.route('/post/<post_id>/comentar', methods=['GET', 'POST'])
@login_required
def comentar_post(post_id):
    post = Post.query.get(post_id)
    form_comentar_post = FormComentarPost()
    curtido = False
    curtida = Curtida.query.filter_by(id_post=post_id, id_usuario=current_user.id).first()
    if curtida:
        curtido = True
    if form_comentar_post.validate_on_submit():
        comentario = Comentario(id_usuario=current_user.id, id_post=post_id, corpo=form_comentar_post.corpo.data)
        database.session.add(comentario)
        database.session.commit()
        flash('Comentário adicionado com sucesso', 'alert-success')
        return redirect(url_for('exibir_post', post_id=post_id))
    return render_template('criar_comentario.html', post=post, curtido=curtido, form_comentar_post=form_comentar_post)


@app.route('/post/<post_id>/excluir', methods=['GET', 'POST'])
@login_required
def excluir_post(post_id):
    post = Post.query.get(post_id)
    if current_user == post.autor:
        database.session.delete(post)
        database.session.commit()
        flash('Post excluído com sucesso', 'alert-success')
        return redirect(url_for('perfil', username=current_user.username))
    else:
        flash('Você não tem permissão para excluir esse post', 'alert-danger')
        return redirect(url_for('exibir_post', post_id=post_id))


@app.route('/post/<post_id>/curtir')
@login_required
def curtir_post(post_id):
    curtida_existente = Curtida.query.filter_by(id_post=post_id, id_usuario=current_user.id).first()
    if not curtida_existente:
        curtida = Curtida(id_usuario=current_user.id, id_post=post_id)
        database.session.add(curtida)
        database.session.commit()
    return redirect(url_for('exibir_post', post_id=post_id))


@app.route('/post/<post_id>/descurtir')
@login_required
def descurtir_post(post_id):
    curtida_existente = Curtida.query.filter_by(id_post=post_id, id_usuario=current_user.id).first()
    if curtida_existente:
        database.session.delete(curtida_existente)
        database.session.commit()
    return redirect(url_for('exibir_post', post_id=post_id))


@app.route('/comentario/<comentario_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_comentario(comentario_id):
    comentario = Comentario.query.get(comentario_id)
    post = Post.query.get(comentario.id_post)
    if current_user == comentario.autor:
        form_editar_comentario = FormComentarPost()
        if request.method == 'GET':
            form_editar_comentario.corpo.data = comentario.corpo
        elif form_editar_comentario.validate_on_submit():
            comentario.corpo = form_editar_comentario.corpo.data
            comentario.editado = True
            database.session.commit()
            flash('Comentário atualizado com sucesso', 'alert-success')
            return redirect(url_for('exibir_post', post_id=post.id))
    else:
        return redirect(url_for('exibir_post', post_id=post.id))
    return render_template('editar_comentario.html', comentario=comentario, form_editar_comentario=form_editar_comentario, post=post)


@app.route('/comentario/<comentario_id>/excluir', methods=['GET', 'POST'])
@login_required
def excluir_comentario(comentario_id):
    comentario = Comentario.query.get(comentario_id)
    post_id = comentario.id_post
    if current_user == comentario.autor:
        database.session.delete(comentario)
        database.session.commit()
        flash('Comentário excluído com sucesso', 'alert-success')
    else:
        flash('Você não tem permissão para excluir esse comentário', 'alert-danger')
    return redirect(url_for('exibir_post', post_id=post_id))


@app.route('/seguir/<username>')
@login_required
def seguir(username):
    if username != current_user.username:
        usuario_seguido = Usuario.query.filter_by(username=username).first()
        seguindo = usuario_seguido.seguidores.filter_by(id_seguidor=int(current_user.id)).first()
        if not seguindo:
            usuario_seguido = Usuario.query.filter_by(username=username).first()
            seguidor = Seguidor(id_seguido=int(usuario_seguido.id), id_seguidor=int(current_user.id))
            database.session.add(seguidor)
            database.session.commit()
            return redirect(url_for('perfil', username=username))
        else:
            flash('Você já segue esse usuário', 'alert-info')
            return redirect(url_for('perfil', username=username))


@app.route('/parar-seguir/<username>')
@login_required
def parar_seguir(username):
    usuario_seguido = Usuario.query.filter_by(username=username).first()
    seguindo = usuario_seguido.seguidores.filter_by(id_seguidor=int(current_user.id)).first()
    if seguindo:
        database.session.delete(seguindo)
        database.session.commit()
        return redirect(url_for('perfil', username=username))
    else:
        flash('Você não segue esse usuário', 'alert-info')
        return redirect(url_for('perfil', username=username))

