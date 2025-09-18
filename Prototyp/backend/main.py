from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List, Optional
import uvicorn
import aiofiles
import os
from pathlib import Path
from openai import OpenAI

from models import (
    ClinicalQuery, RAGResponse, Indication, Severity, InfectionSite, RiskFactor,
    PatientSearchQuery, PatientSearchResult, PatientDetailData, 
    TherapyRecommendationRequest, TherapyRecommendation, LLMConfiguration
)
from rag_service_advanced import AdvancedRAGService
from fhir_service import FHIRService
from therapy_context_builder import TherapyContextBuilder
from therapy_llm_service import TherapyLLMService

# Initialize FastAPI app
app = FastAPI(
    title="RAG Test Pipeline - Clinical Decision Support",
    description="API for testing RAG retrieval with medical guidelines",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
rag_service = AdvancedRAGService()
fhir_service = FHIRService()
therapy_context_builder = TherapyContextBuilder(rag_service, fhir_service)
therapy_llm_service = TherapyLLMService()

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
            ind = ind.strip().upper()
            if ind in ['CAP', 'AMBULANT_ERWORBENE_PNEUMONIE']:
                indication_list.append(Indication.CAP)
            elif ind in ['HAP', 'NOSOKOMIAL_ERWORBENE_PNEUMONIE']:
                indication_list.append(Indication.HAP)
            elif ind in ['AECOPD', 'AKUTE_EXAZERBATION_COPD']:
                indication_list.append(Indication.AECOPD)
            else:
                # Log unknown indication but don't fail
                print(f"Warning: Unknown indication '{ind}' ignored")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid indications: {e}")
    
    # Ensure at least one valid indication was parsed
    if not indication_list:
        raise HTTPException(status_code=400, detail="Keine gültige Indikation erkannt. Verfügbare Optionen: CAP, HAP, AECOPD")
    
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
    """Get available indications"""
    return {
        "indications": [
            {"value": "CAP", "label": "Ambulant erworbene Pneumonie"},
            {"value": "HAP", "label": "Nosokomial erworbene Pneumonie"}
        ]
    }

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
        negative_parts = rag_service._build_negative_query(query)
        
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
                "negative_terms": negative_parts,
                "final_query": search_text,
                "query_length": len(search_text),
                "term_counts": {
                    "must": len(must_parts),
                    "should": len(should_parts), 
                    "boost": len(boost_parts),
                    "negative": len(negative_parts)
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
        max_therapy_options = request.get("max_therapy_options", 3)
        
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
        
        # Transform to match frontend expectations
        recommendations = []
        for i, option in enumerate(therapy_recommendation.therapy_options):
            recommendations.append({
                "name": f"Therapie Option {i+1}",
                "priority": i+1,
                "medications": [option.dict()],
                "clinical_guidance": therapy_recommendation.clinical_guidance.dict(),
                "sources": [citation.dict() for citation in therapy_recommendation.source_citations]
            })
        
        # Create response that matches frontend expectations
        response_data = {
            "recommendations": recommendations,
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
                "model": getattr(therapy_llm_service, 'model', 'openai/gpt-oss-20b'),
                "max_tokens": getattr(therapy_llm_service, 'max_tokens', 4000),
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