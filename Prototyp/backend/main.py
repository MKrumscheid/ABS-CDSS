from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List, Optional
import uvicorn
import aiofiles
import os
from pathlib import Path
from openai import OpenAI
from sqlalchemy.orm import Session

from models import (
    ClinicalQuery, RAGResponse, Indication, Severity, InfectionSite, RiskFactor,
    PatientSearchQuery, PatientSearchResult, PatientDetailData, 
    TherapyRecommendationRequest, TherapyRecommendation, LLMConfiguration,
    SaveTherapyRecommendationRequest, SavedTherapyRecommendationResponse, SavedTherapyRecommendationListItem
)
from rag_service_advanced import AdvancedRAGService
from fhir_service import FHIRService
from therapy_context_builder import TherapyContextBuilder
from therapy_llm_service import TherapyLLMService
from database import get_db, create_tables, SavedTherapyRecommendation

# Helper functions for formatting medication data
def format_frequency(option):
    """Format frequency bounds into human-readable string"""
    if option.frequency_upper_bound and option.frequency_upper_bound != option.frequency_lower_bound:
        return f"{option.frequency_lower_bound}-{option.frequency_upper_bound}x {option.frequency_unit}"
    else:
        return f"{option.frequency_lower_bound}x {option.frequency_unit}"

def format_duration(option):
    """Format duration bounds into human-readable string"""
    if option.duration_lower_bound is None:
        return "Therapiedauer nicht spezifiziert"
    
    if option.duration_upper_bound and option.duration_upper_bound != option.duration_lower_bound:
        return f"{option.duration_lower_bound}-{option.duration_upper_bound} {option.duration_unit}"
    else:
        return f"{option.duration_lower_bound} {option.duration_unit}"

# Initialize FastAPI app
app = FastAPI(
    title="RAG Test Pipeline - Clinical Decision Support",
    description="API for testing RAG retrieval with medical guidelines",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:4000", "http://127.0.0.1:4000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
rag_service = AdvancedRAGService()
fhir_service = FHIRService()
therapy_context_builder = TherapyContextBuilder(rag_service, fhir_service)
therapy_llm_service = TherapyLLMService()

# Initialize database
try:
    create_tables()
    print("Database tables initialized successfully")
except Exception as e:
    print(f"Warning: Database initialization failed: {e}")

# Serve static files for frontend
try:
    frontend_path = Path(__file__).parent.parent / "frontend" / "build"
    if frontend_path.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_path / "static")), name="static")
except:
    pass

@app.get("/")
async def root():
    return {"message": "RAG Test Pipeline API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "rag-test-pipeline"}

@app.get("/device-info")
async def get_device_info():
    """Get information about the current device being used for inference"""
    try:
        device_info = rag_service.get_device_info()
        return {
            "status": "success",
            "device_info": device_info
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get device info: {str(e)}"
        }

@app.post("/upload/guideline")
async def upload_guideline(
    file: UploadFile = File(...),
    guideline_id: str = Form(None),
    indications: str = Form("")  # Explicitly use Form() for multipart data
):
    """Upload a guideline file (markdown or text) for processing"""
    
    # Debug logging
    print(f"🔍 DEBUG - Received indications parameter: '{indications}'")
    print(f"🔍 DEBUG - Indications type: {type(indications)}")
    print(f"🔍 DEBUG - Indications length: {len(indications) if indications else 'None'}")
    print(f"🔍 DEBUG - Raw indications repr: {repr(indications)}")
    
    # Validate file type - now supports both .txt and .md
    if not (file.filename.endswith('.txt') or file.filename.endswith('.md')):
        raise HTTPException(status_code=400, detail="Only .txt and .md files are supported")
    
    # Generate guideline_id if not provided
    if not guideline_id:
        # Remove file extension and clean up filename
        base_name = file.filename
        for ext in ['.txt', '.md']:
            if base_name.endswith(ext):
                base_name = base_name[:-len(ext)]
                break
        guideline_id = base_name.replace(' ', '_')
    
    # Parse indications - require explicit selection
    indication_list = []
    if not indications or indications.strip() == "":
        raise HTTPException(status_code=400, detail="Mindestens eine Indikation muss ausgewählt werden")
    
    try:
        for ind in indications.split(','):
            ind = ind.strip()
            
            # Try to find the indication in the Indication enum
            indication_found = False
            for indication_enum in Indication:
                # Check if the indication matches either the enum name or value
                enum_value = indication_enum.value if hasattr(indication_enum, 'value') else indication_enum.name
                if (ind.upper() == indication_enum.name.upper() or 
                    ind.upper() == enum_value.upper()):
                    indication_list.append(indication_enum)
                    indication_found = True
                    print(f"✅ Matched indication '{ind}' to enum {indication_enum.name}")
                    break
            
            if not indication_found:
                # Log unknown indication but don't fail
                print(f"Warning: Unknown indication '{ind}' ignored")
                print(f"Available indications: {[i.name for i in Indication]}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid indications: {e}")
    
    # Ensure at least one valid indication was parsed
    if not indication_list:
        available_indications = [i.name for i in Indication]
        raise HTTPException(
            status_code=400, 
            detail=f"Keine gültige Indikation erkannt. Verfügbare Optionen: {', '.join(available_indications[:10])}... (insgesamt {len(available_indications)} verfügbar)"
        )
    
    try:
        # Read file content
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # Process with RAG service
        result = rag_service.upload_guideline(
            content=text_content,
            filename=file.filename,
            guideline_id=guideline_id,
            indications=indication_list
        )
        
        return result
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/search", response_model=RAGResponse)
async def search_guidelines(query: ClinicalQuery):
    """Search guidelines based on clinical parameters"""
    try:
        result = rag_service.search(query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get current RAG service statistics"""
    return rag_service.get_stats()

@app.get("/indications")
async def get_indications():
    """Get available indications dynamically from the Indication enum"""
    indications = []
    for indication_enum in Indication:
        # Get display name using the method from models.py
        display_name = indication_enum.get_display_name()
        # Use the enum value (which the frontend expects) instead of the enum name
        enum_value = indication_enum.value if hasattr(indication_enum, 'value') else indication_enum.name
        indications.append({
            "value": enum_value,
            "label": display_name
        })
    
    return {"indications": indications}

@app.post("/test-query")
async def test_query_generation(query: ClinicalQuery):
    """Test query generation without performing actual search"""
    try:
        # Generate the search query
        search_text = rag_service._build_search_query(query)
        
        # Build query parts for analysis
        must_parts = rag_service._build_must_query(query)
        should_parts = rag_service._build_should_query(query)
        boost_parts = rag_service._build_boost_query()
        
        return {
            "status": "success",
            "query_analysis": {
                "input_parameters": {
                    "indication": query.indication.value,
                    "severity": query.severity,
                    "infection_site": query.infection_site,
                    "risk_factors": query.risk_factors,
                    "suspected_pathogens": query.suspected_pathogens,
                    "free_text": query.free_text
                },
                "must_terms": must_parts,
                "should_terms": should_parts,
                "boost_terms": boost_parts,
                "final_query": search_text,
                "query_length": len(search_text),
                "term_counts": {
                    "must": len(must_parts),
                    "should": len(should_parts), 
                    "boost": len(boost_parts)
                }
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error generating query: {str(e)}"
        }

@app.delete("/guidelines/{guideline_id}")
async def delete_guideline(guideline_id: str):
    """Delete a specific guideline and its embeddings"""
    try:
        result = rag_service.delete_guideline(guideline_id)
        return result
    except Exception as e:
        return {
            "success": False,
            "message": f"Error deleting guideline: {str(e)}"
        }

@app.delete("/guidelines")
async def delete_all_guidelines():
    """Delete all guidelines and embeddings"""
    try:
        result = rag_service.delete_all_data()
        return result
    except Exception as e:
        return {
            "success": False,
            "message": f"Error deleting all data: {str(e)}"
        }

@app.get("/guidelines")
async def list_guidelines():
    """List all available guidelines"""
    try:
        stats = rag_service.get_stats()
        return {
            "success": True,
            "guidelines": stats.get("guidelines", []),
            "total_count": stats.get("total_guidelines", 0),
            "total_chunks": stats.get("total_chunks", 0)
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error listing guidelines: {str(e)}"
        }

# ==== Therapy Recommendation Endpoints ====

@app.post("/therapy/recommend")
async def generate_therapy_recommendation(request: dict):
    """Generate therapy recommendations based on clinical parameters"""
    try:
        # Extract parameters from request dict
        indication = request.get("indication")
        severity = request.get("severity")
        infection_site = request.get("infection_site")
        risk_factors = request.get("risk_factors", [])
        suspected_pathogens = request.get("suspected_pathogens", [])
        free_text = request.get("free_text")
        patient_id = request.get("patient_id")
        max_therapy_options = request.get("max_therapy_options", 5)
        
        # Validate required fields
        if not indication:
            raise HTTPException(status_code=422, detail="indication is required")
        if not severity:
            raise HTTPException(status_code=422, detail="severity is required")
        
        # Create ClinicalQuery object from individual parameters
        clinical_query = ClinicalQuery(
            indication=indication,
            severity=severity,
            infection_site=infection_site,
            risk_factors=risk_factors,
            suspected_pathogens=suspected_pathogens,
            free_text=free_text
        )
        
        # 1. Build comprehensive context using TherapyContextBuilder
        context_data = therapy_context_builder.build_therapy_context(
            clinical_query=clinical_query,
            patient_id=patient_id,
            max_rag_results=5,  
            max_dosing_tables=5  
        )
        
        # 2. Check if we have sufficient context
        if not context_data.get("rag_results") and not context_data.get("dosing_tables"):
            raise HTTPException(
                status_code=404, 
                detail="Keine relevanten Leitlinien oder Dosierungstabellen gefunden"
            )
        
        # 3. Generate therapy recommendation using LLM
        therapy_recommendation = therapy_llm_service.generate_therapy_recommendation(
            context_data=context_data,
            max_options=max_therapy_options
        )
        
        # Transform to match frontend expectations with new structure
        recommendations = []
        for i, option in enumerate(therapy_recommendation.therapy_options):
            # Format active ingredients with their individual dosing parameters
            medication_data = {
                "active_ingredients": [
                    {
                        "name": ingredient.name,
                        "strength": ingredient.strength,
                        "frequency_lower_bound": ingredient.frequency_lower_bound,
                        "frequency_upper_bound": ingredient.frequency_upper_bound, 
                        "frequency_unit": ingredient.frequency_unit,
                        "duration_lower_bound": ingredient.duration_lower_bound,
                        "duration_upper_bound": ingredient.duration_upper_bound,
                        "duration_unit": ingredient.duration_unit,
                        "route": ingredient.route
                    }
                    for ingredient in option.active_ingredients
                ],
                "notes": option.notes,
                # Add medication-specific clinical guidance with new field structure
                "clinical_guidance": option.clinical_guidance.dict() if option.clinical_guidance else None
            }
            
            recommendations.append({
                "name": f"Therapie Option {i+1}",
                "priority": i+1,
                "medications": [medication_data],
                "clinical_guidance": therapy_recommendation.clinical_guidance.dict() if therapy_recommendation.clinical_guidance else None,
                "sources": [citation.dict() for citation in therapy_recommendation.source_citations]
            })
        
        # Create response that matches frontend expectations
        response_data = {
            "recommendations": recommendations,
            "therapy_options": [option.dict() for option in therapy_recommendation.therapy_options],  # Add therapy_options
            "therapy_rationale": therapy_recommendation.therapy_rationale,
            "confidence_level": therapy_recommendation.confidence_level,
            "warnings": therapy_recommendation.warnings,
            "source_citations": [citation.dict() for citation in therapy_recommendation.source_citations],
            "general_notes": therapy_recommendation.therapy_rationale,
            "context_summary": {
                "patient_available": context_data["patient_data"] is not None,
                "rag_results_count": len(context_data["rag_results"]),
                "dosing_tables_count": len(context_data["dosing_tables"])
            },
            # Add patient data summary for frontend display
            "patient_data": context_data["patient_data"] if context_data["patient_data"] else None,
            # Add formatted patient summary as shown to LLM
            "patient_summary": therapy_context_builder._format_patient_summary(context_data["patient_data"]) if context_data["patient_data"] else None,
            # Add LLM prompt information for debugging
            "llm_debug": {
                "system_prompt": therapy_recommendation.system_prompt,
                "user_prompt": therapy_recommendation.user_prompt,
                "model": therapy_recommendation.llm_model
            }
        }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Fehler bei der Therapieempfehlung: {str(e)}"
        )

@app.post("/therapy/context")
async def get_therapy_context(request: dict):
    """Get therapy context without generating recommendations (for debugging)"""
    try:
        # Extract parameters from request dict
        indication = request.get("indication")
        severity = request.get("severity")
        infection_site = request.get("infection_site")
        risk_factors = request.get("risk_factors", [])
        suspected_pathogens = request.get("suspected_pathogens", [])
        free_text = request.get("free_text")
        patient_id = request.get("patient_id")
        
        # Validate required fields
        if not indication:
            raise HTTPException(status_code=422, detail="indication is required")
        if not severity:
            raise HTTPException(status_code=422, detail="severity is required")
        
        # Create ClinicalQuery object
        clinical_query = ClinicalQuery(
            indication=indication,
            severity=severity,
            infection_site=infection_site,
            risk_factors=risk_factors,
            suspected_pathogens=suspected_pathogens,
            free_text=free_text
        )
        
        context_data = therapy_context_builder.build_therapy_context(
            clinical_query=clinical_query,
            patient_id=patient_id,
            max_rag_results=5,  # Reduced from 10
            max_dosing_tables=3  # Reduced from 5
        )
        
        # Get context summary for debugging
        context_summary = therapy_context_builder.get_context_summary(context_data)
        
        return {
            "success": True,
            "context_summary": context_summary,
            "context_data": {
                "patient_available": context_data["patient_data"] is not None,
                "rag_results_count": len(context_data["rag_results"]),
                "dosing_tables_count": len(context_data["dosing_tables"]),
                "context_length": len(context_data["context_text"]),
                "warnings": context_data["warnings"]
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Fehler beim Abrufen des Therapiekontexts: {str(e)}"
        }

@app.get("/therapy/test-llm")
async def test_llm_connection():
    """Test connection to LLM service"""
    try:
        result = therapy_llm_service.test_connection()
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"LLM test failed: {str(e)}"
        }

@app.post("/therapy/config")
async def update_llm_configuration(config: LLMConfiguration):
    """Update LLM configuration settings"""
    try:
        # Update the therapy LLM service configuration
        therapy_llm_service.endpoint = config.endpoint
        therapy_llm_service.model = config.model
        therapy_llm_service.max_tokens = config.max_tokens
        therapy_llm_service.temperature = config.temperature
        
        # Create a new client with the updated endpoint
        therapy_llm_service.client = OpenAI(
            base_url=config.endpoint,
            api_key=os.getenv("NOVITA_API_KEY")
        )
        
        return {
            "status": "success",
            "message": "LLM-Konfiguration erfolgreich aktualisiert",
            "config": {
                "endpoint": config.endpoint,
                "model": config.model,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Aktualisieren der LLM-Konfiguration: {str(e)}"
        )

@app.get("/therapy/config")
async def get_llm_configuration():
    """Get current LLM configuration settings"""
    try:
        return {
            "status": "success",
            "config": {
                "endpoint": getattr(therapy_llm_service, 'endpoint', 'https://api.novita.ai/v3/openai/chat/completions'),
                "model": getattr(therapy_llm_service, 'model', 'openai/gpt-oss-120b'),
                "max_tokens": getattr(therapy_llm_service, 'max_tokens', 24000),
                "temperature": getattr(therapy_llm_service, 'temperature', 0.6)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Abrufen der LLM-Konfiguration: {str(e)}"
        )

# ==== FHIR Patient Endpoints ====

@app.post("/patients/search")
async def search_patients(query: PatientSearchQuery):
    """Search for patients by ID or name+birthdate"""
    try:
        if query.search_type == "id":
            if not query.patient_id:
                raise HTTPException(status_code=400, detail="Patient ID is required for ID search")
            
            patients = fhir_service.search_patients_by_id(query.patient_id)
            
        elif query.search_type == "name_birthdate":
            if not all([query.given_name, query.family_name, query.birth_date]):
                raise HTTPException(
                    status_code=400, 
                    detail="Given name, family name, and birth date are required for name search"
                )
            
            patients = fhir_service.search_patients_by_name_and_birthdate(
                query.given_name, query.family_name, query.birth_date
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid search type")
        
        # Convert to search results
        results = []
        for patient in patients:
            try:
                # Parse patient data for search results
                patient_id = patient.get('id', '')
                gender = patient.get('gender', 'unknown')
                birth_date = patient.get('birthDate')
                
                # Parse name
                name = "Unbekannt"
                names = patient.get('name', [])
                if names:
                    first_name = names[0]
                    given = first_name.get('given', [])
                    family = first_name.get('family', '')
                    
                    if given and family:
                        name = f"{' '.join(given)} {family}"
                    elif first_name.get('text'):
                        name = first_name['text']
                    elif family:
                        name = family
                    elif given:
                        name = ' '.join(given)
                
                # Calculate age
                age = None
                if birth_date:
                    try:
                        from datetime import datetime, date
                        birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d").date()
                        today = date.today()
                        age = today.year - birth_date_obj.year
                        if today.month < birth_date_obj.month or (today.month == birth_date_obj.month and today.day < birth_date_obj.day):
                            age -= 1
                    except:
                        pass
                
                # Gender display
                gender_display = {
                    'male': 'Männlich',
                    'female': 'Weiblich',
                    'other': 'Divers',
                    'unknown': 'Unbekannt'
                }.get(gender, 'Unbekannt')
                
                results.append(PatientSearchResult(
                    patient_id=patient_id,
                    name=name,
                    gender=gender_display,
                    birth_date=birth_date,
                    age=age
                ))
                
            except Exception as e:
                print(f"Error parsing patient {patient.get('id', 'unknown')}: {str(e)}")
                continue
        
        return {
            "success": True,
            "patients": results,
            "total_found": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "message": f"Error searching patients: {str(e)}",
            "patients": []
        }

@app.get("/patients/{patient_id}")
async def get_patient_details(patient_id: str):
    """Get detailed patient information including all related data"""
    try:
        # First try to get patient bundle with all related resources
        bundle = fhir_service.get_patient_bundle(patient_id)
        
        if bundle:
            # Parse patient data from bundle
            patient_data = fhir_service.parse_patient_data(bundle)
        else:
            # Fallback: parse patient data directly from raw FHIR responses
            print(f"Bundle creation failed for patient {patient_id}, using raw parsing fallback")
            patient_data = fhir_service.parse_patient_data_raw(patient_id)
            
            if not patient_data:
                raise HTTPException(status_code=404, detail="Patient not found or no data available")
        
        return {
            "success": True,
            "patient": patient_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving patient details for {patient_id}: {str(e)}")
        return {
            "success": False,
            "message": f"Error retrieving patient details: {str(e)}"
        }

# ==== Saved Therapy Recommendations Endpoints ====

@app.post("/therapy/save", response_model=SavedTherapyRecommendationResponse)
async def save_therapy_recommendation(
    save_request: SaveTherapyRecommendationRequest,
    db: Session = Depends(get_db)
):
    """Save a therapy recommendation"""
    try:
        # Create new saved recommendation
        saved_recommendation = SavedTherapyRecommendation(
            title=save_request.title,
            request_data=save_request.request_data,
            therapy_recommendation=save_request.therapy_recommendation,
            patient_data=save_request.patient_data
        )
        
        db.add(saved_recommendation)
        db.commit()
        db.refresh(saved_recommendation)
        
        return SavedTherapyRecommendationResponse(
            id=saved_recommendation.id,
            title=saved_recommendation.title,
            created_at=saved_recommendation.created_at,
            request_data=saved_recommendation.request_data,
            therapy_recommendation=saved_recommendation.therapy_recommendation,
            patient_data=saved_recommendation.patient_data
        )
        
    except Exception as e:
        print(f"Error saving therapy recommendation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save therapy recommendation: {str(e)}")

@app.get("/therapy/saved", response_model=List[SavedTherapyRecommendationListItem])
async def get_saved_therapy_recommendations(db: Session = Depends(get_db)):
    """Get list of saved therapy recommendations (summary view)"""
    try:
        saved_recommendations = db.query(SavedTherapyRecommendation).order_by(
            SavedTherapyRecommendation.created_at.desc()
        ).all()
        
        result = []
        for recommendation in saved_recommendations:
            # Extract indication display name from request_data
            indication_display = "Unbekannte Indikation"
            patient_id = None
            
            if recommendation.request_data:
                # Try to get indication from different possible locations
                clinical_query = recommendation.request_data.get("clinical_query", {})
                indication = (
                    recommendation.request_data.get("indication") or  # Direct in request_data
                    clinical_query.get("indication")                 # Or in clinical_query
                )
                patient_id = recommendation.request_data.get("patient_id")
                
                if indication:
                    try:
                        indication_enum = Indication(indication)
                        indication_display = indication_enum.get_display_name()
                    except ValueError:
                        # If enum lookup fails, use the raw value
                        indication_display = indication
            
            result.append(SavedTherapyRecommendationListItem(
                id=recommendation.id,
                title=recommendation.title,
                created_at=recommendation.created_at,
                indication_display=indication_display,
                patient_id=patient_id
            ))
        
        return result
        
    except Exception as e:
        print(f"Error fetching saved therapy recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch saved recommendations: {str(e)}")

@app.get("/therapy/saved/{recommendation_id}", response_model=SavedTherapyRecommendationResponse)
async def get_saved_therapy_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific saved therapy recommendation"""
    try:
        recommendation = db.query(SavedTherapyRecommendation).filter(
            SavedTherapyRecommendation.id == recommendation_id
        ).first()
        
        if not recommendation:
            raise HTTPException(status_code=404, detail="Saved recommendation not found")
        
        return SavedTherapyRecommendationResponse(
            id=recommendation.id,
            title=recommendation.title,
            created_at=recommendation.created_at,
            request_data=recommendation.request_data,
            therapy_recommendation=recommendation.therapy_recommendation,
            patient_data=recommendation.patient_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching saved therapy recommendation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch saved recommendation: {str(e)}")

@app.delete("/therapy/saved/{recommendation_id}")
async def delete_saved_therapy_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db)
):
    """Delete a saved therapy recommendation"""
    try:
        recommendation = db.query(SavedTherapyRecommendation).filter(
            SavedTherapyRecommendation.id == recommendation_id
        ).first()
        
        if not recommendation:
            raise HTTPException(status_code=404, detail="Saved recommendation not found")
        
        db.delete(recommendation)
        db.commit()
        
        return {"message": "Saved recommendation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting saved therapy recommendation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete saved recommendation: {str(e)}")


# Serve React app for any other routes
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    """Serve React frontend for any unmatched routes"""
    frontend_path = Path(__file__).parent.parent / "frontend" / "build"
    index_file = frontend_path / "index.html"
    
    if index_file.exists():
        return FileResponse(str(index_file))
    else:
        return {"message": "Frontend not built. Please build React app first."}


if __name__ == "__main__":
    print("Starting RAG Test Pipeline API server...")
    print("API Documentation: http://localhost:8000/docs")
    print("Frontend (if available): http://localhost:8000")
    
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )