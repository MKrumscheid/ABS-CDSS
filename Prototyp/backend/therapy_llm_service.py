"""
LLM Service for Therapy Recommendations using Novita AI
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

from models import (
    TherapyRecommendation, 
    TherapyRecommendationRequest,
    ClinicalQuery,
    MedicationRecommendation,
    ActiveIngredient,
    ClinicalGuidance,
    SourceCitation
)

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class TherapyLLMService:
    """Service for generating therapy recommendations using LLM"""
    
    def __init__(self):
        self.endpoint = os.getenv("NOVITA_API_BASE_URL", "https://api.novita.ai/v3/openai/chat/completions")
        self.client = OpenAI(
            base_url=self.endpoint,
            api_key=os.getenv("NOVITA_API_KEY")
        )
        
        self.model = os.getenv("NOVITA_MODEL", "openai/gpt-oss-120b")
        self.max_tokens = int(os.getenv("NOVITA_MAX_TOKENS", "4000"))  # Safe default within API limits
        self.temperature = float(os.getenv("NOVITA_TEMPERATURE", "0.6"))
        
        # Validate API key
        if not os.getenv("NOVITA_API_KEY"):
            raise ValueError("NOVITA_API_KEY not found in environment variables")
        
        logger.info(f"TherapyLLMService initialized with model: {self.model}")
    
    def generate_therapy_recommendation(
        self, 
        context_data: Dict[str, Any], 
        max_options: int = 5
    ) -> TherapyRecommendation:
        """
        Generate therapy recommendations based on clinical context
        
        Args:
            context_data: Dictionary containing patient data, RAG results, dosing tables, clinical query
            max_options: Maximum number of therapy options to generate (1-5)
            
        Returns:
            TherapyRecommendation object with structured therapy plan
        """
        try:
            # Build the system prompt for medical therapy recommendations
            system_prompt = self._build_system_prompt()
            
            # Build the user prompt with context
            user_prompt = self._build_user_prompt(context_data, max_options)
            
            logger.info(f"Generating therapy recommendation with {len(user_prompt)} chars of context")
            
            # Call LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=0.9,
                presence_penalty=-1,
                frequency_penalty=0,
                response_format={"type": "json_object"},
                extra_body={
                    "top_k": 50,
                    "repetition_penalty": 1,
                    "min_p": 0
                }
            )
            
            # Parse LLM response
            llm_response = response.choices[0].message.content
            logger.info(f"Received LLM response: {len(llm_response)} characters")
            
            # Debug: Log the complete LLM response 
            print(f"=== DEBUG COMPLETE LLM RESPONSE ===")
            print(llm_response)
            print(f"=== END LLM RESPONSE ===")
            
            # Clean the response to handle potential control characters
            try:
                # Remove control characters that might break JSON parsing
                import re
                cleaned_response = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', llm_response)
                
                # Try to parse JSON
                therapy_data = json.loads(cleaned_response)
                
                # Debug: Show parsed structure
                print(f"=== DEBUG PARSED JSON STRUCTURE ===")
                for i, option in enumerate(therapy_data.get("therapy_options", [])):
                    print(f"Option {i+1}:")
                    clinical_guidance = option.get("clinical_guidance", {})
                    print(f"  - Has clinical_guidance: {clinical_guidance is not None}")
                    if clinical_guidance:
                        print(f"  - deescalation_focus_info: {clinical_guidance.get('deescalation_focus_info')}")
                print(f"=== END PARSED JSON ===)")
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM JSON response: {e}")
                logger.error(f"Response length: {len(llm_response)}")
                logger.error(f"Character at error position: '{llm_response[e.pos] if e.pos < len(llm_response) else 'EOF'}'")
                logger.error(f"Context around error (±50 chars): '{llm_response[max(0,e.pos-50):e.pos+50]}'")
                
                # Try to extract JSON from response if it's embedded in text
                try:
                    # Look for JSON object boundaries
                    start_idx = llm_response.find('{')
                    end_idx = llm_response.rfind('}') + 1
                    
                    if start_idx != -1 and end_idx > start_idx:
                        json_part = llm_response[start_idx:end_idx]
                        # Clean and parse extracted JSON
                        cleaned_json = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_part)
                        therapy_data = json.loads(cleaned_json)
                        logger.info("Successfully extracted and parsed JSON from response")
                    else:
                        raise ValueError(f"No valid JSON found in LLM response")
                        
                except (json.JSONDecodeError, ValueError) as inner_e:
                    logger.error(f"Failed to extract JSON: {inner_e}")
                    raise ValueError(f"Invalid JSON response from LLM: {e}")
            
            except Exception as e:
                logger.error(f"Unexpected error parsing LLM response: {e}")
                raise ValueError(f"Error processing LLM response: {e}")
            
            # Log the parsed therapy data for debugging
            logger.info(f"Parsed therapy data keys: {list(therapy_data.keys())}")
            if "therapy_options" in therapy_data:
                logger.info(f"Number of therapy options: {len(therapy_data['therapy_options'])}")
            else:
                logger.warning("No 'therapy_options' key found in parsed data!")
                logger.info(f"Available keys: {list(therapy_data.keys())}")
            
            # Convert to Pydantic model
            therapy_recommendation = self._parse_llm_response(therapy_data, context_data)
            
            # Add prompt information for frontend debugging
            therapy_recommendation.system_prompt = system_prompt
            therapy_recommendation.user_prompt = user_prompt
            therapy_recommendation.llm_model = self.model
            
            logger.info(f"Successfully generated {len(therapy_recommendation.therapy_options)} therapy options")
            return therapy_recommendation
            
        except Exception as e:
            logger.error(f"Error generating therapy recommendation: {e}")
            raise
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for therapy recommendation"""
        return """Du bist ein erfahrener Kliniker für Infektiologie und Antibiotikatherapie. Deine Aufgabe ist es, basierend auf klinischen Informationen, Patientendaten und evidenzbasierten Leitlinien strukturierte Therapieempfehlungen für Antibiotikatherapien zu erstellen.

WICHTIGE HINWEISE:
- Dies ist nur ein Prototyp für Forschungszwecke, NICHT für reale Patienten
- Alle Empfehlungen müssen auf den bereitgestellten Leitlinien und Dosierungstabellen basieren
- Berücksichtige immer Patientencharakteristika (Allergien, Schwangerschaft, Nierenfunktion, Vorerkrankungen, Medikation, etc.)
- Zitiere präzise die Quellen mit Leitlinien-ID und Seitenzahl
- Antworte AUSSCHLIESSLICH auf DEUTSCH und verwende deutsche medizinische Begriffe
- WICHTIG: Interaktionen nur erwähnen, wenn der Patient das interagierende Medikament einnimmt
- WICHTIG: Monitoring-Parameter nur für die tatsächlich verschriebenen Antibiotika relevant


AUSGABEFORMAT:
Antworte AUSSCHLIESSLICH mit einem validen JSON-Objekt im folgenden Format:

{
  "therapy_options": [
    {
      "active_ingredients": [
        {
          "name": "Wirkstoffname", 
          "strength": "Stärke mit Einheit",
          "frequency_lower_bound": Integer (mindestens 1),
          "frequency_upper_bound": Integer_oder_null,
          "frequency_unit": "z.B. täglich oder wöchentlich",
          "duration_lower_bound": Integer_oder_null,
          "duration_upper_bound": Integer_oder_null,
          "duration_unit": "z.B. Tage oder Wochen",
          "route": "z.B. p.o., i.v., i.m."
        }
      ],
      "notes": "Medikamentenspezifische Hinweise für die gesamte Kombinationstherapie",
      "clinical_guidance": {
        "monitoring_parameters": ["Monitoring Parameter für diese Therapie"],
        "relevant_side_effects": ["Relevante Nebenwirkungen"],
        "drug_interactions": ["Nur wenn Patient interagierende Medikamente einnimmt"],
        "pregnancy_considerations": "Text oder null - nur wenn relevant UND Patient weiblich ist",
        "deescalation_focus_info": "Kombinierte Deeskalations- und Fokussierungs-Strategie für diese Therapie"
      }
    }
  ],
  "clinical_guidance": null,
  "source_citations": [
    {
      "guideline_id": "ID_der_Leitlinie",
      "guideline_title": "Titel oder null",
      "page_number": Seitenzahl_oder_null,
      "section": "Abschnitt oder null",
      "relevance_score": 95.0
    }
  ],
  "therapy_rationale": "Begründung für die Therapiewahl",
  "confidence_level": "Hoch",
  "warnings": ["Warnung1", "Warnung2"]
}

DOSIERUNGS-REGELN:
- active_ingredients: Array mit 1-3 Wirkstoffen pro Medikament
- frequency_bounds: Häufigkeit pro Tag (z.B. 3xtäglich --> nur lower_bound = 3 setzen, upper_bound = Null, 3-4xtäglich --> lower_bound = 3, upper_bound = 4)
- duration_bounds: INDIVIDUELLE Therapiedauer für JEDES Medikament (z.B. 5 Tage --> lower_bound = 5, upper_bound = Null, 5-7 Tage --> lower_bound = 5, upper_bound = 7)
- WICHTIG: Therapiedauer nur angeben wenn diese in den Informationen explizit genannt wird, ansonsten "Keine Information zur Therapiedauer verfügbar" und beide bounds auf Null setzen
- Therapiedauer nicht nur in notes erwähnen, sondern als duration_bounds angeben
- Berücksichtige patientenspezifische Faktoren für die Dauer (Alter, Schweregrad, Komorbidität)
- Alle Zahlenfelder müssen Integer sein
- confidence_level: Nur "Hoch", "Mittel", oder "Niedrig"

QUELLEN-REGELN:
- relevance_score ist ein PROZENTWERT zwischen 0.0 und 100.0 (höher = relevanter)
- Nutze die angegebenen relevance_scores aus den Evidenzen, um die Qualität deiner Quellenlage zu bewerten
- Scores > 80% = sehr gute Evidenz, 50-80% = gute Evidenz, < 50% = schwache Evidenz
- Berücksichtige die Quellenlage bei deinem confidence_level (viele hochrelevante Quellen = "Hoch", wenige schwache Quellen = "Niedrig")
"""

    def _build_user_prompt(self, context_data: Dict[str, Any], max_options: int) -> str:
        """Build the user prompt with clinical context"""
        
        # Extract context components
        clinical_query = context_data.get("clinical_query", {})
        patient_data = context_data.get("patient_data")
        rag_results = context_data.get("rag_results", [])
        dosing_tables = context_data.get("dosing_tables", [])
        context_text = context_data.get("context_text", "")
        
        prompt_parts = []
        
        # Use the pre-formatted context text which already contains the clinical situation
        # This avoids duplication and ensures proper formatting
        if context_text:
            prompt_parts.append(context_text)
            prompt_parts.append("")
        
        # Task instruction
        prompt_parts.append("=== AUFGABE ===")
        prompt_parts.append(f"Analysiere die verfügbaren Quellen und erstelle zwischen 1 und {max_options} Therapieoptionen für diese klinische Situation.")
        prompt_parts.append("WICHTIG: Die Anzahl der Therapieoptionen soll der Quellenlage angemessen sein:")
        prompt_parts.append("- Bei umfangreichen, klaren Leitlinien mit mehreren validen Alternativen: 3-5 Optionen")
        prompt_parts.append("- Bei mäßiger Quellenlage oder spezifischen Indikationen: 2-3 Optionen") 
        prompt_parts.append("- Bei begrenzter Quellenlage oder sehr spezifischen Fällen: 1-2 Optionen")
        prompt_parts.append("- Erstelle NUR Therapien, die durch die bereitgestellten Quellen gut begründet sind")
        prompt_parts.append("")
        prompt_parts.append("Berücksichtige:")
        prompt_parts.append("- Die bereitgestellten Leitlinien und Dosierungstabellen")
        prompt_parts.append("- Patientenspezifische Faktoren (Allergien, Schwangerschaft, etc.). Achte bei Allergien auch auf den Schweregrad der Allergie, bzw. Unverträglichkeit und entscheide ob wirklich eine Kontraindikation vorliegt oder nicht, da Patienten lebensrettende Antibiotika nicht aufgrund leichter Unverträglichkeitsreaktionen vorbehalten werden sollen.")
        prompt_parts.append("- Mögliche Arzneimittelinteraktionen")
        prompt_parts.append("- Notwendige Überwachungsparameter")
        prompt_parts.append("- Deeskalations- und Fokussierungsstrategien")
        prompt_parts.append("")
        prompt_parts.append("Antworte mit einem validen JSON-Objekt gemäß dem vorgegebenen Schema.")
        
        return "\n".join(prompt_parts)
    
    def _parse_llm_response(
        self, 
        therapy_data: Dict[str, Any], 
        context_data: Dict[str, Any]
    ) -> TherapyRecommendation:
        """Parse LLM JSON response into TherapyRecommendation object"""
        
        # Parse therapy options
        therapy_options = []
        for option_data in therapy_data.get("therapy_options", []):
            # Parse active ingredients with individual dosing parameters
            active_ingredients = []
            for ingredient_data in option_data.get("active_ingredients", []):
                # Handle None values for optional fields
                duration_unit = ingredient_data.get("duration_unit")
                if duration_unit is None and (ingredient_data.get("duration_lower_bound") is None):
                    duration_unit = None  # No duration specified
                elif duration_unit is None:
                    duration_unit = "Tage"  # Default if duration is specified but unit is missing
                
                active_ingredients.append(ActiveIngredient(
                    name=ingredient_data.get("name", ""),
                    strength=ingredient_data.get("strength", ""),
                    frequency_lower_bound=ingredient_data.get("frequency_lower_bound", 1),
                    frequency_upper_bound=ingredient_data.get("frequency_upper_bound"),
                    frequency_unit=ingredient_data.get("frequency_unit", "täglich"),
                    duration_lower_bound=ingredient_data.get("duration_lower_bound"),
                    duration_upper_bound=ingredient_data.get("duration_upper_bound"),
                    duration_unit=duration_unit,
                    route=ingredient_data.get("route", "p.o.")
                ))
            
            # Parse clinical guidance for this specific medication
            medication_guidance_data = option_data.get("clinical_guidance", {})
            medication_clinical_guidance = None
            if medication_guidance_data:
                medication_clinical_guidance = ClinicalGuidance(
                    monitoring_parameters=medication_guidance_data.get("monitoring_parameters", []),
                    relevant_side_effects=medication_guidance_data.get("relevant_side_effects", []),
                    drug_interactions=medication_guidance_data.get("drug_interactions", []),
                    pregnancy_considerations=medication_guidance_data.get("pregnancy_considerations"),
                    deescalation_focus_info=medication_guidance_data.get("deescalation_focus_info")
                )
            
            # Create medication recommendation
            therapy_options.append(MedicationRecommendation(
                active_ingredients=active_ingredients,
                notes=option_data.get("notes"),
                clinical_guidance=medication_clinical_guidance
            ))
        
        # Parse therapy-level clinical guidance (now optional)
        therapy_guidance_data = therapy_data.get("clinical_guidance", {})
        therapy_clinical_guidance = None
        if therapy_guidance_data and any(therapy_guidance_data.values()):
            therapy_clinical_guidance = ClinicalGuidance(
                monitoring_parameters=therapy_guidance_data.get("monitoring_parameters", []),
                relevant_side_effects=therapy_guidance_data.get("relevant_side_effects", []),
                drug_interactions=therapy_guidance_data.get("drug_interactions", []),
                pregnancy_considerations=therapy_guidance_data.get("pregnancy_considerations"),
                deescalation_focus_info=therapy_guidance_data.get("deescalation_focus_info")
            )
        
        # Parse source citations
        source_citations = []
        for citation_data in therapy_data.get("source_citations", []):
            # Ensure relevance_score is between 0.0 and 100.0 (percentage)
            raw_score = citation_data.get("relevance_score", 50.0)
            if isinstance(raw_score, (int, float)):
                # Normalize to 0-100 range
                if raw_score > 100.0:
                    # Score > 100, cap at 100
                    normalized_score = 100.0
                elif raw_score < 0.0:
                    # Score < 0, set to 0
                    normalized_score = 0.0
                elif raw_score <= 1.0:
                    # Looks like old format (0.0-1.0), convert to percentage
                    normalized_score = raw_score * 100.0
                else:
                    # Already in 0-100 range
                    normalized_score = raw_score
            else:
                normalized_score = 50.0  # Default to 50% if invalid
                
            source_citations.append(SourceCitation(
                guideline_id=citation_data.get("guideline_id", ""),
                guideline_title=citation_data.get("guideline_title"),
                page_number=citation_data.get("page_number"),
                section=citation_data.get("section"),
                relevance_score=normalized_score
            ))
        
        # Create final recommendation
        return TherapyRecommendation(
            therapy_options=therapy_options,
            clinical_guidance=therapy_clinical_guidance,
            source_citations=source_citations,
            therapy_rationale=therapy_data.get("therapy_rationale", ""),
            confidence_level=therapy_data.get("confidence_level", "Mittel"),
            warnings=therapy_data.get("warnings", [])
        )
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to Novita AI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'Hello' in JSON format."}
                ],
                max_tokens=100,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            return {
                "status": "success",
                "message": "Connection to Novita AI successful",
                "model": self.model,
                "response": response.choices[0].message.content
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection failed: {str(e)}"
            }