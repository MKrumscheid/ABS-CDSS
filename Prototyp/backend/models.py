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
    CAP = "AMBULANT_ERWORBENE_PNEUMONIE"
    HAP = "NOSOKOMIAL_ERWORBENE_PNEUMONIE"
    AECOPD = "AKUTE_EXAZERBATION_COPD"
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
            "AMBULANT_ERWORBENE_PNEUMONIE": "CAP (Ambulant erworbene Pneumonie)",
            "NOSOKOMIAL_ERWORBENE_PNEUMONIE": "HAP (Nosokomial erworbene Pneumonie)", 
            "AKUTE_EXAZERBATION_COPD": "AECOPD (Akute Exazerbation der COPD)",
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
            "ODONTOGENE_INFEKTIONEN_AUSBREITUNGSTENDENZ": "Odontogene Infektionen mit Ausbreitungstendenz",
            "OSTEOMYELITIS_KIEFER": "Osteomyelitis der Kiefer",
            "PERITONITIS": "Peritonitis",
            "NEKROTISIERENDE_PANKREATITIS_INFIZIERTE_NEKROSEN": "Nekrotisierende Pankreatitis mit infizierten Nekrosen",
            "INVASIVE_INTRAABDOMINELLE_MYKOSEN": "Invasive intraabdominelle Mykosen",
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
            "INFIZIERTE_BISSWUNDEN": "Infizierte Bisswunden",
            "HAEMATOGENE_OSTEOMYELITIS": "Hämatogene Osteomyelitis",
            "SPONDYLODISCITIS": "Spondylodiscitis",
            "POSTTRAUMATISCHE_POSTOPERATIVE_OSTEOMYELITIS": "Posttraumatische/postoperative Osteomyelitis",
            "STERNUMOSTEOMYELITIS": "Sternumosteomyelitis",
            "BAKTERIELLE_ARTHRITIS": "Bakterielle Arthritis",
            "ENDOPROTHESEN_FREMDKOERPER_ASSOZIIERTE_INFEKTIONEN": "Endoprothesen-/Fremdkörper-assoziierte Infektionen",
            "SEPSIS": "Sepsis",
            "BAKTERIELLE_ENDOKARDITIS": "Bakterielle Endokarditis",
            "BAKTERIELLE_MENINGITIS": "Bakterielle Meningitis",
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
            "AMBULANT_ERWORBENE_PNEUMONIE": "Respiratorische Infektionen",
            "NOSOKOMIAL_ERWORBENE_PNEUMONIE": "Respiratorische Infektionen",
            "AKUTE_EXAZERBATION_COPD": "Respiratorische Infektionen",
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
            "ODONTOGENE_INFEKTIONEN_AUSBREITUNGSTENDENZ": "Dentale Infektionen",
            "OSTEOMYELITIS_KIEFER": "Dentale Infektionen",
            "PERITONITIS": "Abdominale Infektionen",
            "NEKROTISIERENDE_PANKREATITIS_INFIZIERTE_NEKROSEN": "Abdominale Infektionen",
            "INVASIVE_INTRAABDOMINELLE_MYKOSEN": "Abdominale Infektionen",
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
            "INFIZIERTE_BISSWUNDEN": "Haut- und Weichteilinfektionen",
            "HAEMATOGENE_OSTEOMYELITIS": "Knochen- und Gelenkinfektionen",
            "SPONDYLODISCITIS": "Knochen- und Gelenkinfektionen",
            "POSTTRAUMATISCHE_POSTOPERATIVE_OSTEOMYELITIS": "Knochen- und Gelenkinfektionen",
            "STERNUMOSTEOMYELITIS": "Knochen- und Gelenkinfektionen",
            "BAKTERIELLE_ARTHRITIS": "Knochen- und Gelenkinfektionen",
            "ENDOPROTHESEN_FREMDKOERPER_ASSOZIIERTE_INFEKTIONEN": "Knochen- und Gelenkinfektionen",
            "SEPSIS": "Systemische Infektionen",
            "BAKTERIELLE_ENDOKARDITIS": "Systemische Infektionen",
            "BAKTERIELLE_MENINGITIS": "Systemische Infektionen",
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
    conditions: List[str] = []  
    allergies: List[str] = []
    medications: List[str] = []
    lab_values: List[LabValue] = []

# ==== Therapy Recommendation Models ====

class ActiveIngredient(BaseModel):
    """Model for active pharmaceutical ingredients in therapy recommendations with individual dosing"""
    name: str 
    strength: str 
    
    frequency_lower_bound: int = Field(..., ge=1)  
    frequency_upper_bound: Optional[int] = Field(None, ge=1) 
    frequency_unit: str = Field(default="täglich") 
    
    
    duration_lower_bound: Optional[int] = Field(None, ge=0)  
    duration_upper_bound: Optional[int] = Field(None, ge=0)  
    duration_unit: Optional[str] = Field(default="Tage")  
    
    route: str = Field(default="i.v.")  # "p.o.", "i.v.", "i.m.", etc.

class MedicationRecommendation(BaseModel):
    """Model for individual medication recommendations"""
    # Active ingredients (1-3 per medication, each with individual dosing parameters)
    active_ingredients: List[ActiveIngredient] = Field(..., min_items=1, max_items=4)
    
    # Additional notes for this specific medication combination
    notes: Optional[str] = None
    
    # Clinical guidance specific to this medication
    clinical_guidance: Optional[ClinicalGuidance] = None

class ClinicalGuidance(BaseModel):
    """Model for additional clinical guidance and safety information"""
    # Monitoring parameters
    monitoring_parameters: List[str] = []  
    
    # Relevant side effects for this case
    relevant_side_effects: List[str] = []  
    
    # Drug interactions (only if patient takes interacting medications)
    drug_interactions: List[str] = []  
    
    # Pregnancy considerations 
    pregnancy_considerations: Optional[str] = None  
    
    # De-escalation and therapy focus information 
    deescalation_focus_info: Optional[str] = None  

class SourceCitation(BaseModel):
    """Model for source citations with guideline and page information"""
    guideline_id: str  
    guideline_title: Optional[str] = None 
    page_number: Optional[int] = None 
    section: Optional[str] = None 
    relevance_score: float = Field(..., ge=0.0, le=100.0) 

class TherapyRecommendation(BaseModel):
    """Model for complete therapy recommendation response"""
    # List of 1-5 recommended therapy options
    therapy_options: List[MedicationRecommendation] = Field(..., min_items=1, max_items=5)
    
    # Clinical guidance and safety information (optional, for therapy-wide guidance)
    clinical_guidance: Optional[ClinicalGuidance] = None
    
    # Source citations that support these recommendations
    source_citations: List[SourceCitation]
    
    # General reasoning for the therapy choice
    therapy_rationale: str  
    
    # Confidence level in recommendations
    confidence_level: str = Field(..., pattern="^(Hoch|Mittel|Niedrig)$")  
    
    # Warnings or special considerations
    warnings: List[str] = []  
    
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
    model: str = Field(default="openai/gpt-oss-120b", 
                      description="Model name to use")
    max_tokens: int = Field(default=16000, ge=1000, le=32768, 
                           description="Maximum tokens for response")
    temperature: float = Field(default=0.6, ge=0.0, le=1.0, 
                              description="Temperature for response generation")

# ==== Saved Therapy Recommendation Models ====
class SaveTherapyRecommendationRequest(BaseModel):
    """Model for saving therapy recommendation"""
    title: Optional[str] = Field(None, max_length=200, description="Optional title for saved recommendation")
    request_data: dict = Field(..., description="Original request data")
    therapy_recommendation: dict = Field(..., description="LLM therapy recommendation response")
    patient_data: Optional[dict] = Field(None, description="Patient data from FHIR")

class SavedTherapyRecommendationResponse(BaseModel):
    """Model for saved therapy recommendation response"""
    id: int
    title: Optional[str]
    created_at: datetime
    request_data: dict
    therapy_recommendation: dict
    patient_data: Optional[dict]

class SavedTherapyRecommendationListItem(BaseModel):
    """Model for saved therapy recommendation list item (summary)"""
    id: int
    title: Optional[str]
    created_at: datetime
    indication_display: str = Field(..., description="Human readable indication")
    patient_id: Optional[str] = Field(None, description="Patient ID if available")