# Instrukcje wdrożenia na Render

## 1. Utwórz repozytorium na GitHub
- Idź na github.com
- Kliknij "New repository"
- Nazwij: `logitransport-app`
- Zaznacz "Public"
- Kliknij "Create repository"

## 2. Wgraj kod na GitHub
### Opcja A: GitHub Desktop
- Pobierz GitHub Desktop
- Clone repository
- Skopiuj pliki do folderu
- Commit & Push

### Opcja B: Przez przeglądarkę
- Drag & drop plików do repozytorium
- Commit changes

## 3. Wdróż na Render
1. Idź na render.com
2. Zarejestruj się przez GitHub
3. Kliknij "New +" → "Web Service"
4. Wybierz repozytorium
5. Konfiguracja:
   - Name: `logitransport-app`
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`
   - Environment: `Python 3.12`

## 4. Dodaj bazę PostgreSQL
1. "New +" → "PostgreSQL"
2. Nazwij: `logitransport-db`
3. Skopiuj DATABASE_URL

## 5. Skonfiguruj zmienne środowiskowe
W ustawieniach aplikacji:
- DATABASE_URL: (z bazy PostgreSQL)
- FLASK_ENV: `production`

## 6. Wdróż!
Kliknij "Create Web Service"
