#!/usr/bin/env python3
"""
Skrypt do dodania przykładowych danych testowych do bazy danych
"""
import os
import sys
from datetime import datetime

# Dodaj ścieżkę do modułów aplikacji
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import SessionLocal, engine
from models import Base, Load, User, Role, Shift

def create_test_data():
    """Dodaj przykładowe dane do bazy danych"""
    
    # Utwórz tabele jeśli nie istnieją
    Base.metadata.create_all(engine)
    
    with SessionLocal() as db:
        # Sprawdź czy admin istnieje
        admin = db.query(User).filter_by(email="admin@example.com").first()
        if not admin:
            print("Błąd: Admin nie istnieje!")
            return
        
        # Sprawdź czy już są dane
        existing_loads = db.query(Load).count()
        if existing_loads > 0:
            print(f"Baza już zawiera {existing_loads} rekordów. Pomijam dodawanie danych.")
            return
        
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
                created_by_id=admin.id
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
                created_by_id=admin.id
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
                created_by_id=admin.id
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
                created_by_id=admin.id
            ),
        ]
        
        # Dodaj dane do bazy
        for load in test_loads:
            db.add(load)
        
        db.commit()
        print(f"Dodano {len(test_loads)} przykładowych rekordów do bazy danych!")
        print("Teraz odśwież aplikację - Tablica powinna pokazać dane!")

if __name__ == "__main__":
    create_test_data()
