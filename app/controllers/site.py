from flask import render_template, flash, redirect, url_for, abort
from flask_login import login_user, logout_user, current_user
from app import app, db, login_manager
from random import randint

from app.models.tables import User, Area, Candidate, User_Areas, User_Candidates
from app.models.forms import LoginForm, RegisterForm, RegisterAreasForm, RateCandidatesForm
from app.scripts.recommenders.recommend import Hybrid_Recommendation


@login_manager.user_loader
def load_user(id):
    return User.query.filter_by(id=id).first()


@app.route("/")
@app.route("/index")
def index():
    return render_template('index.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user:
            if user.password == form.password.data:
                login_user(user)

                return redirect(url_for('profile'))
            else:
                flash("Senha inválida", 'error')
        else:
            flash("Usuário inválido", 'error')

    return render_template('login.html', form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        new_user = User(form.username.data, form.full_name.data, form.password.data)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        flash("Cadastro feito com sucesso, complete seu perfil a seguir.", 'success')
        return redirect(url_for('register_areas'))

    return render_template('register.html', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route("/register_areas", methods=["GET", "POST"])
def register_areas():

    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    form = RegisterAreasForm()

    if form.validate_on_submit():

        user = current_user

        for field, value in form.data.items():

            if field != "csrf_token":
                area = Area.query.filter_by(area_name=field).first()

                user_area_relationship = User_Areas(user=user, area=area, rate=value)

                db.session.add(user_area_relationship)

        db.session.commit()

        flash("Temas avaliados com sucesso.", 'success')

        if not user.candidates_rating:
            return redirect(url_for('rate_candidates'))
        else:
            return redirect(url_for('profile'))

    return render_template('register_areas.html', form=form)


@app.route("/rate_candidates", methods=["GET", "POST"])
def rate_candidates():

    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    form = RateCandidatesForm()

    if form.is_submitted():

        user = current_user

        for field, value in form.data.items():

            if field != "csrf_token" and value is not None:
                candidate = Candidate.query.filter_by(candname=field).first()

                user_cand_relationship = User_Candidates(user=user, candidate=candidate, rate=value)

                db.session.add(user_cand_relationship)

        db.session.commit()

        flash("Avaliação de candidatos feita com sucesso. Obrigado por completar seu perfil.", 'success')

        return redirect(url_for('profile'))

    else:

        candidates = ['alckmin', 'amoedo', 'bolsonaro', 'ciro', 'daciolo', 'boulos', 'haddad', 'marina']

        for i in range(5):
            index = randint(0, len(candidates) - 1)
            del form[candidates[index]]
            candidates.pop(index)

    return render_template('rate_candidates.html', form=form)


@app.route("/profile")
def profile():
    return render_template('profile.html')


@app.route("/recommendation")
def recommendation():

    list_of_candidates = []

    rec = Hybrid_Recommendation(current_user.id)

    for r in rec:
        aux = Candidate.query.filter_by(id=r[0]).first()
        list_of_candidates.append(aux)

    return render_template('recommendation.html', candidates=list_of_candidates)
