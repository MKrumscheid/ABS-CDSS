# ABS-CDSS: Systemarchitektur und Implementierungsdokumentation (wissenschaftliche Fassung)

Version: 1.0  
Autor: Automatisierte Analyse (GitHub Copilot)  
Datum: 2025-10-21

## 1. Überblick und Zielsetzung

Das vorliegende System ist ein KI-gestütztes Clinical Decision Support System (CDSS) zur initialen empirischen Antibiotikatherapie bei Infektionen im Erwachsenenalter. Es kombiniert Retrieval-Augmented Generation (RAG) über deutschsprachige Leitlinieninhalte und Dosistabellen mit Patientendaten aus HL7® FHIR® (R4B) sowie einem generativen Sprachmodell (LLM), um strukturierte, evidenzbasierte Therapieempfehlungen zu erzeugen.

Kernziele:

- Evidenzbasierte Empfehlungsvorschläge (inkl. Dosierung, Applikationsweg, Therapie-Dauer, Monitoring), differenziert nach Schweregrad, Indikationssynonymen und Risikofaktoren.
- Nutzung von FHIR-Patientendaten (Alter, Geschlecht, Nierenfunktion, Medikamente, Allergien) zur Personalisierung und Sicherheit.
- Transparenz durch Quellenzitate und Relevanzscores aus den herangezogenen Leitlinienabschnitten und Dosistabellen.
- Robuste, produktionsnahe Bereitstellung (Docker/Koyeb) mit zwei Frontends: Admin- und Enduser-Interface.

## 2. Architektur auf hoher Ebene

Komponenten:

- Backend (FastAPI, Python 3.11): Orchestriert RAG, FHIR-Zugriff, LLM-Aufrufe, Persistenz und stellt REST/SSE-Endpunkte bereit. Wichtige Module:
  - `backend/main.py`: API-Endpunkte, Streaming (SSE) und Frontend-Serving
  - `backend/rag_service_advanced.py`: RAG-Pipeline (Chunking, FAISS, Query-Building, Dosis-Tabellen)
  - `backend/therapy_context_builder.py`: Kontextaufbau für LLM (Patient + Evidenz + Dosierung + Instruktionen)
  - `backend/therapy_llm_service.py`: LLM-Client (Novita AI/OpenAI-kompatibel), Prompting, JSON-Parsing
  - `backend/fhir_service.py`: HL7 FHIR R4B Retrieval/Parsing (HAPI public), robuste Fallbacks
  - `backend/embedding_service.py`: Lokale vs. Online-Embeddings inkl. Rate-Limiting und Retry
  - `backend/models.py`: Pydantic v2 Modelle und Enums (Indication, Severity, RiskFactor, DTOs)
- Datenablage:
  - Leitlinien (Markdown) unter `backend/data/guidelines/`
  - FAISS-Indizes und Metadaten unter `backend/data/embeddings/`
  - Dosistabellen (`backend/data/dose_info/dosis_tabellen.md`) + zusätzliche Texte (`backend/data/additional_info/`)
  - SQLite (Standard) für gespeicherte Empfehlungen (`backend/abs_cdss.db`)
- Frontend (React + MUI):
  - Admin-Frontend (klassisch, Komponenten in `src/App.js`) – Leitlinienverwaltung, Tests, Debug
  - Enduser-Frontend (MUI-Theme, `src/EnduserApp.js`) – Therapieformular, Ergebnisse, Speicherung
- Deployment: Docker Multi-Stage; Koyeb-Konfiguration (`koyeb.toml`) mit Env-Variablen für Embeddings/LLM.

Datenfluss (vereinfacht):

1. Enduser-Formular → POST /therapy/recommend (oder /therapy/recommend-stream)
2. Kontextaufbau (FHIR -> Patientendaten, RAG -> Leitlinien+Dosis, Instruktionen)
3. LLM-Generierung (JSON-Schema) → validierte Therapieempfehlung
4. Frontend-Rendering + optionales Speichern (/therapy/save)

## 3. Frameworks, Bibliotheken und Laufzeitumgebung

- Python: FastAPI, Uvicorn, Pydantic v2, Requests, fhir.resources (R4B), FAISS, sentence-transformers, python-dotenv, psutil
- Frontend: React, Material UI (MUI), Axios, React Router
- Vektor-Index: FAISS (IP/Flat), Embeddings lokal (SentenceTransformers) oder online (Novita AI)
- LLM: Novita AI OpenAI-kompatibles Chat Completions API (JSON response_format)
- Deployment: Docker (Node 18-alpine für Frontend-Build; python:3.11-slim für Backend), Koyeb

## 4. RAG-Pipeline (inkl. Query-Erstellung)

### 4.1 Dokument-Ingestion und Chunking

- Leitlinien werden per Endpoint `/upload/guideline` (multipart) ingestiert. Metadaten (`GuidelineMetadata`) werden gespeichert.
- Chunking: MarkdownPageSplitter mit Overlap und Tabellen-Erhalt; Markdown oder Plain-Text. Parameter per Env konfigurierbar (z. B. CHUNK_SIZE/OVERLAP).
- Persistenz: Chunks → Embeddings → FAISS; Metadaten in JSON (`data/embeddings/guidelines_metadata.json`).

### 4.2 Query-Konstruktion (MUST/SHOULD/BOOST)

- Funktion `_build_search_query(query: ClinicalQuery)` erzeugt eine deutschsprachige Suchanfrage aus:
  - MUST: Kernbegriffe zur Indikation (inkl. Synonyme aus Enum), Schweregrad-Synonyme
  - SHOULD: Risikofaktoren, Infektionslokalisation, Verdachtskeime, Freitext
  - BOOST: Ankerbegriffe zu Therapie/Dosis/Tabelle/Dauer (erhöhen Ranking)
- Negativ-Booster wurden zugunsten der Robustheit entfernt.

### 4.3 Suche und Scoring

- Semantic Search via FAISS (cosine/IP). Treffer per Guideline gruppiert und ggf. auf Indikation gefiltert.
- Lexikalisches Boosting: für relevante Passagen (z. B. Indikationssynonyme); Kombination von semantischem Score und Boost-Faktoren.
- Top-K Passagen mit Relevanznormalisierung werden für den Kontext selektiert.

### 4.4 Dosistabellen

- Separater Pfad: Parsing der Datei `dose_info/dosis_tabellen.md` → Extraktion von HTML-Tabellen → Konvertierung in LLM-optimierte Textblöcke.
- Eigener FAISS-Index auf Tabellennamen; Suche via `_build_dosing_search_query` (starkes lexikalisches Boosting für Indikations-/Dosisbegriffe).
- Ergebnis: Top-K Dosis-Tabellen mit normalisierten Relevanzscores und Klartext-Tabelleninhalt.

## 5. FHIR-Integration (Patientenretrieval)

- Service: `FHIRService` (R4B) gegen HAPI Public Server. Endpunkte:
  - `POST /patients/search` (Suche per ID oder Name+Geburtsdatum)
  - `GET /patients/{id}` (Details; liefert Bundle oder robusten Roh-Fallback)
- Parsing: Demografie (Alter/Geschlecht), Beobachtungen (LOINC: GFR, Schwangerschaft, CRP etc.), Diagnosen, Allergien (inkl. Schwere/Typ), Medikamente (MedicationStatement → Medication-Resolution).
- Datenbereinigung, um Pydantic-Validierungen zu bestehen; mehrere Konstruktions-Strategien (model_validate/parse_obj/constructor) und Fallback `parse_patient_data_raw` für inkonsistente Bundles.

## 6. Kontextaufbau für das LLM

- `TherapyContextBuilder.build_therapy_context` aggregiert:
  - Klinische Anfrage (Indikation, Schweregrad, Risikofaktoren, Verdachtskeime, Freitext)
  - Patientendaten (FHIR)
  - RAG-Ergebnisse (Leitlinientexte) und Dosistabellen
  - Zusätzliche Wissensbausteine aus `data/additional_info` (Sicherheit/Verträglichkeit, MRGN/MRSA-Risiko, Alter >70, Nierenfunktion ≤60 ml/min)
- Ausgabe: strukturierter Kontexttext mit Abschnitten (Zusammenfassung, Patient, Dosis, Evidenz, Instruktionen, Quellenübersicht) und normalisierten Relevanzwerten.

## 7. LLM-Nutzung (Novita AI, OpenAI-kompatibel)

- Client: OpenAI-kompatible API über Novita (`NOVITA_API_BASE_URL`), Modell z. B. `openai/gpt-oss-120b`.
- Systemprompt: deutschsprachig, striktes JSON-Schema für `TherapyRecommendation` (Felder: `therapy_options[]` mit Wirkstoffen inkl. Dosis/Frequenz/Einheit/Dauer, `clinical_guidance`, `source_citations[]`, `confidence_level`).
- Userprompt: enthält den generierten Kontexttext und Anweisungen zur Anzahl der Optionen, Dosierungsregeln (Nierenfunktion, Interaktionen, Schwangerschaft), sowie zur strikten JSON-Ausgabe.
- Antwortverarbeitung: `response_format={type: json_object}`; robustes Cleaning/Parsing (Grenzfall: Extraktion der JSON-Teilmenge) → Pydantic-Validierung → Rückgabe an Frontend.

## 8. Frontends: Admin vs. Enduser

### 8.1 Enduser-Frontend (`src/EnduserApp.js`)

- UI: MUI-basiertes Layout (`components/Layout/Layout.js`), Navigation (Therapieformular, Gespeicherte Anfragen).
- Seiten:
  - `TherapyRecommendation`: Formular (`TherapyRequestForm`) → POST `/therapy/recommend` → Anzeige (`TherapyResults`) → Speichern (`/therapy/save`).
  - `SavedRequests`: Liste/Details/Löschen über `/therapy/saved`, `/therapy/saved/{id}`, DELETE.
- Services (`services/api.js`):
  - Therapie (streaming/non-streaming), Speichern, Laden, Löschen
  - Patienten: Suche/Details (FHIR)
  - Dropdown-Optionen (Indikationen, Schweregrade, Risikofaktoren) konsistent zu Backend-Enums
- Streaming: Optional via `/therapy/recommend-stream` mit SSE über fetch-Reader und Progress-Callbacks.

### 8.2 Admin-Frontend (`src/App.js`)

- Admin-Ansichten (klassisch mit Bootstrap): Leitlinien-Upload (`/upload/guideline`), RAG-Suche/Analyse (`/search`, `/test-query`), System-Stats (`/stats`), FHIR-Tests, etc. Dient v. a. Debugging/Administration.
- Umschaltung über `REACT_APP_MODE` (Docker-Build erzeugt zwei Builds; Admin unter `/admin`, Enduser unter `/`).

## 9. Integration Frontend ↔ Backend

- REST-Endpunkte (Beispiele):
  - POST `/therapy/recommend` (synchrone Empfehlung; Timeout-Handling clientseitig bis 5 min)
  - POST `/therapy/recommend-stream` (SSE mit Fortschrittsmeldungen)
  - POST `/patients/search`, GET `/patients/{id}` (FHIR)
  - POST `/therapy/save`, GET `/therapy/saved`, GET `/therapy/saved/{id}`, DELETE `/therapy/saved/{id}`
  - GET `/test-query` (Debug: MUST/SHOULD/BOOST), GET `/therapy/context` (Kontext-Summary)
- CORS/Static-Serving: FastAPI mounted statics für beide Frontends in Produktion; Dev-Fallback `/frontend/build`.

## 10. Deployment und Umgebung

- Dockerfile (Multi-Stage):
  - Stage 1: Node 18-alpine baut Admin (`REACT_APP_MODE=admin`, `PUBLIC_URL=/admin`) und Enduser (`REACT_APP_MODE=enduser`, `PUBLIC_URL=/`) Builds.
  - Stage 2: python:3.11-slim installiert Backend-Requirements (`backend/requirements-prod.txt`), kopiert Code und statische Builds nach `./static/admin` bzw. `./static/enduser`.
  - Start: Uvicorn auf Port 8000; Healthcheck via `/health`.
- Koyeb (`koyeb.toml`):
  - Free-Tier-Optimierung (nano, 512Mi RAM), Region `fra`.
  - Env: `USE_ONLINE_EMBEDDINGS`, Ratenlimit für Embeddings, Novita API-Basis/Modelle, RAG-Parameter (CHUNK_SIZE/OVERLAP), Logging-Level.
  - Secrets in `koyeb-env-template.json` (z. B. `NOVITA_API_KEY`, optional `DATABASE_URL` für externe DB).

## 11. Daten- und Fehlertoleranz

- RAG: Kombination aus semantischer Suche und lexikalischem Boost minimiert Fehlzuordnungen; Top-K Auswahl pro Leitlinie; robustes Index-Rebuild bei Löschungen.
- FHIR: Defensive Parser mit Mehrfach-Strategien; Roh-Fallback bei Bundle-Problemen; LOINC-basierte Extraktion.
- LLM: Strenges JSON-Schema + `response_format` reduzieren Parsingfehler; zusätzliche Sanitization bei Grenzfällen.
- Frontend: SSE-Keep-Alive gegen Cloud-Timeouts; dediziertes Timeout- und Fehlermanagement mit Wiederholoption.

## 12. Qualitätssicherung und Debugging-Hilfen

- Endpunkte: `/test-query`, `/therapy/context`, `/health`, `/device-info`, `/debug/fhir` (siehe `main.py`).
- Logging-Level per Env; Metriken (psutil) optional in Nicht-Streaming-Endpoint geloggt.
- Unit-Tests vorhanden (z. B. `backend/test_*`), Fokus auf RAG, Dosing und Rate-Limiting.

## 13. Sicherheit und Compliance (Kurzüberblick)

- Keine Patientendatenpersistenz über den notwendigen Umfang hinaus; Saved Recommendations optional und explizit.
- API-Schlüssel (Novita) als Secret in Deployment-Umgebung.
- Non-root User im Container; minimale Pakete.
- FHIR-Zugriff auf öffentliche HAPI-Instanz zu Demonstrationszwecken; Produktivbetrieb sollte interne FHIR-Server und AuthN/Z nutzen.

## 14. Nächste Schritte und kleine Verbesserungen

- UI: Hinweis/Badge bei Streaming-Status, Link zu Quellenabschnitten in Leitlinien-Viewer (falls Admin-UI erweitert).
- Backend: Optionaler Wechsel auf serverseitiges EventSource-Protokoll für stabileres Streaming in Proxies; Caching von Dosis-Tabellen.
- RAG: Evaluationsskript für Query-Qualität; Hybrid-Suche (BM25 + FAISS) für noch robustere Ergebnisse.
- FHIR: Mapping weiterer LOINC-Codes; optional SMART-on-FHIR Auth.
- LLM: Validierungs-JSON-Schema explizit als Draft 2020-12 definieren; automatische Retry mit Backoff bei 5xx.

## 15. Anhang: Wichtige Endpunkte (Kurzliste)

- GET /health, GET /stats, GET /indications, GET /test-query
- POST /upload/guideline, GET/DELETE /guidelines, DELETE /guidelines/{id}
- POST /therapy/recommend, POST /therapy/recommend-stream
- POST /therapy/save, GET /therapy/saved, GET /therapy/saved/{id}, DELETE /therapy/saved/{id}
- POST /patients/search, GET /patients/{id}

Ende der Dokumentation.
