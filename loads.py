# loads.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required, current_user
from db import SessionLocal
from models import Load, Shift

loads_bp = Blueprint("loads", __name__)

def add_no_cache_headers(response):
    """Dodaj nagłówki anti-cache do odpowiedzi"""
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Last-Modified'] = 'Thu, 01 Jan 1970 00:00:00 GMT'
    response.headers['Vary'] = 'Accept-Encoding'
    return response

@loads_bp.route("/loads", methods=["GET"])
@login_required
def list_loads():
    # Debug: sprawdź sesję użytkownika
    print(f"=== SESSION DEBUG ===")
    print(f"Current user: {current_user.email}")
    print(f"User full name: {current_user.full_name}")
    print(f"User role: {current_user.role.name}")
    print(f"Session ID: {request.cookies.get('session', 'NO SESSION')}")
    print(f"User-Agent: {request.headers.get('User-Agent', 'NO USER-AGENT')[:50]}...")
    filter_time = request.args.get("time_slot")
    with SessionLocal() as db:
        q = db.query(Load).order_by(Load.time_slot, Load.lane, Load.seq)
        if filter_time:
            q = q.filter(Load.time_slot == filter_time)
        items = q.all()

    board = {}
    for r in items:
        ts = r.time_slot or "-"
        data = board.setdefault(ts, {"trailers": set(), "lanes": {}})
        # Ustaw ship_date tylko jeśli jeszcze nie jest ustawione lub jeśli nowy rekord ma datę
        if "ship_date" not in data or (getattr(r, "ship_date", "") and not data["ship_date"]):
            data["ship_date"] = getattr(r, "ship_date", "")
        if r.trailer_no:
            data["trailers"].add(r.trailer_no)
        lane = (r.lane or "L01").upper()
        data["lanes"].setdefault(lane, []).append(r)

    # 3 stałe pasy i sortowanie po seq
    fixed_lanes = ["L01", "L02", "L03"]
    
    # Jeśli board jest pusty, dodaj domyślny time slot
    if not board:
        board["17:00"] = {"trailers": set(), "lanes": {}, "ship_date": ""}
    
    for ts, data in board.items():
        data["trailer_text"] = ", ".join(sorted(data["trailers"])) if data["trailers"] else "00000000"

        # upewnij się, że mamy klucze dla wszystkich pasów
        for ln in fixed_lanes:
            data["lanes"].setdefault(ln, [])
        data["lanes"] = {ln: data["lanes"].get(ln, []) for ln in fixed_lanes}
        
        # Ustaw nagłówki dla każdego pasa
        data["headers"] = {}
        for ln in fixed_lanes:
            # Znajdź pierwszy rekord dla tego pasa, żeby pobrać nagłówki
            first_record = None
            for r in data["lanes"][ln]:
                if r:
                    first_record = r
                    break
            
            if first_record:
                data["headers"][ln] = {
                    "trailer": first_record.trailer_no or "00000000",
                    "status": first_record.status or "PL",
                    "time_slot": first_record.time_slot or ts,
                    "ship_date": getattr(first_record, "ship_date", "") or ""
                }
            else:
                # Domyślne wartości jeśli brak rekordów
                data["headers"][ln] = {
                    "trailer": "00000000",
                    "status": "PL", 
                    "time_slot": ts,
                    "ship_date": data.get("ship_date", "") or ""
                }

        # --- BEZPIECZNE SORTOWANIE PO SEQ (int/str/None) ---
        def seq_key(row):
            v = getattr(row, "seq", None)
            try:
                return (v is None, int(v))  # None idzie na koniec; reszta rzutowana na int
            except Exception:
                return (True, 10 ** 9)  # cokolwiek „dziwnego” ląduje na końcu

        for ln in fixed_lanes:
            data["lanes"][ln].sort(key=seq_key)

    # Debug: sprawdź czy nagłówki są ustawione
    print("=== DEBUG: Board data ===")
    for ts, data in board.items():
        print(f"Time slot: {ts}")
        print(f"  Headers: {data.get('headers', 'NOT SET')}")
        print(f"  Ship date: {data.get('ship_date', 'NOT SET')}")
        for lane, rows in data.get('lanes', {}).items():
            print(f"  Lane {lane}: {len(rows)} rows")
            if rows:
                first_row = rows[0]
                print(f"    First row trailer: {getattr(first_row, 'trailer_no', 'None')}")
                print(f"    First row status: {getattr(first_row, 'status', 'None')}")
                print(f"    First row time_slot: {getattr(first_row, 'time_slot', 'None')}")
                print(f"    First row ship_date: {getattr(first_row, 'ship_date', 'None')}")
            
            # Sprawdź nagłówki dla tego pasa
            if 'headers' in data and lane in data['headers']:
                hdr = data['headers'][lane]
                print(f"    Header trailer: {hdr.get('trailer', 'None')}")
                print(f"    Header status: {hdr.get('status', 'None')}")
                print(f"    Header time_slot: {hdr.get('time_slot', 'None')}")
                print(f"    Header ship_date: {hdr.get('ship_date', 'None')}")
            else:
                print(f"    Header for {lane}: NOT FOUND")
    
    # Debug: sprawdź czy template otrzyma poprawne dane
    print("=== DEBUG: Template data ===")
    for ts, data in board.items():
        print(f"Time slot: {ts}")
        if 'headers' in data:
            for lane, hdr in data['headers'].items():
                print(f"  Lane {lane}:")
                print(f"    Template will get trailer: {hdr.get('trailer', 'None')}")
                print(f"    Template will get status: {hdr.get('status', 'None')}")
                print(f"    Template will get time_slot: {hdr.get('time_slot', 'None')}")
                print(f"    Template will get ship_date: {hdr.get('ship_date', 'None')}")
        else:
            print(f"  No headers found for time slot {ts}")
    
    response = make_response(render_template("dashboard.html", board=board, filter_time=filter_time or ""))
    response.headers['ETag'] = f'"{hash(str(board))}"'
    return add_no_cache_headers(response)


@loads_bp.route("/loads", methods=["POST"])
@login_required
def create_load():
    time_slot  = (request.form.get("time_slot")  or "17:00").strip()
    lane       = (request.form.get("lane")       or "L01").strip().upper()
    area       = (request.form.get("area")       or "").strip()
    trailer_no = (request.form.get("trailer_no") or "").strip()
    status     = (request.form.get("status")     or "").strip()
    ship_date  = (request.form.get("ship_date")  or "").strip()

    # liczby z inputów – jeśli puste, to None
    def to_int(v):
        v = (v or "").strip()
        return int(v) if v.isdigit() else None

    seq     = to_int(request.form.get("seq"))
    planned = to_int(request.form.get("planned"))
    done    = to_int(request.form.get("done"))

    lo_code = (request.form.get("lo_code") or "").strip()
    picker  = (request.form.get("picker")  or "").strip()

    with SessionLocal() as db:
        l = Load(
            time_slot=time_slot,
            lane=lane,
            area=area,           # <— NEW
            trailer_no=trailer_no,
            status=status,
            ship_date=ship_date, # <— NEW (jeśli dodałeś kolumnę)
            seq=seq,
            planned=planned,
            done=done,
            lo_code=lo_code,
            picker=picker,
            shift=Shift.A,                  # lub wyciągnij realną zmianę
            created_by_id=current_user.id
        )
        db.add(l)
        db.commit()

    return redirect(url_for("loads.list_loads", time_slot=time_slot))

@loads_bp.route("/loads/<int:load_id>/delete", methods=["POST"])
@login_required
def delete_load(load_id):
    with SessionLocal() as db:
        l = db.get(Load, load_id)
        if not l:
            flash("Nie znaleziono rekordu", "error")
        else:
            db.delete(l)
            db.commit()
            flash("Usunięto rekord", "success")
    return redirect(url_for("loads.list_loads"))


@loads_bp.route("/loads/<int:load_id>/edit", methods=["POST"])
@login_required
def edit_load(load_id):
    # Sprawdź uprawnienia - USER nie może edytować danych
    if current_user.role.name == 'USER':
        flash("Nie masz uprawnień do edycji danych", "error")
        return redirect(url_for("loads.list_loads"))
    
    fields = ["seq","planned","done","lo_code","picker","status","time_slot","lane","trailer_no","ship_date"]
    updates = {f: request.form.get(f) for f in fields if f in request.form}

    # konwersje liczb
    for k in ["seq","planned","done"]:
        if k in updates and updates[k] not in (None, "", "None"):
            try: updates[k] = int(updates[k])
            except ValueError: updates[k] = None

    with SessionLocal() as db:
        l = db.get(Load, load_id)
        if not l:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return {"success": False, "error": "Nie znaleziono rekordu"}, 404
            flash("Nie znaleziono rekordu", "error")
            return redirect(url_for("loads.list_loads"))
        else:
            # Zapisz time_slot przed zamknięciem sesji
            current_time_slot = l.time_slot
            for k, v in updates.items():
                # tylko jeśli atrybut istnieje w modelu
                if hasattr(l, k):
                    setattr(l, k, v if v != "" else None)
            db.commit()
    
    # Sprawdź czy to AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        response = jsonify({"success": True, "message": "Zapisano pomyślnie"})
        return add_no_cache_headers(response)
    
    return redirect(url_for("loads.list_loads", time_slot=updates.get("time_slot") or current_time_slot))


# ——— Nagłówek: trailer / time / status / (NEW) ship_date ———
@loads_bp.route("/loads/update_header", methods=["POST"])
@login_required
def update_header():
    # Sprawdź uprawnienia - USER nie może edytować nagłówków
    if current_user.role.name == 'USER':
        flash("Nie masz uprawnień do edycji nagłówków", "error")
        return redirect(url_for("loads.list_loads"))
    
    orig_time_slot = (request.form.get("orig_time_slot") or "").strip()   # identyfikator bieżącej karty
    lane = (request.form.get("lane") or "L01").strip().upper()
    new_time_slot = (request.form.get("time_slot") or "").strip()
    trailer_no = (request.form.get("trailer_no") or "").strip()
    status = (request.form.get("status") or "").strip()
    ship_date = (request.form.get("ship_date") or "").strip()   # <-- NOWOŚĆ

    if not orig_time_slot or not lane:
        flash("Brak wymaganych danych nagłówka", "error")
        return redirect(url_for("loads.list_loads", time_slot=orig_time_slot or None))

    with SessionLocal() as db:
        # pobierz wszystkie rekordy z tej karty (lane + orig_time_slot)
        rows = db.query(Load).filter(Load.time_slot == orig_time_slot, Load.lane == lane).all()
        if not rows:
            flash("Brak wierszy do aktualizacji dla tej kolumny", "warning")
        else:
            for r in rows:
                if trailer_no:    r.trailer_no = trailer_no
                if new_time_slot: r.time_slot = new_time_slot
                if status:        r.status = status
                if ship_date:     r.ship_date = ship_date   # <-- zapisujemy datę
            db.commit()
            flash(f"Zaktualizowano nagłówek kolumny {lane} ({len(rows)} wierszy)", "success")

    # Po zmianie TIME przenosimy widok na nowy slot (jeśli został podany)
    response = redirect(url_for("loads.list_loads", time_slot=new_time_slot or orig_time_slot))
    return add_no_cache_headers(response)


@loads_bp.route("/loads/clear_lane", methods=["POST"])
@login_required
def clear_lane():
    """Czyści wszystkie dane w danej kolumnie (lane) dla danego czasu (time_slot)"""
    # Sprawdź uprawnienia - USER nie może czyścić danych
    if current_user.role.name == 'USER':
        flash("Nie masz uprawnień do czyszczenia danych", "error")
        return redirect(url_for("loads.list_loads"))
    
    time_slot = request.form.get("time_slot", "").strip()
    lane = request.form.get("lane", "").strip().upper()
    
    if not time_slot or not lane:
        flash("Brak wymaganych danych", "error")
        return redirect(url_for("loads.list_loads"))
    
    with SessionLocal() as db:
        # Znajdź wszystkie rekordy dla danej kolumny i czasu
        rows = db.query(Load).filter(Load.time_slot == time_slot, Load.lane == lane).all()
        
        if not rows:
            flash(f"Brak danych do wyczyszczenia w kolumnie {lane}", "warning")
        else:
            # Wyczyść pola: planned, done, lo_code, picker
            for row in rows:
                row.planned = None
                row.done = None
                row.lo_code = None
                row.picker = None
            
            db.commit()
            flash(f"Wyczyszczono dane w kolumnie {lane} ({len(rows)} rekordów)", "success")
    
    return redirect(url_for("loads.list_loads", time_slot=time_slot))


