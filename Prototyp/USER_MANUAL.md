# ABS-CDSS - Anwenderhandbuch

## 1. Einführung

Das **Antibiotic Stewardship Clinical Decision Support System (ABS-CDSS)** ist ein intelligentes Assistenzsystem zur Unterstützung bei der Auswahl der optimalen Antibiotikatherapie. Es nutzt modernste KI-Technologie (RAG - Retrieval Augmented Generation) in Kombination mit aktuellen medizinischen Leitlinien, um evidenzbasierte Therapieempfehlungen zu generieren.

Dieses Handbuch beschreibt die Nutzung der beiden Benutzeroberflächen:

1.  **Endnutzer-Oberfläche**: Für klinisches Personal zur täglichen Nutzung.
2.  **Admin-Oberfläche**: Für technisches Personal zur Verwaltung von Leitlinien und Systemüberwachung.

---

## 2. Endnutzer-Oberfläche (Klinik)

Die Endnutzer-Oberfläche ist für den schnellen und intuitiven Einsatz im klinischen Alltag optimiert.

**Zugriff:** Öffnen Sie im Browser `http://localhost:4000`

### 2.1 Hauptmenü

Die Anwendung verfügt über eine einfache Navigation am oberen Bildschirmrand (oder als Seitenleiste):

- **Therapieempfehlung**: Die Hauptansicht zur Eingabe neuer Fälle.
- **Gespeicherte Anfragen**: Historie früherer Abfragen und Empfehlungen.

### 2.2 Neue Therapieempfehlung erstellen

#### Schritt 1: Patientendaten (Optional)

Sie können eine Empfehlung anonym oder patientenbezogen anfordern.

- Klicken Sie auf **"Patient suchen"** (Lupe-Symbol).
- Suchen Sie entweder nach **Patienten-ID** oder nach **Name und Geburtsdatum**.
- Wählen Sie den korrekten Patienten aus der Liste aus.
- _Hinweis: Die Patientendaten werden nur lokal für die Anzeige verwendet und nicht an externe KI-Dienste gesendet._

#### Schritt 2: Klinische Parameter

Füllen Sie das Formular mit den medizinischen Details aus:

- **Indikation**: Wählen Sie die Diagnose aus der Liste (z.B. "Ambulant erworbene Pneumonie"). Die Liste ist nach Kategorien sortiert.
- **Schweregrad**: Leicht, Mittelschwer oder Schwer (Sepsis).
- **Risikofaktoren**: Wählen Sie relevante Faktoren wie "Alter > 65", "Niereninsuffizienz", etc.
- **Erregerverdacht**: (Optional) Falls bereits mikrobiologische Befunde vorliegen.

#### Schritt 3: Freitext & Zusatzinfos

- **Freitext**: Hier können Sie spezifische Details eingeben, die im Formular nicht abgebildet sind (z.B. "Patient hat Penicillin-Allergie").
- **Maximale Therapieoptionen**: Legen Sie fest, wie viele Alternativen angezeigt werden sollen (Standard: 5).

#### Schritt 4: Absenden

Klicken Sie auf **"Therapieempfehlung generieren"**. Das System analysiert nun die Eingaben und konsultiert die hinterlegten Leitlinien. Dies kann einige Sekunden dauern.

### 2.3 Ergebnisse interpretieren

Die Ergebnisseite zeigt Ihnen strukturierte Empfehlungen:

1.  **Empfohlene Antibiotika**:
    - Name des Wirkstoffs.
    - **Dosierung**: Genaue Angaben zu Menge, Frequenz und Dauer.
    - **Begründung**: Warum dieses Antibiotikum gewählt wurde (basierend auf Leitlinien).
2.  **Quellen & Evidenz**:
    - Zu jeder Empfehlung werden die zugrundeliegenden Leitlinien-Auszüge angezeigt.
    - Sie können aufklappen, um den genauen Text der Leitlinie zu lesen.
3.  **Warnhinweise**:
    - Achten Sie auf rote oder gelbe Warnboxen (z.B. bei Kontraindikationen oder Interaktionen).

### 2.4 Speichern & Exportieren

- **Speichern**: Klicken Sie auf das Disketten-Symbol, um den Fall in der lokalen Datenbank zu speichern.
- **Drucken/PDF**: Nutzen Sie die Druckfunktion Ihres Browsers (Strg+P), um einen Bericht zu erstellen.

### 2.5 Gespeicherte Anfragen

Unter dem Menüpunkt "Gespeicherte Anfragen" finden Sie eine chronologische Liste aller gespeicherten Fälle.

- **Ansehen**: Klicken Sie auf das Auge-Symbol, um die Details erneut aufzurufen.
- **Löschen**: Entfernen Sie veraltete Einträge mit dem Mülleimer-Symbol.

---

## 3. Admin-Oberfläche (Verwaltung)

Die Admin-Oberfläche dient der Pflege der Wissensbasis und der Systemüberwachung.

**Zugriff:** Öffnen Sie im Browser `http://localhost:3000`

### 3.1 Dashboard Übersicht

Das Dashboard bietet verschiedene Tabs für unterschiedliche Verwaltungsaufgaben:

- **Upload**: Verwalten von medizinischen Leitlinien.
- **Search Test**: Testen der Suchfunktion (RAG) ohne LLM.
- **System Status**: Überwachung der Dienste.

### 3.2 Leitlinien verwalten (Upload Tab)

Hier pflegen Sie das medizinische Wissen des Systems.

#### Neue Leitlinie hochladen:

1.  Wählen Sie eine Datei aus (PDF, Markdown oder Text).
2.  Geben Sie Metadaten an (Titel, Gültigkeit, Herausgeber).
3.  Klicken Sie auf **"Upload & Process"**.
4.  Das System verarbeitet das Dokument automatisch:
    - Texterkennung (OCR) falls nötig.
    - Aufteilung in Abschnitte (Chunking).
    - Erstellung von Vektor-Embeddings für die Suche.

#### Vorhandene Leitlinien:

- Unten sehen Sie eine Liste aller aktiven Dokumente.
- Sie können veraltete Leitlinien hier löschen. **Achtung:** Dies entfernt das Wissen unwiderruflich aus dem System.

### 3.3 Such-Test (Search Tab)

Dient zur Überprüfung, ob das System die richtigen Textstellen findet.

1.  Geben Sie eine medizinische Frage ein (z.B. "Therapie bei Pneumonie").
2.  Das System zeigt Ihnen die gefundenen Textpassagen aus den Leitlinien an, _ohne_ eine Antwort zu generieren.
3.  Nutzen Sie dies, um zu prüfen, ob neu hochgeladene Leitlinien korrekt indiziert wurden.

### 3.4 Systemstatus

Der Status-Banner (oben rechts) zeigt die Gesundheit der Teilsysteme:

- **RAG Status**: Grün = Bereit, Rot = Fehler im Vektor-Speicher.
- **LLM Status**: Verbindung zur KI (Novita AI).
- **DB Status**: Verbindung zur PostgreSQL Datenbank.

---

## 4. Fehlerbehebung

### Häufige Probleme

**"System antwortet nicht" / Ladebalken bleibt stehen**

- Prüfen Sie im Admin-Dashboard den Systemstatus.
- Starten Sie ggf. das Backend neu (`start_backend_venv.bat`).

**"Keine passenden Leitlinien gefunden"**

- Die Anfrage war zu spezifisch oder es fehlen Leitlinien zu diesem Thema.
- Laden Sie entsprechende Fachinformationen im Admin-Bereich hoch.

**Fehlermeldung beim Speichern**

- Prüfen Sie, ob die Datenbank läuft.
- Stellen Sie sicher, dass alle Pflichtfelder ausgefüllt sind.

---

**Support**
Bei technischen Problemen wenden Sie sich bitte an die IT-Abteilung oder erstellen Sie ein Ticket im GitHub-Repository.
