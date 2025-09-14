# Neue Features: Modell-Wechsel und Leitlinien-Verwaltung

## 🎯 Zusammenfassung der Änderungen

### 1. Flexibles Embedding-Modell

**Problem gelöst**: Hardcodiertes Modell `intfloat/multilingual-e5-large`
**Lösung**: Environment-basierte Konfiguration

#### Was ist neu:

- ✅ Modell wird aus `.env` Datei geladen
- ✅ Standard ist jetzt `NeuML/pubmedbert-base-embeddings` (medizinisch optimiert)
- ✅ Einfacher Modell-Wechsel ohne Code-Änderungen

#### Modell wechseln:

```bash
# In backend/.env ändern:
EMBEDDING_MODEL=NeuML/pubmedbert-base-embeddings

# Oder alternatives Modell:
EMBEDDING_MODEL=intfloat/multilingual-e5-large
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

**Wichtig**: Nach Modell-Wechsel müssen alle Embeddings neu erstellt werden!

### 2. Webbasierte Leitlinien-Verwaltung

**Problem gelöst**: Keine Möglichkeit, vorhandene Leitlinien zu verwalten
**Lösung**: Neuer "Leitlinien Verwalten" Tab

#### Neue Features:

- ✅ Übersicht aller hochgeladenen Leitlinien
- ✅ Einzelne Leitlinien löschen
- ✅ Alle Leitlinien auf einmal löschen
- ✅ Automatische Aktualisierung nach Upload/Löschung

## 🔧 API Änderungen

### Neue Endpoints:

```
GET /guidelines           - Liste aller Leitlinien
DELETE /guidelines/{id}   - Einzelne Leitlinie löschen
DELETE /guidelines        - Alle Leitlinien löschen
```

### Beispiel-Responses:

```json
GET /guidelines:
{
  "success": true,
  "guidelines": [
    {
      "id": "cap_guideline",
      "title": "CAP-Leitlinie.md",
      "indications": ["AMBULANT_ERWORBENE_PNEUMONIE"],
      "pages": 12
    }
  ],
  "total_count": 1,
  "total_chunks": 47
}

DELETE /guidelines/cap_guideline:
{
  "success": true,
  "message": "Successfully deleted guideline 'cap_guideline'",
  "removed_chunks": 47
}
```

## 🎯 Neue Modell-Eigenschaften

### NeuML/pubmedbert-base-embeddings

- **Spezialisierung**: Medizinische Texte (PubMed trainiert)
- **Vorteil**: Besseres Verständnis medizinischer Terminologie
- **Embedding-Größe**: 768 Dimensionen
- **Performance**: Optimiert für biomedizinische Domäne

### Vergleich der Modelle:

| Modell                                   | Domäne    | Größe | Sprachen | Use Case           |
| ---------------------------------------- | --------- | ----- | -------- | ------------------ |
| `NeuML/pubmedbert-base-embeddings`       | Medizin   | 768D  | EN       | Medizinische Texte |
| `intfloat/multilingual-e5-large`         | Universal | 1024D | Multi    | Allgemeine Texte   |
| `sentence-transformers/all-MiniLM-L6-v2` | Universal | 384D  | EN       | Schnell/Klein      |

## 🚀 Workflow für Modell-Wechsel

1. **Stoppe den Server**
2. **Ändere `.env`**:
   ```
   EMBEDDING_MODEL=NeuML/pubmedbert-base-embeddings
   ```
3. **Lösche alle Embeddings** (über Web-UI: "Leitlinien Verwalten" → "ALLE Leitlinien löschen")
4. **Starte Server neu**
5. **Lade Leitlinien erneut hoch**

## 🎨 UI Verbesserungen

### Neuer Tab: "Leitlinien Verwalten"

- **Tabellen-Ansicht**: Übersichtliche Darstellung aller Leitlinien
- **Batch-Operationen**: Alle auf einmal löschen
- **Status-Feedback**: Erfolgs-/Fehlermeldungen
- **Auto-Refresh**: Automatische Aktualisierung der Listen

### Verbesserte Navigation:

```
📁 Leitlinien Upload → 🗂️ Leitlinien Verwalten → 🔍 RAG Search Test
```

## ⚠️ Wichtige Hinweise

1. **Modell-Kompatibilität**: Embeddings verschiedener Modelle sind NICHT kompatibel
2. **Performance**: Medizinische Modelle können langsamer sein als Universal-Modelle
3. **Memory**: Größere Modelle benötigen mehr RAM
4. **Lösch-Warnung**: Gelöschte Leitlinien können nicht wiederhergestellt werden

## 🔍 Nächste Schritte

Nach dem Modell-Wechsel sollten Sie:

1. Test-Uploads mit verschiedenen Leitlinien durchführen
2. Such-Performance mit medizinischen Begriffen testen
3. Embedding-Qualität für deutsche vs. englische Texte vergleichen
4. ggf. weitere medizinische Modelle evaluieren
