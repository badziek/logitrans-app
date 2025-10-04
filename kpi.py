from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
import pandas as pd
from io import BytesIO

kpi_bp = Blueprint("kpi", __name__)

@kpi_bp.route("/kpi", methods=["GET"])
@login_required
def kpi_view():
    return render_template("kpi.html", results=None)

@kpi_bp.route("/kpi", methods=["POST"])
@login_required
def kpi_upload():
    file = request.files.get("excel")
    if not file:
        flash("Dodaj plik Excel", "error")
        return redirect(url_for("kpi.kpi_view"))
    data = file.read()
    df = pd.read_excel(BytesIO(data))
    df.columns = [c.strip().lower() for c in df.columns]
    required = {"timestamp", "user_email", "shift", "loads_count"}
    if not required.issubset(set(df.columns)):
        flash(f"Brak wymaganych kolumn: {required}", "error")
        return redirect(url_for("kpi.kpi_view"))
    df["shift"] = df["shift"].astype(str).str.upper().map({"A":"A","B":"B","C":"C"})
    df = df.dropna(subset=["user_email","shift"])
    by_shift = df.groupby("shift").agg(total_loads=("loads_count","sum")).reset_index()
    by_user = df.groupby("user_email").agg(total_loads=("loads_count","sum")).reset_index().sort_values("total_loads", ascending=False)
    res = {"by_shift": by_shift.to_dict(orient="records"),
           "by_user": by_user.to_dict(orient="records")}
    return render_template("kpi.html", results=res)
