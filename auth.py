from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from passlib.hash import pbkdf2_sha256
from models import User, Base, Role
from db import engine, SessionLocal
from functools import wraps

auth_bp = Blueprint("auth", __name__)
login_manager = LoginManager()
login_manager.login_view = "auth.login"

class UserAdapter(UserMixin):
    def __init__(self, u: User):
        self.u = u
    @property
    def id(self): return str(self.u.id)
    @property
    def role(self): return self.u.role
    @property
    def email(self): return self.u.email
    @property
    def full_name(self): return self.u.full_name

@login_manager.user_loader
def load_user(user_id):
    with SessionLocal() as db:
        u = db.get(User, int(user_id))
        return UserAdapter(u) if u else None

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with SessionLocal() as db:
            u = db.query(User).filter(User.email == email, User.is_active == True).first()
            if u and pbkdf2_sha256.verify(password, u.password_hash):
                login_user(UserAdapter(u))
                return redirect(url_for("dashboard"))
        flash("Błędny login lub hasło", "error")
    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

def init_db_and_admin():
    Base.metadata.create_all(engine)
    from os import getenv
    admin_email = getenv("ADMIN_EMAIL", "admin@example.com").lower()
    admin_pass = getenv("ADMIN_PASSWORD", "Admin123!")
    with SessionLocal() as db:
        if not db.query(User).filter_by(email=admin_email).first():
            admin = User(email=admin_email, full_name="Administrator",
                         password_hash=pbkdf2_sha256.hash(admin_pass), role=Role.ADMIN)
            db.add(admin); db.commit()

def require_roles(*roles):
    def wrapper(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            role_names = [r if isinstance(r, str) else r.name for r in roles]
            if current_user.role.name not in role_names:
                abort(403)
            return fn(*args, **kwargs)
        return inner
    return wrapper
