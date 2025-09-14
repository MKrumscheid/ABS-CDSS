from __future__ import annotations
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

# ==== Enums ====
class Severity(str, Enum):
    LIGHT = "LEICHT"
    MODERATE = "MITTELSCHWER" 
    SEVERE = "SCHWER"
    SEPTIC = "SEPTISCH"

class RiskFactor(str, Enum):
    PRIOR_ANTIBIOTICS_3M = "ANTIBIOTISCHE_VORBEHANDLUNG"
    MRGN_SUSPECTED = "MRGN_VERDACHT"
    MRSA_SUSPECTED = "MRSA_VERDACHT"
    VENTILATION = "BEATMUNG"
    CATHETER = "KATHETER"

class Indication(str, Enum):
    CAP = "AMBULANT_ERWORBENE_PNEUMONIE"
    HAP = "NOSOKOMIAL_ERWORBENE_PNEUMONIE"
    AECOPD = "AKUTE_EXAZERBATION_COPD"

class InfectionSite(str, Enum):
    BLOOD = "BLUT"
    LUNG = "LUNGE" 
    GIT = "GASTROINTESTINAL"
    CNS = "ZNS"
    SST = "HAUT_WEICHTEILE"
    UT = "HARNTRAKT"
    SYSTEMIC = "SYSTEMISCH"

# ==== Models ====
class GuidelineMetadata(BaseModel):
    guideline_id: str
    title: str
    version: Optional[str] = None
    year: Optional[int] = None
    indications: List[Indication] = []

class RAGChunk(BaseModel):
    chunk_id: str
    guideline_id: str
    section_path: Optional[str] = None
    page: Optional[int] = None
    kind: Literal["section", "table", "row"] = "section"
    table_id: Optional[str] = None
    snippet: str
    metadata: Dict = {}

class ClinicalQuery(BaseModel):
    indication: Indication
    severity: Severity
    infection_site: Optional[InfectionSite] = None
    risk_factors: List[RiskFactor] = []
    suspected_pathogens: List[str] = []
    free_text: Optional[str] = None

class RAGResult(BaseModel):
    chunk_id: str
    guideline_id: str
    section_path: Optional[str] = None
    page: Optional[int] = None
    snippet: str
    score: float
    metadata: Dict = {}

class DosingTable(BaseModel):
    table_id: str
    table_name: str
    table_html: str
    score: float
    clinical_context: Dict = {}  # indication, severity, infection_site extracted from name

class RAGResponse(BaseModel):
    query: str
    results: List[RAGResult]
    dosing_tables: List[DosingTable] = []  # Top 3 dosing tables
    total_chunks_searched: int
    execution_time_ms: float
    metadata: Optional[Dict[str, Any]] = None  # For warnings and additional info