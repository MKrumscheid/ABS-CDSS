# ABS-CDSS Enduser Frontend Setup

## Überblick

Das Enduser-Frontend ist eine benutzerfreundliche Oberfläche für Endanwender, um Antibiotikatherapie-Empfehlungen zu erhalten und zu speichern.

## Features

- 📱 **Mobile-First Design** - Optimiert für Smartphones und Tablets
- 🎨 **Material Design 3** - Modernes, medizinisches Farbschema
- 🔍 **Therapie-Empfehlungen** - Evidenzbasierte Antibiotika-Empfehlungen
- 💾 **Speicherfunktion** - Empfehlungen mit optionalem Titel speichern
- 👤 **Patientenintegration** - FHIR-basierte Patientendaten
- 📊 **Übersichtliche Darstellung** - Strukturierte Anzeige der Ergebnisse

## Setup

### 1. PostgreSQL Datenbank

Installieren und konfigurieren Sie PostgreSQL:

```bash
# Windows: Laden Sie PostgreSQL von https://www.postgresql.org/download/windows/ herunter
# Oder verwenden Sie einen Docker Container:
docker run --name abs-cdss-postgres -e POSTGRES_PASSWORD=password -e POSTGRES_DB=abs_cdss -p 5432:5432 -d postgres:15
```

Konfigurieren Sie die Datenbankverbindung in der `DATABASE_URL` Umgebungsvariable oder lassen Sie die Standard-URL:

```
postgresql://postgres:password@localhost:5432/abs_cdss
```

### 2. Backend starten

```bash
# Virtuelle Umgebung aktivieren
.\venv\Scripts\activate.bat

# Backend starten
python backend/main.py
```

Das Backend läuft auf Port 8000 und erstellt automatisch die benötigten Datenbank-Tabellen.

### 3. Frontend starten

#### Admin-Frontend (Port 3000)

```bash
cd frontend
npm start
```

#### Enduser-Frontend (Port 4000)

```bash
cd frontend
npm run start:enduser
```

Oder verwenden Sie die bereitgestellten Batch-Dateien:

- `start_frontend.bat` - Admin-Frontend
- `start_enduser_frontend.bat` - Enduser-Frontend

## Verwendung

### Enduser-Interface (Port 4000)

1. **Therapie-Empfehlung erstellen**

   - Verdachtsdiagnose auswählen
   - Schweregrad und Risikofaktoren angeben
   - Optional: Patienten-ID eingeben
   - Empfehlung generieren lassen

2. **Empfehlung speichern**

   - Nach der Generierung "Speichern" klicken
   - Optionalen Titel vergeben
   - Empfehlung wird mit Datum gespeichert

3. **Gespeicherte Empfehlungen verwalten**
   - Alle gespeicherten Empfehlungen anzeigen
   - Details anzeigen
   - Empfehlungen löschen

### Admin-Interface (Port 3000)

Das bestehende Admin-Interface bleibt unverändert und bietet:

- Leitlinien-Upload und -Verwaltung
- RAG-System-Tests
- FHIR-Integration
- Alle Entwickler-Tools

## API-Endpoints

### Neue Enduser-Endpoints

- `POST /therapy/save` - Empfehlung speichern
- `GET /therapy/saved` - Gespeicherte Empfehlungen auflisten
- `GET /therapy/saved/{id}` - Spezifische Empfehlung abrufen
- `DELETE /therapy/saved/{id}` - Empfehlung löschen

### Bestehende Endpoints

- `POST /therapy/recommend` - Therapie-Empfehlung generieren
- `POST /fhir/patients/search` - Patientensuche
- `GET /fhir/patients/{id}` - Patientendetails

## Technische Details

### Backend-Erweiterungen

- **PostgreSQL Integration** mit SQLAlchemy
- **Neue Pydantic-Modelle** für gespeicherte Empfehlungen
- **Automatische Datenbank-Migration** beim Start

### Frontend-Architektur

- **React 18** mit Material-UI v5
- **React Router** für Navigation
- **Responsive Design** mit Mobile-First Ansatz
- **Modulare Komponenten-Struktur**

### Dateien-Struktur

```
frontend/src/
├── EnduserApp.js                 # Haupt-App für Enduser
├── theme/
│   └── medicalTheme.js          # Material-UI Theme
├── components/
│   ├── Layout/
│   │   └── Layout.js            # Navigation Layout
│   ├── TherapyRequest/
│   │   └── TherapyRequestForm.js # Eingabeformular
│   ├── TherapyResults/
│   │   └── TherapyResults.js     # Ergebnisdarstellung
│   └── SaveRecommendation/
│       └── SaveRecommendationDialog.js # Speicher-Dialog
├── pages/
│   ├── TherapyRecommendation.js  # Hauptseite
│   └── SavedRequests.js          # Gespeicherte Empfehlungen
└── services/
    └── api.js                    # API-Service
```

## Entwicklung

### Lokale Entwicklung

```bash
# Backend
.\venv\Scripts\activate.bat
python backend/main.py

# Frontend (separates Terminal)
cd frontend
npm run start:enduser  # Port 4000 für Enduser
npm start              # Port 3000 für Admin
```

### Build für Produktion

```bash
# Enduser-Build
cd frontend
npm run build:enduser

# Admin-Build
npm run build
```

## Fehlerbehebung

### Häufige Probleme

1. **Datenbank-Verbindungsfehler**

   - PostgreSQL-Service prüfen
   - DATABASE_URL korrekt konfiguriert?
   - Firewall-Einstellungen prüfen

2. **Frontend startet nicht auf Port 4000**

   - Port bereits belegt? `netstat -an | findstr 4000`
   - cross-env installiert? `npm install cross-env`

3. **CORS-Fehler**
   - Backend läuft auf Port 8000?
   - CORS für Port 4000 konfiguriert

### Logs

- Backend-Logs in der Konsole
- Browser-Entwicklerkonsole für Frontend-Fehler
- Netzwerk-Tab für API-Probleme

## Produktions-Deployment

Für Produktionsumgebungen:

1. PostgreSQL-Datenbankserver einrichten
2. Backend mit WSGI-Server (uvicorn, gunicorn) deployen
3. Frontend-Build erstellen und über Nginx/Apache bereitstellen
4. HTTPS konfigurieren
5. Umgebungsvariablen für Produktion setzen
