from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
import os
from db import engine, SessionLocal
from models import Base, User, Role
from auth import auth_bp, login_manager, init_db_and_admin, require_roles
from loads import loads_bp
from kpi import kpi_bp
from passlib.hash import pbkdf2_sha256
import re

app = Flask(__name__)

# Ustaw unikalne sesje dla różnych przeglądarek
import secrets
app.secret_key = secrets.token_hex(32)

def validate_password(password):
    """Walidacja hasła: min 6 znaków, przynajmniej jedna duża litera"""
    if len(password) < 6:
        return False, "Hasło musi mieć minimum 6 znaków"
    if not re.search(r'[A-Z]', password):
        return False, "Hasło musi zawierać przynajmniej jedną dużą literę"
    return True, "Hasło jest poprawne"
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET", "dev-secret")

# DB init & admin
Base.metadata.create_all(engine)
init_db_and_admin()

# login manager
login_manager.init_app(app)

# blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(loads_bp)
app.register_blueprint(kpi_bp)

@app.route("/")
@login_required
def dashboard():
    return redirect(url_for("loads.list_loads"))

@app.route("/users", methods=["GET", "POST"])
@login_required
@require_roles(Role.ADMIN, Role.SUPERVISOR)
def users_manage():
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "add":
            # Dodawanie nowego użytkownika
            email = request.form.get("email").strip().lower()
            full_name = request.form.get("full_name").strip()
            password = request.form.get("password")
            role_str = request.form.get("role")
            
            # SuperVisor może dodawać tylko User
            if current_user.role == Role.SUPERVISOR and role_str != "USER":
                flash("Możesz dodawać tylko użytkowników z rolą USER", "error")
                return redirect(url_for("users_manage"))
            
            # Walidacja hasła
            is_valid, message = validate_password(password)
            if not is_valid:
                flash(message, "error")
                return redirect(url_for("users_manage"))
            
            role = Role[role_str]
            with SessionLocal() as db:
                if db.query(User).filter_by(email=email).first():
                    flash("Taki użytkownik już istnieje", "error")
                else:
                    db.add(User(email=email, full_name=full_name,
                                password_hash=pbkdf2_sha256.hash(password),
                                role=role, is_active=True))
                    db.commit()
                    flash("Użytkownik dodany", "success")
        
        elif action == "edit":
            # Edycja użytkownika
            user_id = request.form.get("user_id")
            email = request.form.get("email").strip().lower()
            full_name = request.form.get("full_name").strip()
            role_str = request.form.get("role")
            
            with SessionLocal() as db:
                user = db.query(User).get(user_id)
                if user:
                    user.email = email
                    user.full_name = full_name
                    user.role = Role[role_str]
                    db.commit()
                    flash("Użytkownik zaktualizowany", "success")
        
        elif action == "change_password":
            # Zmiana hasła
            user_id = request.form.get("user_id")
            new_password = request.form.get("new_password")
            
            # Walidacja hasła
            is_valid, message = validate_password(new_password)
            if not is_valid:
                flash(message, "error")
                return redirect(url_for("users_manage"))
            
            with SessionLocal() as db:
                user = db.query(User).get(user_id)
                if user:
                    user.password_hash = pbkdf2_sha256.hash(new_password)
                    db.commit()
                    flash("Hasło zmienione", "success")
        
        elif action == "delete":
            # Usuwanie użytkownika (tylko Admin)
            user_id = request.form.get("user_id")
            with SessionLocal() as db:
                user = db.query(User).get(user_id)
                if user and user.id != current_user.id:  # Nie można usunąć siebie
                    db.delete(user)
                    db.commit()
                    flash("Użytkownik usunięty", "success")
                else:
                    flash("Nie można usunąć tego użytkownika", "error")
    
    with SessionLocal() as db:
        users = db.query(User).all()
    return render_template("users.html", users=users)

@app.route("/clear_all_data")
@login_required
@require_roles(Role.ADMIN)
def clear_all_data():
    """Endpoint do wyczyszczenia wszystkich danych z bazy"""
    from models import Load
    
    with SessionLocal() as db:
        # Usuń wszystkie rekordy Load
        db.query(Load).delete()
        db.commit()
        return f"Wyczyszczono wszystkie dane z bazy! <a href='/loads'>Przejdź do Tablicy</a>"

@app.route("/add_test_data")
@login_required
@require_roles(Role.ADMIN)
def add_test_data():
    """Endpoint do dodania przykładowych danych testowych"""
    from models import Load, Shift
    
    with SessionLocal() as db:
        # Sprawdź czy już są dane
        existing_loads = db.query(Load).count()
        if existing_loads > 0:
            return f"Baza już zawiera {existing_loads} rekordów. Pomijam dodawanie danych."
        
        # Dodaj przykładowe dane
        test_loads = [
            # Slot 17:00 - L01
            Load(
                time_slot="17:00",
                lane="L01",
                trailer_no="TR001",
                status="PL",
                ship_date="04.10.2025",
                area="J01",
                seq=1,
                planned=100,
                done=0,
                lo_code="LO001",
                picker="Jan Kowalski",
                shift=Shift.A,
                created_by_id=current_user.id
            ),
            Load(
                time_slot="17:00",
                lane="L01",
                trailer_no="TR001",
                status="PL",
                ship_date="04.10.2025",
                area="J02",
                seq=2,
                planned=50,
                done=0,
                lo_code="LO002",
                picker="Anna Nowak",
                shift=Shift.A,
                created_by_id=current_user.id
            ),
            # Slot 17:00 - L02
            Load(
                time_slot="17:00",
                lane="L02",
                trailer_no="TR002",
                status="PA",
                ship_date="04.10.2025",
                area="J03",
                seq=1,
                planned=75,
                done=25,
                lo_code="LO003",
                picker="Piotr Wiśniewski",
                shift=Shift.A,
                created_by_id=current_user.id
            ),
            # Slot 18:00 - L01
            Load(
                time_slot="18:00",
                lane="L01",
                trailer_no="TR003",
                status="PL",
                ship_date="05.10.2025",
                area="J01",
                seq=1,
                planned=200,
                done=0,
                lo_code="LO004",
                picker="Maria Kowalczyk",
                shift=Shift.B,
                created_by_id=current_user.id
            ),
        ]
        
        # Dodaj dane do bazy
        for load in test_loads:
            db.add(load)
        
        db.commit()
        return f"Dodano {len(test_loads)} przykładowych rekordów do bazy danych! <a href='/loads'>Przejdź do Tablicy</a>"

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    
    print(f"Starting Flask on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
