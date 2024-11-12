from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager


class Employee(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(64), unique=True, nullable=False)
    is_staff = db.Column(db.Boolean, default=False)
    has_not_voted = db.Column(db.Boolean, default=True)
    department = db.Column(db.String(100))  # New department column
    password_hash = db.Column(db.String(256))
    votes = db.relationship('Vote', backref='voter', lazy=True)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def password(self):
        raise AttributeError("Password cannot be seen")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)


class Award(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    is_department_specific = db.Column(db.Boolean, default=False)
    votes = db.relationship('Vote', backref='award', lazy=True)


class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey(
        'employee.id'), nullable=False)
    award_id = db.Column(db.Integer, db.ForeignKey('award.id'), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return Employee.query.get(int(user_id))
