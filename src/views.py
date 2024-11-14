import os
from flask import flash, render_template, url_for, request, redirect
from flask_login import login_user, login_required, logout_user
from . models import Employee, Vote, Award
from .forms import LoginForm
from sqlalchemy import func
from . import db
from . decorators import staff_required
from flask import Blueprint

main = Blueprint("main", __name__)


@main.route("/")
def index():
    company = os.environ.get("COMPANY", "No Company")
    return render_template("index.html", company=company)


@main.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Employee.query.filter_by(email=form.email.data).first()

        if user and user.verify_password(form.password.data):
            next_page = request.args.get("next")
            login_user(user, form.remember_me.data)
            flash("You have been logged in", "info")

            if not next_page or not next_page.startswith("/"):
                next_page = url_for("main.index")
            return redirect(next_page)
        flash("Wrong email or password", "danger")
    form.email.data = ""
    form.password.data = ""
    return render_template("login.html", form=form)


@main.route('/view-not-voted')
@login_required
@staff_required
def not_voted():
    not_voted = Employee.query.filter_by(has_not_voted=True).all()
    return render_template("not_voted.html", not_voted=not_voted)


@main.route('/logout', methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for('main.index'))


@main.route('/voting-page/<int:id>', methods=["GET", "POST"])
@login_required
def voting_page(id):
    # Fetch all awards
    awards = Award.query.all()

    # Filter nominees based on department if the award is department-specific
    user = Employee.query.get(id)
    nominees = Employee.query.filter_by(is_staff=False)
    if any(award.is_department_specific for award in awards):
        nominees = nominees.filter(Employee.department == user.department)

    # Handle form submission
    if request.method == "POST" and user.has_not_voted:
        for award in awards:
            selected_nominee_id = request.form.get(f"award_{award.id}")
            if selected_nominee_id:
                vote = Vote(employee_id=selected_nominee_id, award_id=award.id)
                db.session.add(vote)

        # Mark the user as having voted
        user.has_not_voted = False
        db.session.commit()
        flash("Your votes have been recorded successfully!", "info")
        return redirect(url_for('main.index'))

    return render_template("voting_page.html", awards=awards, nominees=nominees)


@main.route('/award-winners')
@login_required
@staff_required
def award_winners():
    award_winners = {}

    # Calculate winners for each award, considering department specificity
    awards = Award.query.all()
    for award in awards:
        query = db.session.query(Employee, func.count(Vote.id).label(
            'vote_count')).join(Vote).filter(Vote.award_id == award.id)

        if award.is_department_specific:
            departments = db.session.query(
                Employee.department).distinct().all()
            for department in departments:
                department_winners = query.filter(Employee.department == department[0]).group_by(
                    Employee.id).order_by(func.count(Vote.id).desc()).first()
                if department_winners:
                    award_winners[f"{award.name} ({department[0]})"] = {
                        "winners": [department_winners.Employee.name],
                        "vote_count": department_winners.vote_count
                    }
                else:
                    award_winners[f"{award.name} ({department[0]})"] = {
                        "winners": ["No votes cast"],
                        "vote_count": 0
                    }
        else:
            winner = query.group_by(Employee.id).order_by(
                func.count(Vote.id).desc()).first()
            award_winners[award.name] = {
                "winners": [winner.Employee.name] if winner else ["No votes cast"],
                "vote_count": winner.vote_count if winner else 0
            }

    return render_template('award_winners.html', award_winners=award_winners)


@main.route('/all-users')
@login_required
@staff_required
def get_all_user_details():
    all_users = Employee.query.all()
    return render_template("all_users.html", all_users=all_users)
