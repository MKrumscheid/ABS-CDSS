from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import os

from models import ClinicalQuery, RAGResult, DosingTable, PatientDetailData
from rag_service_advanced import AdvancedRAGService
from fhir_service import FHIRService

logger = logging.getLogger(__name__)

class TherapyContextBuilder:
    """Service to build comprehensive context for LLM therapy recommendations"""
    
    def __init__(self, rag_service: AdvancedRAGService, fhir_service: FHIRService):
        self.rag_service = rag_service
        self.fhir_service = fhir_service
        self.additional_info_path = os.path.join(os.path.dirname(__file__), "data", "additional_info")
        # Check if RAG is enabled via environment variable
        self.rag_enabled = os.getenv("ENABLE_RAG", "true").lower() == "true"
        if not self.rag_enabled:
            logger.info("RAG functionality is DISABLED - Running in validation mode without RAG")
    
    def _format_indication(self, indication):
        """Format indication with human-readable description"""
        if hasattr(indication, 'get_display_name'):
            return indication.get_display_name()
        else:
            print("Fehler bei der Indikationsformatierung in der Methode _format_indication im Skript therapy_context_builder.py")
    
    def _format_severity(self, severity):
        """Format severity with human-readable description"""
        if hasattr(severity, 'get_display_name'):
            return severity.get_display_name()
        else:
            print("Fehler bei der Schweregradformatierung in der Methode _format_severity im Skript therapy_context_builder.py")
    
    def build_therapy_context(
        self, 
        clinical_query: ClinicalQuery, 
        patient_id: str,
        max_rag_results: int = 10,
        max_dosing_tables: int = 5
    ) -> Dict[str, Any]:
        """
        Build comprehensive context for therapy recommendation
        
        Args:
            clinical_query: Clinical parameters for the case
            patient_id: Patient identifier
            max_rag_results: Maximum number of RAG results to include
            max_dosing_tables: Maximum number of dosing tables to include
            
        Returns:
            Dict containing formatted context and metadata
        """
        context_data = {
            "patient_data": None,
            "rag_results": [],
            "dosing_tables": [],
            "clinical_query": clinical_query.model_dump(),
            "context_text": "",
            "warnings": [],
            "sources_count": 0
        }
        
        try:
            # 1. Get patient data
            logger.info(f"Retrieving patient data for {patient_id}")
            patient_data = self._get_patient_data(patient_id)
            context_data["patient_data"] = patient_data
            
            # 2. Perform RAG search (only if enabled in .env)
            if self.rag_enabled:
                logger.info(f"Performing RAG search for {clinical_query.indication}")
                rag_response = self.rag_service.search(clinical_query, top_k=max_rag_results)
                context_data["rag_results"] = rag_response.results
                context_data["dosing_tables"] = rag_response.dosing_tables[:max_dosing_tables]
                context_data["sources_count"] = len(rag_response.results) + len(rag_response.dosing_tables)
                
                # Add warnings if needed
                if not rag_response.results:
                    context_data["warnings"].append("Keine relevanten Leitlinien-Chunks gefunden")
                if not rag_response.dosing_tables:
                    context_data["warnings"].append("Keine relevanten Dosierungstabellen gefunden")
            else:
                logger.info("RAG is disabled - Skipping guideline and dosing table retrieval")
                context_data["warnings"].append("RAG deaktiviert: Keine Leitlinien oder Dosistabellen verfügbar")
            
            # 3. Build formatted context text
            context_text = self._build_context_text(
                rag_results=context_data["rag_results"],
                dosing_tables=context_data["dosing_tables"],
                clinical_query=clinical_query,
                patient_data=patient_data
            )
            context_data["context_text"] = context_text
            
            if not patient_data:
                context_data["warnings"].append("Keine Patientendaten verfügbar")
            
            if self.rag_enabled:
                logger.info(f"Kontext erfolgreich gebaut: {len(context_data['rag_results'])} RAG results, "
                           f"{len(context_data['dosing_tables'])} dosing tables")
            else:
                logger.info(f"Kontext erfolgreich gebaut (RAG deaktiviert): Nur Patientendaten")
            
        except Exception as e:
            logger.error(f"Fehler beim Bauen des Kontexts: {e}")
            context_data["warnings"].append(f"Fehler beim Erstellen des Kontexts: {str(e)}")
        
        return context_data
    
    def _get_patient_data(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve and format patient data"""
        try:
            # Get patient details from FHIR service
            patient_response = self.fhir_service.get_patient_bundle(patient_id)
            
            if patient_response:
                patient_data = self.fhir_service.parse_patient_data(patient_response)
                return patient_data.model_dump() if patient_data else None
            else:
                # Fallback to raw parsing
                patient_data = self.fhir_service.parse_patient_data_raw(patient_id)
                return patient_data.model_dump() if patient_data else None
                
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Patientendaten für {patient_id}: {e}")
            return None
    
    def _build_context_text(
        self, 
        rag_results: List[RAGResult],
        dosing_tables: List[DosingTable],
        clinical_query: ClinicalQuery,
        patient_data: Optional[Dict[str, Any]]
    ) -> str:
        """Build formatted context text optimized for LLM consumption"""
        
        sections = []
        
        # 1. Clinical Query Summary
        sections.append("=== KLINISCHE ANFRAGE ===")
        sections.append(f"Indikation: {self._format_indication(clinical_query.indication)}")
        sections.append(f"Schweregrad: {self._format_severity(clinical_query.severity)}")
        if clinical_query.infection_site:
            sections.append(f"Infektionsort: {clinical_query.infection_site}")
        if clinical_query.risk_factors:
            sections.append(f"Risikofaktoren: {', '.join(clinical_query.risk_factors)}")
        if clinical_query.suspected_pathogens:
            sections.append(f"Verdachtserreger: {', '.join(clinical_query.suspected_pathogens)}")
        if clinical_query.free_text:
            sections.append(f"Zusätzlicher Kontext: {clinical_query.free_text}")
        sections.append("")
        
        # 2. Patient Summary
        if patient_data:
            sections.append("=== PATIENTENINFORMATIONEN ===")
            sections.append(self._format_patient_summary(patient_data))
            sections.append("")
        
        # 3. Additional Clinical Information (based on rules, only if RAG enabled)
        additional_context = self._get_additional_context(clinical_query, patient_data)
        if additional_context:
            sections.append(additional_context)
        
        # 4. Enhanced Dosing Tables for LLM Processing (only if RAG enabled)
        if dosing_tables and self.rag_enabled:
            sections.append("=== DOSIERUNGSTABELLEN ===")
            sections.append("Die folgenden Tabellen enthalten spezifische Dosierungsempfehlungen (Wähle nur die für diesen Patienten relevante Tabellen aus):")
            sections.append("")
            
            for i, table in enumerate(dosing_tables, 1):
                # Normalize score to 0-1 range for display
                normalized_score = min(table.score, 1.0) if table.score > 1.0 else table.score
                sections.append(f"DOSIERUNGSTABELLE {i} [Relevanz: {normalized_score:.1%}]")
                sections.append(f"TABELLE: {table.table_name}")
                
                # Enhanced clinical context
                if table.clinical_context:
                    sections.append("KLINISCHER KONTEXT:")
                    if table.clinical_context.get("indication"):
                        sections.append(f"   • Indikation: {table.clinical_context['indication']}")
                    if table.clinical_context.get("severity"):
                        sections.append(f"   • Schweregrad: {table.clinical_context['severity']}")
                    if table.clinical_context.get("infection_site"):
                        sections.append(f"   • Infektionsort: {table.clinical_context['infection_site']}")
                    sections.append("")
                
                sections.append("DOSIERUNGSDATEN:")
                sections.append(table.table_html)
                sections.append("")
                
        
        # 5. Relevant Guideline Chunks with Enhanced Source Citations (only if RAG enabled)
        if rag_results and self.rag_enabled:
            sections.append("=== LEITLINIEN-EVIDENZ ===")
            sections.append("Die folgenden Informationen stammen aus medizinischen Leitlinien:")
            sections.append("")
            
            for i, result in enumerate(rag_results, 1):
                # Normalize score to 0-100 range (percentage) for better LLM interpretation
                # Semantic scores can be > 1.0 due to lexical boosting
                if result.score > 1.0:
                    # Scores > 1.0 are already boosted, normalize to max 100
                    normalized_score = min(result.score * 10, 100.0)  # Scale up but cap at 100
                else:
                    # Scores 0.0-1.0 are pure semantic similarity, convert to percentage
                    normalized_score = result.score * 100.0
                
                sections.append(f"EVIDENZ {i} [Relevanz: {normalized_score:.1f}%]")
                sections.append(f"QUELLE: {result.guideline_id}")
                if result.page:
                    sections.append(f"SEITE: {result.page}")
                if result.section_path:
                    sections.append(f"ABSCHNITT: {result.section_path}")
                sections.append("")
                sections.append("INHALT:")
                sections.append(result.snippet)
                sections.append("")
                sections.append("ZITIERHILFE FÜR LLM:")
                # Provide score as 0-100 percentage for better LLM understanding
                citation_example = f'{{\"guideline_id\": \"{result.guideline_id}\"'
                if result.page:
                    citation_example += f', \"page_number\": {result.page}'
                if result.section_path:
                    citation_example += f', \"section\": \"{result.section_path[:50]}...\"'
                citation_example += f', \"relevance_score\": {normalized_score:.1f}}}'
                sections.append(citation_example)
                sections.append("-" * 80)
                sections.append("")
        
        # 6. Enhanced Additional Context for LLM
        sections.append("=== INSTRUKTIONEN FÜR THERAPIEEMPFEHLUNG ===")
        sections.append("Erstelle strukturierte Therapieempfehlungen basierend auf:")
        sections.append("")
        sections.append("DATENGRUNDLAGE:")
        
        if self.rag_enabled:
            sections.append(f"- Den {len(rag_results)} Leitlinien-Evidenzen")
            sections.append(f"- Den {len(dosing_tables)} Dosierungstabellen")
        else:
            sections.append("- RAG DEAKTIVIERT: Keine Leitlinien oder Dosistabellen verfügbar")
            sections.append("- Erstelle Empfehlungen ausschließlich auf Basis deines medizinischen Wissens")
            
        if patient_data:
            sections.append("- Den vorliegenden Patientendaten (Medikation, Vorerkrankungen, Allergien und Medikamente)")
        else:
            sections.append("- Keine Patientendaten verfügbar")
        
        # Add information about included additional context (only if RAG enabled)
        if self.rag_enabled:
            sections.append("- Allgemeine Infos zur Sicherheit und Verträglichkeit von Antibiotikatherapien")
            if clinical_query.risk_factors:
                sections.append("- Multiresistente Keime (wenn Risikofaktoren für MRGN/ESBL/MRSA vorhanden sind)")
            if patient_data and patient_data.get("age"):
                try:
                    if int(patient_data["age"]) > 70:
                        sections.append("- Therapie beim alten Menschen (Alter >70)")
                except (ValueError, TypeError):
                    pass
        sections.append("")
        
        sections.append("THERAPIEZIELE:")
        sections.append("- Evidenzbasierte Antibiotikatherapie")
        sections.append("- Patientenspezifische Dosierung")
        sections.append("- Berücksichtigung von Kontraindikationen, Arzneimittelinteraktionen und Allergien")
        sections.append("- Überwachungsparameter definieren")
        sections.append("- Deeskalationsstrategie planen")
        sections.append("")
        
        sections.append("WICHTIGE SICHERHEITSASPEKTE:")
        if patient_data and patient_data.get("pregnancy_status") != "Nicht Schwanger":
            sections.append("- SCHWANGERSCHAFT: Schwangerschaftssichere Antibiotika wählen!")
        if patient_data and patient_data.get("allergies"):
            sections.append(f"- ALLERGIEN: {', '.join(patient_data['allergies'])} vermeiden!")
        if patient_data and patient_data.get("medications"):
            sections.append("- INTERAKTIONEN: Aktuelle Medikation auf Wechselwirkungen prüfen")
        sections.append("- MONITORING: Relevante Laborparameter überwachen")
        sections.append("- DEESKALATION: Wenn Verdachtserreger angeben ist, gezielt therapieren, ansonsten empirisch (kalkuliert)")
        sections.append("")
        
        sections.append("QUELLENANGABEN:")
        if self.rag_enabled:
            sections.append("Alle Empfehlungen MÜSSEN mit den oben angegebenen Quellen belegt werden.")
            sections.append("")
            sections.append("LEITLINIEN-EVIDENZ:")
            sections.append("Format: {\"guideline_id\": \"ID\", \"page_number\": Zahl, \"section\": \"Abschnitt\", \"relevance_score\": XX.X}")
            sections.append("WICHTIG: relevance_score ist ein Prozentwert zwischen 0.0 und 100.0 (höher = relevanter)")
        else:
            sections.append("RAG DEAKTIVIERT - Keine Quellenangaben erforderlich (Validierungsmodus)")
            sections.append("Erstelle Empfehlungen basierend auf deinem medizinischen Wissen und den Patientendaten.")
        sections.append("")
        
        # Add dosing table source citations (only if RAG enabled)
        if dosing_tables and self.rag_enabled:
            sections.append("")
            sections.append("DOSIERUNGSTABELLEN-QUELLEN:")
            for i, table in enumerate(dosing_tables, 1):
                # Normalize dosing table score to 0-100 percentage range
                # Table scores can be very high due to boosting (+1000/+100)
                if table.score > 100:
                    normalized_table_score = 100.0  # Cap at 100%
                elif table.score > 10:
                    normalized_table_score = min(table.score, 100.0)  # Already in reasonable range
                else:
                    normalized_table_score = table.score * 10.0  # Scale up small scores
                normalized_table_score = max(0.0, min(normalized_table_score, 100.0))
                
                sections.append(f"Tabelle {i}: {table.table_name}")
                sections.append(f"Quelle: {table.table_id}")
                sections.append(f"Format: {{\"dosing_table_id\": \"{table.table_id}\", \"table_name\": \"{table.table_name}\", \"relevance_score\": {normalized_table_score:.1f}}}")
            sections.append("")
            sections.append("WICHTIG: Dosierungsempfehlungen müssen mit der entsprechenden Tabellennummer und Quelle zitiert werden.")
            sections.append("WICHTIG: relevance_score ist ein Prozentwert zwischen 0.0 und 100.0 (höher = relevanter)")
        sections.append("")
        
        # Add metadata about available sources for easier LLM processing (only if RAG enabled)
        if self.rag_enabled and (rag_results or dosing_tables):
            sections.append("=== VERFÜGBARE QUELLEN (Übersicht) ===")
            unique_guidelines = set()
            if rag_results:
                for result in rag_results:
                    unique_guidelines.add(result.guideline_id)
            if dosing_tables:
                for table in dosing_tables:
                    if table.clinical_context.get('source_guideline'):
                        unique_guidelines.add(table.clinical_context['source_guideline'])
            
            # Add additional information sources
            unique_guidelines.add("S2k_Parenterale_Antibiotika_2019-08 (Sicherheit und Verträglichkeit, S. 81-84)")
            if clinical_query.risk_factors:
                unique_guidelines.add("S2k_Parenterale_Antibiotika_2019-08 (Multiresistente Keime, S. 309-318)")
            if patient_data and patient_data.get("age"):
                try:
                    if int(patient_data["age"]) > 70:
                        unique_guidelines.add("S2k_Parenterale_Antibiotika_2019-08 (Alte Menschen, S. 294-302)")
                except (ValueError, TypeError):
                    pass
            
            for guideline in sorted(unique_guidelines):
                sections.append(f"- {guideline}")
            sections.append("")
        
        return "\n".join(sections)
    
    def _format_patient_summary(self, patient_data: Dict[str, Any]) -> str:
        """Format patient data into a concise summary without names for privacy"""
        summary_lines = []
        
        # Demographics (excluding name for privacy)
        demographic_info = []
        if patient_data.get("age"):
            demographic_info.append(f"Alter: {patient_data['age']} Jahre")
        if patient_data.get("gender"):
            demographic_info.append(f"Geschlecht: {patient_data['gender']}")
        if demographic_info:
            summary_lines.append(", ".join(demographic_info))
        
        # Physical parameters
        physical_params = []
        if patient_data.get("weight"):
            physical_params.append(f"Gewicht: {patient_data['weight']} kg")
        if patient_data.get("height"):
            physical_params.append(f"Größe: {patient_data['height']} cm")
        if patient_data.get("bmi"):
            physical_params.append(f"BMI: {patient_data['bmi']}")
        if patient_data.get("gfr"):
            physical_params.append(f"GFR: {patient_data['gfr']} ml/min/1.73m²")
        if physical_params:
            summary_lines.append(", ".join(physical_params))
        
        # Pregnancy status (important for drug selection)
        pregnancy_status = patient_data.get("pregnancy_status", "Nicht Schwanger")
        if pregnancy_status != "Nicht Schwanger":
            summary_lines.append(f"SCHWANGERSCHAFT: {pregnancy_status}")
        
        # Medical history (consolidated)
        conditions = patient_data.get("conditions", [])
        if conditions:
            summary_lines.append(f"Anamnese/Vorerkrankungen: {', '.join(conditions)}")
        
        # Allergies (critical for drug selection)
        allergies = patient_data.get("allergies", [])
        if allergies:
            summary_lines.append(f"Allergien: {', '.join(allergies)}")
        else:
            summary_lines.append("Allergien: Keine bekannt")
        
        # Current medications (IMPORTANT for interactions)
        medications = patient_data.get("medications", [])
        if medications:
            summary_lines.append(f"Aktuelle Medikation: {', '.join(medications)}")
        
        # Key lab values (prioritize organ function)
        lab_values = patient_data.get("lab_values", [])
        if lab_values:
            key_labs = []
            for lab in lab_values:
                name = lab.get("name", "")
                value = lab.get("value", "")
                unit = lab.get("unit", "")
                
                # Prioritize kidney and liver function for dosing
                if any(keyword in name.lower() for keyword in ["kreatinin", "clearance", "gfr", "bilirubin", "ast", "alt"]):
                    key_labs.append(f"{name}: {value} {unit}".strip())
            
            if key_labs:
                summary_lines.append(f"Relevante Laborwerte: {', '.join(key_labs)}")
            elif len(lab_values) <= 5:
                # If few lab values, show all
                all_labs = []
                for lab in lab_values:
                    name = lab.get("name", "")
                    value = lab.get("value", "")
                    unit = lab.get("unit", "")
                    all_labs.append(f"{name}: {value} {unit}".strip())
                summary_lines.append(f"Laborwerte: {', '.join(all_labs)}")
        
        return "\n".join(summary_lines)
    
    def _load_additional_info(self, filename: str) -> str:
        """Load additional information from file"""
        try:
            file_path = os.path.join(self.additional_info_path, filename)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.warning(f"Additional info file not found: {file_path}")
                return ""
        except Exception as e:
            logger.error(f"Error loading additional info from {filename}: {e}")
            return ""
    
    def _get_additional_context(
        self, 
        clinical_query: ClinicalQuery, 
        patient_data: Optional[Dict[str, Any]]
    ) -> str:
        """
        Get additional context based on rules:
        - Always: Sicherheit und Verträglichkeit
        - If risk factors: Infektionen durch multiresistente Keime  
        - If patient age >70: Antibiotikatherapie beim alten Menschen
        
        NOTE: Only loads additional info if RAG is enabled
        """
        # Skip additional context if RAG is disabled
        if not self.rag_enabled:
            return ""
            
        additional_sections = []
        
        # Always include safety information
        safety_info = self._load_additional_info("Sicherheit und Verträglichkeit.txt")
        if safety_info:
            additional_sections.append("=== ALLGEMEINE INFOS ZUR SICHERHEIT UND VERTRÄGLICHKEIT DER ANTIBIOTISCHEN THERAPIE ===")
            additional_sections.append("(Quelle: S2k_Parenterale_Antibiotika_2019-08, Seite 81-84)")
            additional_sections.append("")
            additional_sections.append(safety_info)
            additional_sections.append("")
        
        # Include resistant pathogens info if risk factors present
        if clinical_query.risk_factors:
            resistant_info = self._load_additional_info("Infektionen durch multiresistente Keime.txt")
            if resistant_info:
                additional_sections.append("=== INFORMATIONEN FÜR INFEKTIONEN DURCH MULTIRESISTENTE KEIME ===")
                additional_sections.append("(Quelle: S2k_Parenterale_Antibiotika_2019-08, Seite 309-318)")
                additional_sections.append(f"RELEVANT wegen Risikofaktoren: {', '.join(clinical_query.risk_factors)}")
                additional_sections.append("")
                additional_sections.append(resistant_info)
                additional_sections.append("")
        
        # Include elderly therapy info if patient age >70
        if patient_data and patient_data.get("age"):
            try:
                patient_age = int(patient_data["age"])
                if patient_age > 70:
                    elderly_info = self._load_additional_info("Antibiotikatherapie beim alten Menschen.txt")
                    if elderly_info:
                        additional_sections.append("=== ANTIBIOTIKATHERAPIE BEIM ALTEN MENSCHEN (Alter > 70) ===")
                        additional_sections.append("(Quelle: S2k_Parenterale_Antibiotika_2019-08, Seite 294-302)")
                        additional_sections.append(f"RELEVANT wegen Patientenalter: {patient_age} Jahre (>70)")
                        additional_sections.append("")
                        additional_sections.append(elderly_info)
                        additional_sections.append("")
            except (ValueError, TypeError):
                logger.warning(f"Could not parse patient age: {patient_data.get('age')}")
        
        # Include kidney dosing adjustment table if patient GFR ≤ 60
        if patient_data and patient_data.get("gfr"):
            try:
                patient_gfr = float(patient_data["gfr"])
                if patient_gfr <= 60:
                    kidney_dosing_info = self._load_additional_info("Anpassung Nierenfunktion Tabelle.txt")
                    if kidney_dosing_info:
                        additional_sections.append("=== DOSIERUNGSANPASSUNG BEI NIERENINSUFFIZIENZ ===")
                        additional_sections.append("(Quelle: Interne Dosierungstabelle für Antiinfektiva)")
                        additional_sections.append(f"RELEVANT wegen eingeschränkter Nierenfunktion: GFR {patient_gfr} ml/min/1.73m² (≤ 60)")
                        additional_sections.append("")
                        additional_sections.append(kidney_dosing_info)
                        additional_sections.append("")
            except (ValueError, TypeError):
                logger.warning(f"Could not parse patient GFR: {patient_data.get('gfr')}")
        
        return "\n".join(additional_sections)
    
    def get_context_summary(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of the built context for debugging/monitoring"""
        return {
            "patient_available": context_data["patient_data"] is not None,
            "rag_results_count": len(context_data["rag_results"]),
            "dosing_tables_count": len(context_data["dosing_tables"]),
            "context_length": len(context_data["context_text"]),
            "total_sources": context_data["sources_count"],
            "warnings": context_data["warnings"],
            "clinical_indication": context_data["clinical_query"].get("indication"),
            "clinical_severity": context_data["clinical_query"].get("severity")
        }