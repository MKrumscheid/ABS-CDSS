# Expertenfeedback: Strukturierte Query-Generierung

## 🎯 Problem & Lösung

### Ursprüngliches Problem:

- Queries "mischten" Intent (CAP) mit generischen Schlagwörtern
- Trafen auch AECOPD-/HAP-Passagen durch zu allgemeine Begriffe
- Fehlende Struktur bei der Query-Generierung

### Expertenfeedback Umsetzung:

**Strukturierte Query mit MUST/SHOULD/BOOST-Pattern**

## 📋 Neue Query-Struktur

### 1. MUST (Kernkontext/Filter) - Höchste Priorität

**Was**: Hauptindikation und Schweregrad mit Synonymen

```
CAP: ["CAP", "ambulant erworbene Pneumonie", "community-acquired pneumonia", "Pneumonie ambulant"]
HAP: ["HAP", "nosokomial erworbene Pneumonie", "hospital-acquired pneumonia", "Pneumonie nosokomial"]

Schweregrad:
- LEICHT: ["leicht", "mild", "niedriggradig"]
- MITTELSCHWER: ["mittelschwer", "moderat", "moderate", "mäßig"]
- SCHWER: ["schwer", "severe", "hochgradig", "schwerwiegend"]
- SEPTISCH: ["septisch", "septic", "Schock", "kritisch"]
```

### 2. SHOULD (Klinische Besonderheiten) - Mittlere Priorität

**Was**: Risikofaktoren, Infektionsort, Erreger

#### Risikofaktoren mit Synonymen:

```
MRSA_VERDACHT: [
  "MRSA", "methicillin-resistenter Staphylococcus aureus",
  "MRSA-Kolonisation", "methicillin-resistente Erreger"
]

MRGN_VERDACHT: [
  "MRGN", "multiresistente Erreger", "MRE", "ESBL",
  "Extended-Spectrum Beta-Lactamase", "multiresistente Bakterien"
]

ANTIBIOTISCHE_VORBEHANDLUNG: [
  "antibiotische Vorbehandlung", "Antibiotika-Vortherapie",
  "vorherige Antibiotika", "Antibiose Vorbehandlung"
]
```

### 3. BOOST (Therapie/Dosierung/Tabellenanker) - Konstante Verstärkung

**Was**: Immer hinzugefügte Therapie-relevante Begriffe

```
Therapie-Anker:
- "kalkulierte Initialtherapie", "empirisch", "initial"
- "Empfehlung", "Therapie der Wahl", "Behandlung"

Dosierungs-Anker:
- "Dosierung", "Dosis", "Tagesdosis", "Dosierungsempfehlung"
- "mg", "g", "i.v.", "p.o.", "intravenös", "oral"

Tabellen-Anker:
- "Tabelle", "Tab.", "Übersicht", "Schema"

Zielgerichtete Therapie:
- "gezielt", "erregerspezifisch", "Deeskalation"
```

## 🔧 Technische Implementierung

### Query-Generierung mit Gewichtung:

```python
def _build_search_query(self, query: ClinicalQuery) -> str:
    # MUST parts - doppelt für Betonung
    must_parts = self._build_must_query(query)
    query_parts.extend(must_parts)
    query_parts.extend(must_parts)  # Wiederholung für Embedding-Gewichtung

    # SHOULD parts - einmal
    should_parts = self._build_should_query(query)
    query_parts.extend(should_parts)

    # BOOST parts - immer hinzugefügt
    boost_parts = self._build_boost_query()
    query_parts.extend(boost_parts)
```

### Debug-Output:

```
🔍 Query Debug:
  MUST: ['CAP', 'ambulant erworbene Pneumonie', 'mittelschwer', 'moderat']
  SHOULD: ['MRSA', 'methicillin-resistenter Staphylococcus aureus']
  BOOST: ['kalkulierte Initialtherapie', 'empirisch', 'Dosierung', ...]
  FINAL: CAP ambulant erworbene Pneumonie mittelschwer moderat CAP ambulant...
```

## 🧪 Query-Test-Interface

### Neuer API-Endpoint: `/test-query`

**Zweck**: Query-Generierung testen ohne vollständige Suche

**Response-Struktur**:

```json
{
  "status": "success",
  "query_analysis": {
    "input_parameters": { ... },
    "must_terms": ["CAP", "ambulant erworbene Pneumonie", ...],
    "should_terms": ["MRSA", "methicillin-resistenter Staphylococcus aureus", ...],
    "boost_terms": ["kalkulierte Initialtherapie", "Dosierung", ...],
    "final_query": "CAP ambulant erworbene Pneumonie ...",
    "term_counts": {
      "must": 4,
      "should": 8,
      "boost": 23
    }
  }
}
```

### Frontend Query-Test Tab

- **Neuer Tab**: "🧪 Query Test"
- **Funktionen**:
  - Gleiche Parameter wie Search-Tab
  - Zeigt Query-Struktur-Analyse
  - Keine Embedding-Suche, nur Query-Generierung

## 📊 Erwartete Verbesserungen

### Vor der Änderung:

```
Query: "CAP ambulant erworbene Pneumonie mittelschwere Infektion MRSA Verdacht Dosierung Antibiotikum"
Problem: Trifft auch HAP wegen "Pneumonie", trifft AECOPD wegen allgemeiner Begriffe
```

### Nach der Änderung:

```
Query: "CAP ambulant erworbene Pneumonie community-acquired pneumonia CAP ambulant erworbene Pneumonie MRSA methicillin-resistenter Staphylococcus aureus kalkulierte Initialtherapie Dosierung Tabelle"
Vorteil: Spezifischere CAP-Terme, strukturierte Gewichtung, Tabellen-Fokus
```

## 🎯 Vorteile für PubMedBERT

1. **Medizinische Terminologie**: Synonym-Sets nutzen medizinische Fachbegriffe
2. **Strukturierte Gewichtung**: MUST-Terme werden doppelt gewichtet
3. **Kontext-Bewahrung**: SHOULD-Terme geben klinischen Kontext
4. **Dosierungs-Fokus**: BOOST-Terme verankern Therapie-relevante Inhalte
5. **Tabellen-Erkennung**: Explizite "Tabelle"/"Tab."-Terme

## ⚠️ Migration & Testing

### Nach der Implementierung:

1. **Alte Embeddings löschen** (anderes Modell = inkompatible Embeddings)
2. **Leitlinien neu hochladen** mit NeuML/pubmedbert-base-embeddings
3. **Query-Tests durchführen** mit neuem Tab
4. **Suchergebnisse vergleichen** vor/nach der Änderung

### Test-Szenarien:

- CAP + MRSA-Risiko → sollte keine HAP-Treffer
- Dosierungs-Anfragen → sollte Tabellen prioritieren
- Verschiedene Schweregrade → spezifische Synonyme
- Deutsch vs. Englisch → beide Varianten abdecken
