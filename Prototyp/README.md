# RAG Test Pipeline - Clinical Decision Support System

## Übersicht

Diese RAG-Testpipeline ermöglicht das Hochladen, Chunking und Indexieren von medizinischen Leitlinien sowie das Testen von Retrieval-Abfragen für die Clinical Decision Support App.

## Features

- Upload von .txt und .md Leitlinien-Dateien
- **Intelligentes Markdown-Chunking**: Seiten-basierte Chunks mit Overlap
- Automatische Extraktion von Tabellen, Headers und Metadaten
- CPU-basierte Embeddings mit BERT
- FAISS Vektordatenbank
- Web-UI für Parameter-Eingabe
- RAG-Query Testing

## Neue Markdown-Features

- **Seitenbasiertes Chunking**: `---` Trennzeichen definieren Seitenumbrüche
- **Overlap-Strategie**: 3 Sätze Überlappung zwischen Seiten für besseren Kontext
- **Metadaten-Extraktion**: Automatische Erkennung von Headers, Tabellen, Therapie-Inhalten
- **Tabellen-Erhaltung**: HTML-Tabellen bleiben intakt in Chunks
- **Struktur-Awareness**: Erkennung von Dosierungen, Medikamenten, Therapieempfehlungen

## Setup

### Backend

```bash
cd backend
pip install -r ../requirements.txt
python main.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Unterstützte Infektionen

- CAP (Ambulant erworbene Pneumonie)
- HAP (Nosokomial erworbene Pneumonie)

## Leitlinien

- 082-006l_S2k_Parenterale_Antibiotika_2019-08-abgelaufen
- 020-020l_S3_Behandlung-von-erwachsenen-Patienten-mit-ambulant-erworbener-Pneumonie\_\_2021-05
