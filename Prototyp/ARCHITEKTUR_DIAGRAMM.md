# ABS-CDSS Architektur-Diagramm

## Systemarchitektur mit Tech-Stack

```mermaid
graph TB
    subgraph "Frontend Layer"
        AdminUI["Admin Frontend<br/>React + Bootstrap<br/>Port: /admin"]
        EnduserUI["Enduser Frontend<br/>React + MUI<br/>Port: /"]
    end

    subgraph "API Layer"
        FastAPI["FastAPI Backend<br/>Python 3.11<br/>Uvicorn ASGI Server<br/>Port: 8000"]
    end

    subgraph "Core Services"
        RAG["RAG Service Advanced<br/>- FAISS IndexFlatIP<br/>- Markdown Page Splitter<br/>- Query Builder (MUST/SHOULD/BOOST)"]

        LLM["LLM Service<br/>- Novita AI API<br/>- OpenAI Compatible<br/>- JSON Schema Response"]

        FHIR["FHIR Service<br/>- HAPI R4B Client<br/>- Resource Parser<br/>- Bundle Aggregation"]

        Context["Therapy Context Builder<br/>- Patient Integration<br/>- Evidence Aggregation<br/>- Prompt Assembly"]

        Embed["Embedding Service<br/>Local: SentenceTransformers<br/>Online: Novita AI<br/>Rate Limiting + Retry"]
    end

    subgraph "Data Layer"
        Guidelines["Leitlinien<br/>Markdown Files<br/>backend/data/guidelines/"]

        DosingTables["Dosistabellen<br/>dosis_tabellen.md<br/>HTML → LLM Format"]

        AdditionalInfo["Additional Info<br/>Sicherheit, MRGN,<br/>Alter, Nierenfunktion"]

        FAISSDB["FAISS Indices<br/>- Guidelines Index<br/>- Dosing Tables Index<br/>embeddings/*.bin"]

        SQLite["SQLite DB<br/>Saved Recommendations<br/>abs_cdss.db"]
    end

    subgraph "External Services"
        NovitaLLM["Novita AI<br/>LLM API<br/>gpt-oss-120b"]

        NovitaEmbed["Novita AI<br/>Embeddings API<br/>qwen3-embedding-8b"]

        HapiFHIR["HAPI FHIR Server<br/>R4B Public<br/>Patient Resources"]
    end

    subgraph "Deployment"
        Docker["Docker Multi-Stage Build<br/>Stage 1: Node 18 Alpine<br/>Stage 2: Python 3.11 Slim"]

        Koyeb["Koyeb Platform<br/>Region: fra<br/>Instance: nano (512Mi RAM)"]
    end

    %% Frontend to API
    AdminUI -->|REST/SSE| FastAPI
    EnduserUI -->|REST/SSE| FastAPI

    %% API to Services
    FastAPI -->|"POST /therapy/recommend"| Context
    FastAPI -->|"POST /upload/guideline"| RAG
    FastAPI -->|"POST /search"| RAG
    FastAPI -->|"POST /patients/search"| FHIR
    FastAPI -->|"POST /therapy/save"| SQLite

    %% Service Dependencies
    Context -->|build_therapy_context| RAG
    Context -->|get_patient_bundle| FHIR
    Context -->|generate_recommendation| LLM

    RAG -->|encode texts| Embed
    RAG -->|search index| FAISSDB
    RAG -->|parse tables| DosingTables
    RAG -->|chunk markdown| Guidelines

    Context -->|load context| AdditionalInfo

    %% External API Calls
    LLM -->|"chat.completions<br/>response_format: json"| NovitaLLM
    Embed -->|"conditional:<br/>USE_ONLINE_EMBEDDINGS"| NovitaEmbed
    FHIR -->|"Bundle query<br/>LOINC parsing"| HapiFHIR

    %% Data Persistence
    RAG -.->|save/load| FAISSDB
    RAG -.->|read| Guidelines
    RAG -.->|parse| DosingTables

    %% Deployment
    Docker -->|"build & package"| FastAPI
    Docker -->|"static builds"| AdminUI
    Docker -->|"static builds"| EnduserUI
    Koyeb -->|"run container"| Docker

    %% Styling
    classDef frontend fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef api fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef service fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef data fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef external fill:#ffe0b2,stroke:#e65100,stroke-width:2px
    classDef deploy fill:#fce4ec,stroke:#880e4f,stroke-width:2px

    class AdminUI,EnduserUI frontend
    class FastAPI api
    class RAG,LLM,FHIR,Context,Embed service
    class Guidelines,DosingTables,AdditionalInfo,FAISSDB,SQLite data
    class NovitaLLM,NovitaEmbed,HapiFHIR external
    class Docker,Koyeb deploy
```

````

## Datenfluss: Therapieempfehlung

```mermaid
sequenceDiagram
    participant UI as Enduser Frontend
    participant API as FastAPI
    participant CTX as Context Builder
    participant RAG as RAG Service
    participant FHIR as FHIR Service
    participant LLM as LLM Service
    participant EMB as Embedding Service
    participant FAISS as FAISS Index
    participant HAPI as HAPI FHIR
    participant Novita as Novita AI

    UI->>+API: POST /therapy/recommend<br/>{indication, severity, risk_factors, patient_id}

    API->>+CTX: build_therapy_context(query, patient_id)

    par Parallel Data Retrieval
        CTX->>+RAG: search(ClinicalQuery, top_k=5)
        RAG->>RAG: _build_search_query<br/>(MUST/SHOULD/BOOST)
        RAG->>+EMB: encode(search_text)
        EMB-->>-RAG: query_embedding
        RAG->>+FAISS: search(query_embedding)
        FAISS-->>-RAG: semantic scores + indices
        RAG->>RAG: _calculate_lexical_boost<br/>(+500/+50 per synonym)
        RAG->>RAG: combine semantic + lexical
        RAG->>RAG: _search_dosing_tables<br/>(+1000/+100 boost)
        RAG-->>-CTX: RAGResponse{results, dosing_tables}
    and
        CTX->>+FHIR: get_patient_bundle(patient_id)
        FHIR->>+HAPI: GET /Patient/{id}?_include=*
        HAPI-->>-FHIR: Bundle{Patient, Condition,<br/>Observation, Medication, Allergy}
        FHIR->>FHIR: parse_patient_data<br/>(LOINC codes, eGFR, demographics)
        FHIR-->>-CTX: PatientData
    end

    CTX->>CTX: _build_context_text<br/>(normalize scores to 0-1)
    CTX->>CTX: add additional_info<br/>(age>70, GFR≤60, MRGN)
    CTX-->>-API: context_data{context_text, patient, sources}

    API->>+LLM: generate_therapy_recommendation<br/>(context_data, max_options=5)
    LLM->>LLM: _build_system_prompt<br/>(JSON schema, German output)
    LLM->>LLM: _build_user_prompt<br/>(context_text + instructions)
    LLM->>+Novita: chat.completions.create<br/>{response_format: json_object}
    Novita-->>-LLM: JSON{therapy_options[], clinical_guidance,<br/>source_citations[], confidence_level}
    LLM->>LLM: _parse_llm_response<br/>(cleanup + Pydantic validation)
    LLM-->>-API: TherapyRecommendation

    API->>API: Transform to frontend format
    API-->>-UI: {therapy_options, clinical_guidance,<br/>source_citations, patient_data, confidence_level}

    UI->>UI: Display TherapyResults<br/>(Relevanz: score×100%)
````

## RAG Query Construction

```mermaid
flowchart LR
    subgraph "Input: ClinicalQuery"
        IND[indication:<br/>AMBULANT_ERWORBENE_PNEUMONIE]
        SEV[severity:<br/>SCHWER]
        RISK[risk_factors:<br/>MRGN_VERDACHT]
        SITE[infection_site:<br/>LUNGE]
        PATH[suspected_pathogens:<br/>MRSA]
        FREE[free_text:<br/>additional notes]
    end

    subgraph "Query Builder"
        MUST["MUST Terms<br/>- Indication synonyms<br/>- Severity synonyms<br/>Example: 'CAP', 'Pneumonie',<br/>'ambulant', 'schwer'"]

        SHOULD["SHOULD Terms<br/>- Risk factor synonyms<br/>- Infection site synonyms<br/>- Pathogens<br/>Example: 'MRGN', 'ESBL',<br/>'pulmonal', 'MRSA'"]

        BOOST["BOOST Terms<br/>- Therapy anchors<br/>- Dosage keywords<br/>Example: 'Therapie',<br/>'Dosierung', 'Tabelle'"]
    end

    subgraph "Search Execution"
        CONCAT[Concatenate:<br/>MUST + SHOULD + BOOST + FREE]
        EMB[Embedding Service:<br/>encode to vector]
        FAISS1[FAISS Search:<br/>Guidelines Index<br/>IndexFlatIP]
        FAISS2[FAISS Search:<br/>Dosing Tables Index<br/>IndexFlatIP]
        LEX1[Lexical Boost:<br/>Chunks +500/+50]
        LEX2[Lexical Boost:<br/>Tables +1000/+100]
        SORT[Sort by final score<br/>Top-K per guideline]
    end

    IND --> MUST
    SEV --> MUST
    RISK --> SHOULD
    SITE --> SHOULD
    PATH --> SHOULD
    FREE --> CONCAT

    MUST --> CONCAT
    SHOULD --> CONCAT
    BOOST --> CONCAT

    CONCAT --> EMB
    EMB --> FAISS1
    EMB --> FAISS2

    FAISS1 --> LEX1
    FAISS2 --> LEX2

    LEX1 --> SORT
    LEX2 --> SORT
```

## Tech Stack Übersicht

```mermaid
mindmap
  root((ABS-CDSS<br/>Tech Stack))
    Frontend
      React 18
      Material UI MUI
      React Router
      Axios
      date-fns
      Bootstrap alt Admin
    Backend
      Python 3.11
      FastAPI 0.104
      Uvicorn ASGI
      Pydantic v2
      aiofiles
    RAG & AI
      FAISS CPU
      SentenceTransformers
      Novita AI API
        LLM gpt-oss-120b
        Embeddings qwen3
      OpenAI SDK compatible
    FHIR
      fhir.resources R4B
      HAPI FHIR Public
      LOINC Codes
    Data & Storage
      SQLite SQLAlchemy
      Markdown Guidelines
      JSON Metadata
      Pickle Cache
    Deployment
      Docker Multi-Stage
        Node 18 Alpine
        Python 3.11 Slim
      Koyeb Platform
        Region Frankfurt
        512Mi RAM nano
      Health Checks
    Dev Tools
      python-dotenv
      psutil monitoring
      requests HTTP
      re regex
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Development"
        DEV_FE["Frontend Dev<br/>npm run start<br/>Port 3000/4000"]
        DEV_BE["Backend Dev<br/>uvicorn main:app<br/>Port 8000"]
    end

    subgraph "Docker Build"
        STAGE1["Stage 1: Frontend Builder<br/>node:18-alpine<br/>- npm ci<br/>- Build Admin PUBLIC_URL=/admin<br/>- Build Enduser PUBLIC_URL=/"]

        STAGE2["Stage 2: Production<br/>python:3.11-slim<br/>- pip install requirements-prod.txt<br/>- Copy backend code<br/>- Copy frontend builds → static/<br/>- Create non-root user"]
    end

    subgraph "Koyeb Deployment"
        BUILD["Koyeb Builder<br/>- Clone from Git<br/>- docker build -f Dockerfile<br/>- Push to registry"]

        RUNTIME["Runtime Container<br/>- uvicorn main:app<br/>- --host 0.0.0.0<br/>- --port 8000<br/>- --workers 1<br/>- Health check /health"]
    end

    subgraph "Environment Variables"
        ENV["Production Config<br/>USE_ONLINE_EMBEDDINGS=true<br/>NOVITA_API_KEY=***<br/>EMBEDDING_REQUESTS_PER_MINUTE=45<br/>NOVITA_MODEL=gpt-oss-120b<br/>CHUNK_SIZE=8000<br/>LOG_LEVEL=INFO"]
    end

    subgraph "Static Serving"
        ADMIN_STATIC["Static Mount<br/>/admin → backend/static/admin<br/>/admin/static → assets"]

        ENDUSER_STATIC["Static Mount<br/>/ → backend/static/enduser<br/>/static → assets"]
    end

    DEV_FE -.->|npm run build| STAGE1
    DEV_BE -.->|copy src| STAGE2

    STAGE1 -->|admin-build<br/>enduser-build| STAGE2
    STAGE2 -->|Docker Image| BUILD

    BUILD -->|Deploy| RUNTIME
    ENV -->|Configure| RUNTIME

    RUNTIME -->|Serve| ADMIN_STATIC
    RUNTIME -->|Serve| ENDUSER_STATIC

    RUNTIME -->|REST API| API_ROUTES["/therapy/*<br/>/patients/*<br/>/upload/*<br/>/search"]
```

## Komponenten-Interaktion

```mermaid
graph TD
    subgraph "Frontend Components"
        TRF[TherapyRequestForm<br/>- Dropdown selections<br/>- Patient search<br/>- Form validation]

        TR[TherapyResults<br/>- Therapy options display<br/>- Source citations<br/>- Patient summary]

        SR[SavedRequests<br/>- List view<br/>- Detail dialog<br/>- Delete actions]

        SDL[SaveRecommendationDialog<br/>- Title input<br/>- Save confirmation]
    end

    subgraph "API Service Layer"
        APIJS[api.js<br/>- therapyAPI.*<br/>- patientAPI.*<br/>- Axios client<br/>- SSE handling]
    end

    subgraph "Backend Endpoints"
        TE["/therapy/recommend<br/>/therapy/recommend-stream"]
        PE["/patients/search<br/>/patients/{id}"]
        SE["/therapy/save<br/>/therapy/saved"]
    end

    subgraph "Backend Services"
        TCB[TherapyContextBuilder]
        RAGS[RAGService]
        FHIRS[FHIRService]
        LLMS[LLMService]
    end

    TRF -->|formData| APIJS
    APIJS -->|POST| TE
    TE -->|orchestrate| TCB

    TCB -->|search| RAGS
    TCB -->|get_patient| FHIRS
    TCB -->|generate| LLMS

    TE -->|response| APIJS
    APIJS -->|therapyRecommendation| TR

    TR -->|save click| SDL
    SDL -->|POST| SE

    SR -->|GET| SE
    SE -->|SQLite query| DB[(abs_cdss.db)]

    APIJS -->|GET/POST| PE
    PE -->|FHIR calls| FHIRS
```

## Pydantic Datenmodelle

### Therapy Recommendation Modelle

```mermaid
classDiagram
    class TherapyRecommendation {
        +List~MedicationRecommendation~ therapy_options
        +ClinicalGuidance clinical_guidance
        +List~SourceCitation~ source_citations
        +str therapy_rationale
        +str confidence_level
        +List~str~ warnings
        +str system_prompt
        +str user_prompt
        +str llm_model
    }

    class MedicationRecommendation {
        +List~ActiveIngredient~ active_ingredients
        +str notes
        +ClinicalGuidance clinical_guidance
    }

    class ActiveIngredient {
        +str name
        +str strength
        +int frequency_lower_bound
        +int frequency_upper_bound
        +str frequency_unit
        +int duration_lower_bound
        +int duration_upper_bound
        +str duration_unit
        +str route
    }

    class ClinicalGuidance {
        +List~str~ monitoring_parameters
        +List~str~ relevant_side_effects
        +List~str~ drug_interactions
        +str pregnancy_considerations
        +str deescalation_focus_info
    }

    class SourceCitation {
        +str guideline_id
        +str guideline_title
        +int page_number
        +str section
        +float relevance_score
    }

    TherapyRecommendation "1" *-- "1..5" MedicationRecommendation
    TherapyRecommendation "1" *-- "0..1" ClinicalGuidance
    TherapyRecommendation "1" *-- "*" SourceCitation
    MedicationRecommendation "1" *-- "1..4" ActiveIngredient
    MedicationRecommendation "1" *-- "0..1" ClinicalGuidance
```

### Query und RAG Modelle

```mermaid
classDiagram
    class ClinicalQuery {
        +Indication indication
        +Severity severity
        +InfectionSite infection_site
        +List~RiskFactor~ risk_factors
        +List~str~ suspected_pathogens
        +str free_text
    }

    class RAGResponse {
        +str query
        +List~RAGResult~ results
        +List~DosingTable~ dosing_tables
        +int total_chunks_searched
        +float execution_time_ms
        +Dict metadata
    }

    class RAGResult {
        +str chunk_id
        +str guideline_id
        +str section_path
        +int page
        +str snippet
        +float score
        +Dict metadata
    }

    class DosingTable {
        +str table_id
        +str table_name
        +str table_html
        +float score
        +Dict clinical_context
    }

    class Indication {
        <<enumeration>>
        CAP
        HAP
        AECOPD
        SEPSIS
        BACTERIAL_MENINGITIS
        +get_display_name() str
        +get_synonyms() List~str~
        +get_category() str
    }

    class Severity {
        <<enumeration>>
        LIGHT
        MODERATE
        SEVERE
        SEPTIC
        +get_display_name() str
        +get_synonyms() List~str~
    }

    class RiskFactor {
        <<enumeration>>
        PRIOR_ANTIBIOTICS_3M
        MRGN_SUSPECTED
        MRSA_SUSPECTED
        VENTILATION
        CATHETER
    }

    class InfectionSite {
        <<enumeration>>
        BLOOD
        LUNG
        GIT
        CNS
        SST
        UT
        SYSTEMIC
    }

    ClinicalQuery --> Indication
    ClinicalQuery --> Severity
    ClinicalQuery --> InfectionSite
    ClinicalQuery --> RiskFactor
    RAGResponse "1" *-- "*" RAGResult
    RAGResponse "1" *-- "0..3" DosingTable
```

### FHIR Patient Modelle

```mermaid
classDiagram
    class PatientSearchQuery {
        +str search_type
        +str patient_id
        +str given_name
        +str family_name
        +str birth_date
    }

    class PatientSearchResult {
        +str patient_id
        +str name
        +str gender
        +str birth_date
        +int age
    }

    class PatientDetailData {
        +str patient_id
        +str name
        +str gender
        +int age
        +str birth_date
        +float height
        +float weight
        +float bmi
        +str pregnancy_status
        +List~str~ conditions
        +List~str~ allergies
        +List~str~ medications
        +List~LabValue~ lab_values
    }

    class LabValue {
        +str name
        +str value
        +str unit
        +str code
    }

    PatientDetailData "1" *-- "*" LabValue
```

### Request/Response Workflow

```mermaid
classDiagram
    class TherapyRecommendationRequest {
        +ClinicalQuery clinical_query
        +str patient_id
        +int max_therapy_options
        +bool include_alternative_options
    }

    class SaveTherapyRecommendationRequest {
        +str title
        +dict request_data
        +dict therapy_recommendation
        +dict patient_data
    }

    class SavedTherapyRecommendationResponse {
        +int id
        +str title
        +datetime created_at
        +dict request_data
        +dict therapy_recommendation
        +dict patient_data
    }

    class SavedTherapyRecommendationListItem {
        +int id
        +str title
        +datetime created_at
        +str indication_display
        +str patient_id
    }

    TherapyRecommendationRequest --> ClinicalQuery
    TherapyRecommendationRequest ..> TherapyRecommendation : generates
    SaveTherapyRecommendationRequest ..> SavedTherapyRecommendationResponse : creates
    SavedTherapyRecommendationResponse --> SavedTherapyRecommendationListItem : summary
```

### Guideline Metadata

```mermaid
classDiagram
    class GuidelineMetadata {
        +str guideline_id
        +str title
        +str version
        +int year
        +List~Indication~ indications
    }

    class RAGChunk {
        +str chunk_id
        +str guideline_id
        +str section_path
        +int page
        +str kind
        +str table_id
        +str snippet
        +Dict metadata
    }

    GuidelineMetadata "1" --> "*" Indication
    RAGChunk --> GuidelineMetadata : references
```

## Use Case Diagramm

### Hinweis zu UML-Stereotypen:

- **`<<include>>`** = Zwingend benötigte Beziehung (Use Case A benötigt Use Case B)
- **`<<extend>>`** = Optionale Erweiterung (Use Case B erweitert optional Use Case A)

### Gesamtsystem Use Cases

```mermaid
graph TB
    %% Akteure
    Arzt["Arzt/Ärztin"]
    Admin["Administrator"]
    System["Backend System"]

    %% Enduser Use Cases
    UC1["Patientensuche"]
    UC2["Patientendaten abrufen"]
    UC3["Therapieempfehlung anfordern"]
    UC4["Empfehlung speichern"]
    UC5["Gespeicherte Empfehlungen anzeigen"]
    UC6["Gespeicherte Empfehlung löschen"]

    %% Admin Use Cases
    UC7["Leitlinien hochladen"]
    UC8["Leitlinien verwalten"]
    UC9["Patientensuche testen"]
    UC10["Query-Erstellung testen"]
    UC11["RAG-Suche testen"]
    UC12["Therapieanfrage testen"]
    UC13["Einstellungen verwalten"]

    %% System Use Cases
    UC14["RAG-Suche durchführen"]
    UC15["FHIR-Daten abrufen"]
    UC16["LLM-Inference ausführen"]
    UC17["Kontext aggregieren"]
    UC18["Dosierungstabellen suchen"]
    UC19["Embeddings generieren"]
    UC20["Scores berechnen"]

    %% Enduser Verbindungen
    Arzt --> UC1
    Arzt --> UC3
    Arzt --> UC5
    Arzt --> UC6

    %% Admin Verbindungen
    Admin --> UC7
    Admin --> UC8
    Admin --> UC9
    Admin --> UC10
    Admin --> UC11
    Admin --> UC12
    Admin --> UC13

    %% Enduser Use Case Dependencies
    UC1 -.->|include| UC2
    UC3 -.->|include| UC2
    UC3 -.->|include| UC14
    UC3 -.->|include| UC15
    UC3 -.->|include| UC17
    UC3 -.->|include| UC16
    UC3 -.->|extend| UC4
    UC5 -.->|include| UC2

    %% Admin Use Case Dependencies
    UC7 -.->|include| UC19
    UC8 -.->|include| UC2
    UC9 -.->|include| UC2
    UC10 -.->|include| UC14
    UC11 -.->|include| UC14
    UC12 -.->|include| UC2
    UC12 -.->|include| UC14
    UC12 -.->|include| UC15
    UC12 -.->|include| UC17
    UC12 -.->|include| UC16

    %% System Dependencies
    UC14 -.->|include| UC19
    UC14 -.->|include| UC18
    UC14 -.->|include| UC20
    UC17 -.->|include| UC14
    UC17 -.->|include| UC15

    %% System führt interne Use Cases aus
    System -.-> UC14
    System -.-> UC15
    System -.-> UC16
    System -.-> UC17
    System -.-> UC18
    System -.-> UC19
    System -.-> UC20

    %% Styling
    classDef actorStyle fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    classDef enduserUC fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef adminUC fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef systemUC fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px

    class Arzt,Admin,System actorStyle
    class UC1,UC2,UC3,UC4,UC5,UC6 enduserUC
    class UC7,UC8,UC9,UC10,UC11,UC12,UC13 adminUC
    class UC14,UC15,UC16,UC17,UC18,UC19,UC20 systemUC
```

### Detaillierter Use Case: Therapieempfehlung anfordern

```mermaid
sequenceDiagram
    actor Arzt as Arzt
    participant UI as Enduser Frontend
    participant API as Backend API
    participant RAG as RAG Service
    participant FHIR as FHIR Service
    participant LLM as LLM Service

    Note over Arzt,LLM: Use Case: Therapieempfehlung anfordern

    Arzt->>UI: Gibt klinische Parameter ein<br/>(Indikation, Schweregrad, etc.)
    Arzt->>UI: Sucht Patient
    UI->>API: GET /patients/search
    API->>FHIR: Patientensuche
    FHIR-->>API: Suchergebnisse
    API-->>UI: Liste von Patienten
    UI-->>Arzt: Zeigt Patienten an

    Arzt->>UI: Wählt Patient aus
    Arzt->>UI: Fordert Empfehlung an

    UI->>API: POST /therapy/recommend<br/>{query, patient_id}

    Note over API,LLM: Parallel: RAG + FHIR

    par RAG-Suche
        API->>RAG: search(ClinicalQuery)
        RAG->>RAG: Query-Building<br/>(MUST/SHOULD/BOOST)
        RAG->>RAG: Semantic Search (FAISS)
        RAG->>RAG: Lexical Boosting
        RAG->>RAG: Dosierungstabellen-Suche
        RAG-->>API: RAGResponse<br/>(Chunks + Tables)
    and FHIR-Abruf
        API->>FHIR: get_patient_bundle(id)
        FHIR->>FHIR: FHIR Bundle aggregieren
        FHIR->>FHIR: LOINC-Codes parsen
        FHIR-->>API: PatientData<br/>(Labs, Meds, Conditions)
    end

    API->>API: Kontext aggregieren<br/>(RAG + Patient + Additional Info)
    API->>LLM: generate_recommendation<br/>(Context)
    LLM->>LLM: Prompt-Building<br/>(System + User)
    LLM->>LLM: LLM Inference<br/>(Novita AI)
    LLM->>LLM: JSON Parsing<br/>(Pydantic Validation)
    LLM-->>API: TherapyRecommendation

    API-->>UI: Response<br/>(Options + Guidance + Sources)
    UI-->>Arzt: Zeigt Empfehlung an

    alt Arzt möchte speichern
        Arzt->>UI: Klickt "Speichern"
        UI->>API: POST /therapy/save
        API->>API: SQLite Insert
        API-->>UI: Saved ID
        UI-->>Arzt: Bestätigung
    end
```

### Use Case: Leitlinien hochladen (Admin)

```mermaid
sequenceDiagram
    actor Admin as Administrator
    participant UI as Admin Frontend
    participant API as Backend API
    participant RAG as RAG Service
    participant Embed as Embedding Service
    participant FAISS as FAISS Index

    Note over Admin,FAISS: Use Case: Leitlinien hochladen

    Admin->>UI: Wählt Markdown-Datei
    Admin->>UI: Gibt Metadaten ein<br/>(Title, Indikationen)
    Admin->>UI: Klickt "Upload"

    UI->>API: POST /upload/guideline<br/>(file + metadata)

    API->>RAG: process_guideline(file, metadata)

    RAG->>RAG: Markdown parsen<br/>(Überschriften-Hierarchie)
    RAG->>RAG: Text chunking<br/>(MarkdownPageSplitter)
    RAG->>RAG: Dosierungstabellen extrahieren<br/>(HTML-Parsing)

    loop Für jeden Chunk
        RAG->>Embed: encode(chunk_text)
        alt Online-Embeddings
            Embed->>Embed: Rate Limiting Check<br/>(45 req/min)
            Embed->>Embed: Novita API Call<br/>(qwen3-embedding-8b)
        else Local-Embeddings
            Embed->>Embed: SentenceTransformers<br/>(Local Model)
        end
        Embed-->>RAG: embedding_vector
        RAG->>FAISS: add_vector(embedding)
    end

    RAG->>RAG: Metadata speichern<br/>(guidelines_metadata.json)
    RAG->>RAG: Index persistieren<br/>(faiss_index.bin)
    RAG-->>API: Success + Statistics

    API-->>UI: Upload-Bestätigung<br/>(Chunks, Tables, Time)
    UI-->>Admin: Zeigt Ergebnis an

    Admin->>UI: Optional: Test-Suche
    UI->>API: POST /search<br/>(test query)
    API->>RAG: search(query)
    RAG-->>API: Results
    API-->>UI: Search Results
    UI-->>Admin: Zeigt Relevanz-Scores
```

### Use Case: Einstellungen verwalten (Admin)

```mermaid
sequenceDiagram
    actor Admin as Administrator
    participant UI as Admin Frontend
    participant API as Backend API
    participant Config as Configuration

    Note over Admin,Config: Use Case: Einstellungen verwalten

    Admin->>UI: Öffnet Einstellungen
    UI->>API: GET /settings
    API->>Config: Lade aktuelle Konfiguration
    Config-->>API: LLM-Modell, Embedding-Service, etc.
    API-->>UI: Settings-Response
    UI-->>Admin: Zeigt Einstellungen an

    Admin->>UI: Wählt LLM-Modell<br/>(z.B. gpt-oss-120b)
    Admin->>UI: Konfiguriert Parameter<br/>(Temperature, Max Tokens)
    Admin->>UI: Speichert Änderungen

    UI->>API: POST /settings<br/>{llm_model, temperature, ...}
    API->>Config: Validiere und speichere
    Config->>Config: Update Environment/Config
    Config-->>API: Success

    API-->>UI: Bestätigung
    UI-->>Admin: "Einstellungen gespeichert"

    opt Admin testet neue Einstellungen
        Admin->>UI: "Therapieanfrage testen"
        UI->>API: POST /test/therapy
        API->>API: Verwende neue LLM-Konfiguration
        API-->>UI: Test-Ergebnis
        UI-->>Admin: Zeigt Test-Response
    end
```

### Use Case Matrix

```mermaid
graph TB
    %% Akteure
    A1["Arzt/Ärztin"]
    A2["Administrator"]

    %% Use Case Kategorien
    UC_ENDUSER["Enduser Use Cases:<br/>- Patientensuche<br/>- Therapieempfehlung anfordern<br/>- Empfehlung speichern<br/>- Gespeicherte anzeigen<br/>- Empfehlung löschen"]

    UC_ADMIN_TEST["Admin Test Use Cases:<br/>- Patientensuche testen<br/>- Query-Erstellung testen<br/>- RAG-Suche testen<br/>- Therapieanfrage testen"]

    UC_ADMIN_MGMT["Admin Management:<br/>- Leitlinien hochladen<br/>- Leitlinien verwalten<br/>- Einstellungen verwalten"]

    %% Beziehungen
    A1 -->|Vollzugriff| UC_ENDUSER
    A1 -.->|Kein Zugriff| UC_ADMIN_TEST
    A1 -.->|Kein Zugriff| UC_ADMIN_MGMT

    A2 -->|Lesezugriff| UC_ENDUSER
    A2 -->|Vollzugriff| UC_ADMIN_TEST
    A2 -->|Vollzugriff| UC_ADMIN_MGMT

    %% Styling
    classDef actor fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef enduser fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef adminTest fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef adminMgmt fill:#fce4ec,stroke:#c2185b,stroke-width:2px

    class A1,A2 actor
    class UC_ENDUSER enduser
    class UC_ADMIN_TEST adminTest
    class UC_ADMIN_MGMT adminMgmt
```

### Use Case Übersicht nach Akteur

#### Arzt/Ärztin (Enduser)

| Use Case                           | Beschreibung                                           | Zugriff        |
| ---------------------------------- | ------------------------------------------------------ | -------------- |
| Patientensuche                     | Patient nach ID oder Name/Geburtsdatum suchen          | ✅ Vollzugriff |
| Therapieempfehlung anfordern       | Klinische Parameter eingeben und Empfehlung generieren | ✅ Vollzugriff |
| Empfehlung speichern               | Angezeigte Therapieempfehlung in Datenbank speichern   | ✅ Vollzugriff |
| Gespeicherte Empfehlungen anzeigen | Liste aller gespeicherten Empfehlungen abrufen         | ✅ Vollzugriff |
| Gespeicherte Empfehlung löschen    | Einzelne gespeicherte Empfehlung entfernen             | ✅ Vollzugriff |

#### Administrator

| Use Case                | Beschreibung                                 | Zugriff        |
| ----------------------- | -------------------------------------------- | -------------- |
| **Management**          |                                              |                |
| Leitlinien hochladen    | Markdown-Leitlinien hochladen und indexieren | ✅ Vollzugriff |
| Leitlinien verwalten    | Hochgeladene Leitlinien anzeigen und löschen | ✅ Vollzugriff |
| Einstellungen verwalten | LLM-Modell und Parameter konfigurieren       | ✅ Vollzugriff |
| **Testing**             |                                              |                |
| Patientensuche testen   | FHIR-Patientensuche durchführen              | ✅ Vollzugriff |
| Query-Erstellung testen | ClinicalQuery-Aufbau und Synonyme prüfen     | ✅ Vollzugriff |
| RAG-Suche testen        | Semantische und lexikalische Suche testen    | ✅ Vollzugriff |
| Therapieanfrage testen  | Kompletten Workflow end-to-end testen        | ✅ Vollzugriff |
| **Enduser-Funktionen**  |                                              |                |
| Alle Enduser Use Cases  | Zugriff auf Therapieempfehlungen             | ⚠️ Lesezugriff |

---

**Legende:**

- **Blaue Boxen**: Frontend-Komponenten (React)
- **Gelbe Boxen**: API-Layer (FastAPI)
- **Violette Boxen**: Core Services (Python)
- **Grüne Boxen**: Datenschicht (Files, DB, FAISS)
- **Orange Boxen**: Externe Services (Novita, HAPI)
- **Rosa Boxen**: Deployment-Infrastruktur (Docker, Koyeb)
