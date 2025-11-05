# RAG Toggle Feature - Dokumentation

## Übersicht

Diese Funktion ermöglicht es, die RAG-Funktionalität (Retrieval Augmented Generation) temporär zu deaktivieren, um Validierungstests durchzuführen. Dies erlaubt den Vergleich der Systemleistung mit und ohne Leitlinien/Dosistabellen.

## Verwendung

### RAG deaktivieren (Validierungsmodus)

1. Öffne die Datei `backend/.env`
2. Ändere die Zeile:
   ```
   ENABLE_RAG=false
   ```
3. Starte das Backend neu

### RAG aktivieren (Normalmodus)

1. Öffne die Datei `backend/.env`
2. Ändere die Zeile:
   ```
   ENABLE_RAG=true
   ```
3. Starte das Backend neu

## Was passiert bei deaktiviertem RAG?

### Backend-Verhalten

**Das LLM erhält WEITERHIN:**

- ✅ Klinische Parameter (Verdachtsdiagnose, Schweregrad, Verdachtskeim, Risikofaktoren, etc.)
- ✅ Patienteninformationen (Vorerkrankungen, Medikamente, Laborwerte, Allergien, etc.)

**Das LLM erhält NICHT mehr:**

- ❌ Leitlinien-Chunks (Guidelines)
- ❌ Dosierungstabellen
- ❌ Zusatzinformationen (z.B. zu Schwangerschaft, Therapie im Alter, multiresistente Keime, etc.)

### Prompt-Anpassungen

- **System-Prompt:** Weist das LLM darauf hin, dass es im Validierungsmodus läuft und nur auf Basis seines medizinischen Wissens antworten soll
- **User-Prompt:** Enthält keine RAG-Quellen mehr, nur noch klinische Daten und Patienteninfos
- **Quellenangaben:** Werden nicht mehr verlangt (source_citations bleibt leer)

### Frontend-Anzeige

- **Banner:** Ein farbiger Banner zeigt den RAG-Status an:
  - 🟢 **Grün:** "RAG Active" (RAG aktiviert)
  - 🔴 **Rot:** "Validation Mode (RAG Disabled)" (RAG deaktiviert)
- Der Banner kann weggeklickt werden, um nicht zu stören

## Geänderte Dateien

### Backend

1. **`backend/.env`**

   - Neue Variable: `ENABLE_RAG=true`

2. **`backend/therapy_context_builder.py`**

   - Prüft `ENABLE_RAG` beim Initialisieren
   - Überspringt RAG-Suche wenn deaktiviert
   - Lädt keine Zusatzinfos (Alter, multiresistente Keime, etc.)
   - Passt Context-Text automatisch an

3. **`backend/therapy_llm_service.py`**

   - System-Prompt wird dynamisch generiert (unterschiedlich für RAG ein/aus)
   - User-Prompt passt Aufgabenstellung an RAG-Status an
   - Keine Quellenangaben im Validierungsmodus

4. **`backend/main.py`**
   - Neuer Endpunkt: `GET /rag-status` für Frontend-Abfrage

### Frontend

1. **`frontend/src/components/RagStatusBanner/RagStatusBanner.js`**

   - Neue Komponente für Status-Banner
   - Pollt RAG-Status alle 30 Sekunden
   - Kann weggeklickt werden

2. **`frontend/src/components/RagStatusBanner/RagStatusBanner.css`**

   - Styling für grünen/roten Banner
   - Fixed position oben am Bildschirm

3. **`frontend/src/App.js`**

   - Integriert RagStatusBanner-Komponente

4. **`frontend/src/EnduserApp.js`**
   - Integriert RagStatusBanner-Komponente

## Minimale Code-Änderungen

Die Implementierung wurde bewusst minimal gehalten:

- Nur 1 neue Environment-Variable
- RAG-Suche wird einfach übersprungen wenn deaktiviert
- Prompts passen sich automatisch an
- Keine tiefgreifenden Architekturänderungen
- Funktionalität bleibt vollständig intakt (kann jederzeit wieder aktiviert werden)

## Testprozess

### Phase 1: Mit RAG (bereits durchgeführt)

```
ENABLE_RAG=true
```

→ Normale Funktionalität, Leitlinien werden verwendet

### Phase 2: Ohne RAG (für Validierung)

```
ENABLE_RAG=false
```

→ Validierungsmodus, nur LLM-Wissen ohne Leitlinien

### Vergleich

Dokumentiere die Unterschiede in den Therapieempfehlungen zwischen beiden Modi.

## Wichtige Hinweise

- ⚠️ Backend muss neu gestartet werden nach Änderung der `.env`
- ⚠️ Frontend zeigt automatisch den aktuellen Status an
- ⚠️ Im Validierungsmodus sollte `confidence_level` niedriger sein (wird automatisch angepasst)
- ⚠️ Quellenangaben sind im Validierungsmodus nicht erforderlich
