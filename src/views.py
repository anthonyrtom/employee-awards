import os
from flask import flash, render_template, url_for, request, redirect
from flask_login import login_user, login_required, logout_user
from . models import Employee, Vote, Award
from .forms import LoginForm
from sqlalchemy import func
from . import db
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
        user = Employee.query.filter_by(email=form.email.data.lower()).first()

        if user and user.verify_password(form.password.data):
            next_page = request.args.get("next")
            login_user(user, form.remember_me.data)
            flash("You have been logged in")

            if not next_page or not next_page.startswith("/"):
                next_page = url_for("main.index")
            return redirect(next_page)
        flash("Wrong email or password")
    form.email.data = ""
    form.password.data = ""
    return render_template("login.html", form=form)


@main.route('/view-not-voted')
@login_required
def not_voted():
    not_voted = Employee.query.filter_by(has_not_voted=True).all()
    return render_template("not_voted.html", not_voted=not_voted)


@main.route('/logout', methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out")
    return redirect(url_for('main.index'))


@main.route('/voting-page/<int:id>', methods=["GET", "POST"])
@login_required
def voting_page(id):
    # Fetch all awards and non-staff employees
    awards = Award.query.all()
    nominees = Employee.query.filter_by(is_staff=False).all()

    # Handle form submission
    if request.method == "POST":
        user = Employee.query.get(id)

        # Ensure the user has not voted yet
        if user and user.has_not_voted:
            for award in awards:
                # Get the selected nominee for this award from the form data
                selected_nominee_id = request.form.get(f"award_{award.id}")

                # Skip if no nominee was selected for this award
                if not selected_nominee_id:
                    continue

                vote = Vote(employee_id=selected_nominee_id, award_id=award.id)
                db.session.add(vote)

            # Update the user's voting status
            user.has_not_voted = False
            db.session.commit()

            flash("Your votes have been recorded successfully!", "success")
            return redirect(url_for('main.index'))

        else:
            flash("You have already voted.", "danger")
            return redirect(url_for('main.index'))

    return render_template("voting_page.html", awards=awards, nominees=nominees)


@main.route('/award-winners')
@login_required
def award_winners():
    # Dictionary to store winners for each award
    award_winners = {}

    # Loop over each award and calculate the winner(s)
    awards = Award.query.all()
    for award in awards:
        # Get the highest vote count for any employee for this award
        highest_vote_count_query = (
            db.session.query(func.count(Vote.id).label('vote_count'))
            .join(Employee)
            .filter(Vote.award_id == award.id)
            .group_by(Employee.id)
            .order_by(func.count(Vote.id).desc())
            .all()
        )

        if highest_vote_count_query:
            # Extract the highest vote count
            highest_vote_count = highest_vote_count_query[0].vote_count

            # Get all employees with the highest vote count for this award
            winners = (
                db.session.query(Employee)
                .join(Vote)
                .filter(Vote.award_id == award.id)
                .group_by(Employee.id)
                .having(func.count(Vote.id) == highest_vote_count)
                .all()
            )

            # Add the winners to the award_winners dictionary
            award_winners[award.name] = {
                "winners": [winner.name for winner in winners],
                "vote_count": highest_vote_count
            }
        else:
            # If no votes were cast for this award
            award_winners[award.name] = {
                "winners": ["No votes cast"],
                "vote_count": 0
            }

    return render_template('award_winners.html', award_winners=award_winners)
