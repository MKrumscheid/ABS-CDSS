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
    
    def get_display_name(self) -> str:
        """Get human-readable display name for the severity"""
        display_names = {
            "LEICHT": "Leicht",
            "MITTELSCHWER": "Mittelschwer",
            "SCHWER": "Schwer", 
            "SEPTISCH": "Septisch"
        }
        return display_names.get(self.value, self.value)
    
    def get_synonyms(self) -> List[str]:
        """Get search synonyms for this severity"""
        synonyms = {
            "LEICHT": ["leicht", "mild", "niedriggradig"],
            "MITTELSCHWER": ["mittelschwer", "moderat", "moderate", "mäßig"],
            "SCHWER": ["schwer", "severe", "hochgradig", "schwerwiegend"],
            "SEPTISCH": ["septisch", "Schock"]
        }
        return synonyms.get(self.value, [self.value])

class RiskFactor(str, Enum):
    PRIOR_ANTIBIOTICS_3M = "ANTIBIOTISCHE_VORBEHANDLUNG"
    MRGN_SUSPECTED = "MRGN_VERDACHT"
    MRSA_SUSPECTED = "MRSA_VERDACHT"
    VENTILATION = "BEATMUNG"
    CATHETER = "KATHETER"

class Indication(str, Enum):
    # Existing diagnoses
    CAP = "AMBULANT_ERWORBENE_PNEUMONIE"
    HAP = "NOSOKOMIAL_ERWORBENE_PNEUMONIE"
    AECOPD = "AKUTE_EXAZERBATION_COPD"
    
    # New diagnoses - alphabetically organized
    ACUTE_EPIDIDYMITIS = "AKUTE_EPIDIDYMITIS"
    ACUTE_PROSTATITIS = "AKUTE_PROSTATITIS"
    ACUTE_UNCOMPLICATED_PYELONEPHRITIS = "AKUTE_UNKOMPLIZIERTE_PYELONEPHRITIS"
    BACTERIAL_ARTHRITIS = "BAKTERIELLE_ARTHRITIS"
    BACTERIAL_ENDOCARDITIS = "BAKTERIELLE_ENDOKARDITIS"
    BACTERIAL_GASTROINTESTINAL_INFECTIONS = "BAKTERIELLE_GASTROINTESTINALE_INFEKTIONEN"
    BACTERIAL_MENINGITIS = "BAKTERIELLE_MENINGITIS"
    BACTERIAL_SINUSITIS_AND_COMPLICATIONS = "BAKTERIELLE_SINUSITIDEN_UND_KOMPLIKATIONEN"
    ENDOMETRITIS = "ENDOMETRITIS"
    ENDOPROSTHESIS_FOREIGN_BODY_INFECTIONS = "ENDOPROTHESEN_FREMDKOERPER_ASSOZIIERTE_INFEKTIONEN"
    EPIDIDYMO_ORCHITIS = "EPIDIDYMOORCHITIS"
    EPIGLOTTITIS = "EPIGLOTTITIS"
    HEMATOGENOUS_OSTEOMYELITIS = "HAEMATOGENE_OSTEOMYELITIS"
    INFECTED_BITE_WOUNDS = "INFIZIERTE_BISSWUNDEN"
    INVASIVE_INTRAABDOMINAL_MYCOSES = "INVASIVE_INTRAABDOMINELLE_MYKOSEN"
    COMPLICATED_NOSOCOMIAL_UTI = "KOMPLIZIERTE_NOSOKOMIALE_HARNWEGSINFEKTION"
    MASTOIDITIS = "MASTOIDITIS"
    NASAL_FURUNCLE = "NASENFURUNKEL"
    NECROTIZING_PANCREATITIS_INFECTED_NECROSIS = "NEKROTISIERENDE_PANKREATITIS_INFIZIERTE_NEKROSEN"
    ODONTOGENIC_INFECTIONS_SPREADING = "ODONTOGENE_INFEKTIONEN_AUSBREITUNGSTENDENZ"
    AURICULAR_PERICHONDRITIS = "OHRMUSCHELPERICHONDRITIS"
    JAW_OSTEOMYELITIS = "OSTEOMYELITIS_KIEFER"
    SKULL_BASE_OSTEOMYELITIS = "OSTEOMYELITIS_SCHAEDELBASIS"
    MALIGNANT_OTITIS_EXTERNA = "OTITIS_EXTERNA_MALIGNA"
    PELVEOPERITONITIS = "PELVEOPERITONITIS"
    PERITONITIS = "PERITONITIS"
    PERITONSILLITIS = "PERITONSILLITIS"
    PERITONSILLAR_ABSCESS = "PERITONSILLARABSZESS"
    POSTTRAUMATIC_POSTOPERATIVE_OSTEOMYELITIS = "POSTTRAUMATISCHE_POSTOPERATIVE_OSTEOMYELITIS"
    PROSTATE_ABSCESS = "PROSTATAABSZESS"
    SALPINGITIS = "SALPINGITIS"
    SEPSIS = "SEPSIS"
    SIALADENITIS = "SIALADENITIS"
    SPONDYLODISCITIS = "SPONDYLODISCITIS"
    STERNAL_OSTEOMYELITIS = "STERNUMOSTEOMYELITIS"
    TUBO_OVARIAN_ABSCESS = "TUBOOVARIALABSZESS"
    UROSEPSIS = "UROSEPSIS"
    CERVICOFACIAL_ACTINOMYCOSIS = "ZERVIKOFAZIALE_AKTINOMYKOSE"
    
    def get_display_name(self) -> str:
        """Get human-readable display name for the indication"""
        display_names = {
            # Existing
            "AMBULANT_ERWORBENE_PNEUMONIE": "CAP (Ambulant erworbene Pneumonie)",
            "NOSOKOMIAL_ERWORBENE_PNEUMONIE": "HAP (Nosokomial erworbene Pneumonie)", 
            "AKUTE_EXAZERBATION_COPD": "AECOPD (Akute Exazerbation der COPD)",
            
            # HNO-Infektionen
            "OTITIS_EXTERNA_MALIGNA": "Otitis externa maligna",
            "OSTEOMYELITIS_SCHAEDELBASIS": "Osteomyelitis der Schädelbasis",
            "MASTOIDITIS": "Mastoiditis",
            "EPIGLOTTITIS": "Epiglottitis",
            "OHRMUSCHELPERICHONDRITIS": "Ohrmuschelperichondritis", 
            "NASENFURUNKEL": "Nasenfurunkel",
            "PERITONSILLITIS": "Peritonsillitis",
            "PERITONSILLARABSZESS": "Peritonsillarabszess",
            "BAKTERIELLE_SINUSITIDEN_UND_KOMPLIKATIONEN": "Bakterielle Sinusitiden und deren Komplikationen",
            "SIALADENITIS": "Sialadenitis",
            "ZERVIKOFAZIALE_AKTINOMYKOSE": "Zervikofaziale Aktinomykose",
            
            # Dental
            "ODONTOGENE_INFEKTIONEN_AUSBREITUNGSTENDENZ": "Odontogene Infektionen mit Ausbreitungstendenz",
            "OSTEOMYELITIS_KIEFER": "Osteomyelitis der Kiefer",
            
            # Abdominale Infektionen
            "PERITONITIS": "Peritonitis",
            "NEKROTISIERENDE_PANKREATITIS_INFIZIERTE_NEKROSEN": "Nekrotisierende Pankreatitis mit infizierten Nekrosen",
            "INVASIVE_INTRAABDOMINELLE_MYKOSEN": "Invasive intraabdominelle Mykosen",
            
            # Urogenitale Infektionen
            "AKUTE_UNKOMPLIZIERTE_PYELONEPHRITIS": "Akute unkomplizierte Pyelonephritis",
            "KOMPLIZIERTE_NOSOKOMIALE_HARNWEGSINFEKTION": "Komplizierte bzw. nosokomiale Harnwegsinfektion",
            "UROSEPSIS": "Urosepsis",
            "AKUTE_PROSTATITIS": "Akute Prostatitis",
            "PROSTATAABSZESS": "Prostataabszess",
            "AKUTE_EPIDIDYMITIS": "Akute Epididymitis",
            "EPIDIDYMOORCHITIS": "Epididymoorchitis",
            "ENDOMETRITIS": "Endometritis",
            "SALPINGITIS": "Salpingitis",
            "TUBOOVARIALABSZESS": "Tuboovarialabszess",
            "PELVEOPERITONITIS": "Pelveoperitonitis",
            
            # Haut und Weichteile
            "INFIZIERTE_BISSWUNDEN": "Infizierte Bisswunden",
            
            # Knochen und Gelenke
            "HAEMATOGENE_OSTEOMYELITIS": "Hämatogene Osteomyelitis",
            "SPONDYLODISCITIS": "Spondylodiscitis",
            "POSTTRAUMATISCHE_POSTOPERATIVE_OSTEOMYELITIS": "Posttraumatische/postoperative Osteomyelitis",
            "STERNUMOSTEOMYELITIS": "Sternumosteomyelitis",
            "BAKTERIELLE_ARTHRITIS": "Bakterielle Arthritis",
            "ENDOPROTHESEN_FREMDKOERPER_ASSOZIIERTE_INFEKTIONEN": "Endoprothesen-/Fremdkörper-assoziierte Infektionen",
            
            # Systemische Infektionen
            "SEPSIS": "Sepsis",
            "BAKTERIELLE_ENDOKARDITIS": "Bakterielle Endokarditis",
            "BAKTERIELLE_MENINGITIS": "Bakterielle Meningitis",
            
            # Gastrointestinale Infektionen
            "BAKTERIELLE_GASTROINTESTINALE_INFEKTIONEN": "Bakterielle gastrointestinale Infektionen"
        }
        return display_names.get(self.value, self.value)
    
    def get_synonyms(self) -> List[str]:
        """Get search synonyms for this indication using external synonyms dictionary"""
        from synonyms import get_synonyms_for_indication
        return get_synonyms_for_indication(self.value)
    
    def get_category(self) -> str:
        """Get the medical category for this indication"""
        categories = {
            # Respiratorische Infektionen
            "AMBULANT_ERWORBENE_PNEUMONIE": "Respiratorische Infektionen",
            "NOSOKOMIAL_ERWORBENE_PNEUMONIE": "Respiratorische Infektionen",
            "AKUTE_EXAZERBATION_COPD": "Respiratorische Infektionen",
            
            # HNO-Infektionen
            "OTITIS_EXTERNA_MALIGNA": "HNO-Infektionen",
            "OSTEOMYELITIS_SCHAEDELBASIS": "HNO-Infektionen",
            "MASTOIDITIS": "HNO-Infektionen",
            "EPIGLOTTITIS": "HNO-Infektionen",
            "OHRMUSCHELPERICHONDRITIS": "HNO-Infektionen",
            "NASENFURUNKEL": "HNO-Infektionen",
            "PERITONSILLITIS": "HNO-Infektionen",
            "PERITONSILLARABSZESS": "HNO-Infektionen",
            "BAKTERIELLE_SINUSITIDEN_UND_KOMPLIKATIONEN": "HNO-Infektionen",
            "SIALADENITIS": "HNO-Infektionen",
            "ZERVIKOFAZIALE_AKTINOMYKOSE": "HNO-Infektionen",
            
            # Dentale Infektionen
            "ODONTOGENE_INFEKTIONEN_AUSBREITUNGSTENDENZ": "Dentale Infektionen",
            "OSTEOMYELITIS_KIEFER": "Dentale Infektionen",
            
            # Abdominale Infektionen
            "PERITONITIS": "Abdominale Infektionen",
            "NEKROTISIERENDE_PANKREATITIS_INFIZIERTE_NEKROSEN": "Abdominale Infektionen",
            "INVASIVE_INTRAABDOMINELLE_MYKOSEN": "Abdominale Infektionen",
            
            # Urogenitale Infektionen
            "AKUTE_UNKOMPLIZIERTE_PYELONEPHRITIS": "Urogenitale Infektionen",
            "KOMPLIZIERTE_NOSOKOMIALE_HARNWEGSINFEKTION": "Urogenitale Infektionen",
            "UROSEPSIS": "Urogenitale Infektionen",
            "AKUTE_PROSTATITIS": "Urogenitale Infektionen",
            "PROSTATAABSZESS": "Urogenitale Infektionen",
            "AKUTE_EPIDIDYMITIS": "Urogenitale Infektionen",
            "EPIDIDYMOORCHITIS": "Urogenitale Infektionen",
            "ENDOMETRITIS": "Urogenitale Infektionen",
            "SALPINGITIS": "Urogenitale Infektionen",
            "TUBOOVARIALABSZESS": "Urogenitale Infektionen",
            "PELVEOPERITONITIS": "Urogenitale Infektionen",
            
            # Haut und Weichteile
            "INFIZIERTE_BISSWUNDEN": "Haut- und Weichteilinfektionen",
            
            # Knochen und Gelenke
            "HAEMATOGENE_OSTEOMYELITIS": "Knochen- und Gelenkinfektionen",
            "SPONDYLODISCITIS": "Knochen- und Gelenkinfektionen",
            "POSTTRAUMATISCHE_POSTOPERATIVE_OSTEOMYELITIS": "Knochen- und Gelenkinfektionen",
            "STERNUMOSTEOMYELITIS": "Knochen- und Gelenkinfektionen",
            "BAKTERIELLE_ARTHRITIS": "Knochen- und Gelenkinfektionen",
            "ENDOPROTHESEN_FREMDKOERPER_ASSOZIIERTE_INFEKTIONEN": "Knochen- und Gelenkinfektionen",
            
            # Systemische Infektionen
            "SEPSIS": "Systemische Infektionen",
            "BAKTERIELLE_ENDOKARDITIS": "Systemische Infektionen",
            "BAKTERIELLE_MENINGITIS": "Systemische Infektionen",
            
            # Gastrointestinale Infektionen
            "BAKTERIELLE_GASTROINTESTINALE_INFEKTIONEN": "Gastrointestinale Infektionen"
        }
        return categories.get(self.value, "Sonstige")

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

# ==== FHIR Patient Models ====
class PatientSearchQuery(BaseModel):
    """Model for patient search requests"""
    search_type: Literal["id", "name_birthdate"]
    # For ID search
    patient_id: Optional[str] = None
    # For name + birthdate search
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    birth_date: Optional[str] = None  # Format: YYYY-MM-DD

class PatientSearchResult(BaseModel):
    """Model for patient search results"""
    patient_id: str
    name: str
    gender: str
    birth_date: Optional[str] = None
    age: Optional[int] = None

class LabValue(BaseModel):
    """Model for laboratory values"""
    name: str
    value: str
    unit: str = ""
    code: Optional[str] = None

class PatientDetailData(BaseModel):
    """Detailed patient data for display"""
    patient_id: str
    name: str
    gender: str
    age: Optional[int] = None
    birth_date: Optional[str] = None
    height: Optional[float] = None  # in cm
    weight: Optional[float] = None  # in kg
    bmi: Optional[float] = None
    pregnancy_status: str = "Nicht Schwanger"
    conditions: List[str] = []  # Pre-existing conditions
    allergies: List[str] = []
    medications: List[str] = []
    lab_values: List[LabValue] = []

# ==== Therapy Recommendation Models ====

class ActiveIngredient(BaseModel):
    """Model for active pharmaceutical ingredients in therapy recommendations"""
    name: str  # e.g., "Amoxicillin", "Clavulansäure"
    strength: str  # e.g., "1000mg", "125mg"

class MedicationRecommendation(BaseModel):
    """Model for individual medication recommendations with dosing bounds"""
    # Active ingredients (1-3 per medication, combined with "/")
    active_ingredients: List[ActiveIngredient] = Field(..., min_items=1, max_items=3)
    
    # Frequency bounds (e.g., "3x täglich" or "3-4x täglich")
    frequency_lower_bound: int = Field(..., ge=1)  # Minimum times per day
    frequency_upper_bound: Optional[int] = Field(None, ge=1)  # Maximum times per day (if range)
    frequency_unit: str = Field(default="täglich")  # "täglich", "alle 8h", etc.
    
    # Duration bounds (e.g., "5 Tage" or "5-7 Tage") - Optional if not specified in guidelines
    duration_lower_bound: Optional[int] = Field(None, ge=0)  # Minimum duration (null if not specified)
    duration_upper_bound: Optional[int] = Field(None, ge=0)  # Maximum duration (null if not specified)
    duration_unit: str = Field(default="Tage")  # "Tage", "Wochen", etc.
    
    # Route of administration
    route: str = Field(default="i.v.")  # "p.o.", "i.v.", "i.m.", etc.
    
    # Additional notes for this specific medication
    notes: Optional[str] = None
    
    # Clinical guidance specific to this medication
    clinical_guidance: Optional[ClinicalGuidance] = None

class ClinicalGuidance(BaseModel):
    """Model for additional clinical guidance and safety information"""
    # Monitoring parameters
    monitoring_parameters: List[str] = []  # e.g., ["Kreatinin", "Leberwerte", "Herzfrequenz"]
    
    # Relevant side effects for this case
    relevant_side_effects: List[str] = []  # e.g., ["Gastrointestinale Beschwerden", "Hautausschlag"]
    
    # Drug interactions (only if patient takes interacting medications)
    drug_interactions: List[str] = []  # e.g., ["Warfarin: INR-Kontrolle erforderlich"]
    
    # Pregnancy considerations (only if patient is pregnant)
    pregnancy_considerations: Optional[str] = None  # e.g., "Kontraindiziert in der Schwangerschaft"
    
    # De-escalation information
    deescalation_info: Optional[str] = None  # e.g., "Nach Erregernachweis auf gezieltes Antibiotikum umstellen"
    
    # Therapy focus information
    therapy_focus_info: Optional[str] = None  # e.g., "Bei Besserung auf orale Therapie umstellen"

class SourceCitation(BaseModel):
    """Model for source citations with guideline and page information"""
    guideline_id: str  # e.g., "020-020l_S3_Behandlung-von-erwachsenen-Patienten-mit-ambulant-erworbener-Pneumonie"
    guideline_title: Optional[str] = None  # Human-readable title
    page_number: Optional[int] = None  # Page number if available
    section: Optional[str] = None  # Section name if available
    relevance_score: float = Field(..., ge=0.0, le=1.0)  # How relevant this source is to the recommendation

class TherapyRecommendation(BaseModel):
    """Model for complete therapy recommendation response"""
    # List of 1-5 recommended therapy options
    therapy_options: List[MedicationRecommendation] = Field(..., min_items=1, max_items=5)
    
    # Clinical guidance and safety information (optional, for therapy-wide guidance)
    clinical_guidance: Optional[ClinicalGuidance] = None
    
    # Source citations that support these recommendations
    source_citations: List[SourceCitation]
    
    # General reasoning for the therapy choice
    therapy_rationale: str  # Explanation why these therapies were chosen
    
    # Confidence level in recommendations
    confidence_level: str = Field(..., pattern="^(Hoch|Mittel|Niedrig)$")  # "Hoch", "Mittel", "Niedrig"
    
    # Warnings or special considerations
    warnings: List[str] = []  # e.g., ["Niereninsuffizienz beachten", "Allergien berücksichtigt"]
    
    # LLM prompt information for debugging (optional fields)
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    llm_model: Optional[str] = None

class TherapyRecommendationRequest(BaseModel):
    """Model for therapy recommendation request"""
    clinical_query: ClinicalQuery
    patient_id: str
    max_therapy_options: int = Field(default=5, ge=1, le=5)
    include_alternative_options: bool = Field(default=True)

# ==== LLM Configuration ====
class LLMConfiguration(BaseModel):
    """Model for LLM configuration settings"""
    endpoint: str = Field(default="https://api.novita.ai/v3/openai/chat/completions", 
                         description="LLM API endpoint URL")
    model: str = Field(default="openai/gpt-oss-20b", 
                      description="Model name to use")
    max_tokens: int = Field(default=16000, ge=1000, le=32768, 
                           description="Maximum tokens for response")
    temperature: float = Field(default=0.6, ge=0.0, le=1.0, 
                              description="Temperature for response generation")