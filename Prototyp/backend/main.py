from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from typing import List, Optional
import uvicorn
import aiofiles
import os
import time
import json
import asyncio
from pathlib import Path
from openai import OpenAI
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

# Add CORS middleware - Updated for cloud deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000", 
        "http://localhost:4000", 
        "http://127.0.0.1:4000",
        "https://*.koyeb.app",  # Allow all Koyeb subdomains
        "*"  # For development - should be restricted in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler to prevent app crashes
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle uncaught exceptions to prevent app crashes"""
    print(f"🚨 UNCAUGHT EXCEPTION: {str(exc)}")
    import traceback
    print(f"📋 UNCAUGHT EXCEPTION TRACEBACK: {traceback.format_exc()}")
    
    # Try to get request info for debugging
    try:
        print(f"🔍 Request URL: {request.url}")
        print(f"🔍 Request method: {request.method}")
    except:
        print("🔍 Could not get request info")
    
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
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

# Mount static files for frontend applications (production)
static_admin_path = Path(__file__).parent / "static" / "admin"
static_enduser_path = Path(__file__).parent / "static" / "enduser"

if static_admin_path.exists():
    # Mount admin static assets first
    admin_static = static_admin_path / "static"
    if admin_static.exists():
        app.mount("/admin/static", StaticFiles(directory=str(admin_static)), name="admin_static")
        print("✅ Admin frontend static files mounted at /admin/static")
    
    app.mount("/admin", StaticFiles(directory=str(static_admin_path), html=True), name="admin")
    print("✅ Admin frontend mounted at /admin")

if static_enduser_path.exists():
    # Mount enduser static assets
    enduser_static = static_enduser_path / "static"
    if enduser_static.exists():
        app.mount("/static", StaticFiles(directory=str(enduser_static)), name="static")
    print("✅ Enduser frontend static files mounted")

# Legacy support for local development
try:
    frontend_path = Path(__file__).parent.parent / "frontend" / "build"
    if frontend_path.exists() and not static_enduser_path.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_path / "static")), name="static")
        print("✅ Development frontend mounted")
except Exception as e:
    print(f"Development frontend mount failed: {e}")

@app.get("/")
async def root():
    return {"message": "RAG Test Pipeline API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "rag-test-pipeline"}

@app.get("/rag-status")
async def get_rag_status():
    """Get current RAG configuration status"""
    rag_enabled = os.getenv("ENABLE_RAG", "true").lower() == "true"
    return {
        "rag_enabled": rag_enabled,
        "mode": "RAG Active" if rag_enabled else "Validation Mode (RAG Disabled)"
    }

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check including service dependencies"""
    health_status = {
        "status": "healthy",
        "service": "rag-test-pipeline",
        "timestamp": time.time(),
        "checks": {}
    }
    
    # Check RAG service
    try:
        # Quick test of RAG service
        test_result = rag_service.search("test", top_k=1)
        health_status["checks"]["rag_service"] = "healthy"
    except Exception as e:
        health_status["checks"]["rag_service"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check LLM service
    try:
        # Test if LLM service is accessible (without making a request)
        if therapy_llm_service:
            health_status["checks"]["llm_service"] = "healthy"
        else:
            health_status["checks"]["llm_service"] = "not_initialized"
    except Exception as e:
        health_status["checks"]["llm_service"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check FHIR service
    try:
        if fhir_service:
            health_status["checks"]["fhir_service"] = "healthy"
        else:
            health_status["checks"]["fhir_service"] = "not_initialized"
    except Exception as e:
        health_status["checks"]["fhir_service"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/debug/fhir")
async def debug_fhir():
    """Debug endpoint to check FHIR environment in production"""
    import sys
    
    try:
        # Check FHIR library
        import fhir
        fhir_available = True
        fhir_location = fhir.__file__
        try:
            fhir_version = fhir.__version__
        except:
            fhir_version = "unknown"
    except ImportError as e:
        fhir_available = False
        fhir_location = None
        fhir_version = f"Import Error: {e}"
    
    # Check FHIR components
    components = {}
    fhir_modules = [
        'fhir.resources',
        'fhir.resources.R4B',
        'fhir.resources.R4B.bundle',
        'fhir.resources.R4B.patient',
        'fhir.resources.R4B.medicationstatement',
        'fhir.resources.R4B.medication',
    ]
    
    for module in fhir_modules:
        try:
            __import__(module)
            components[module] = "available"
        except ImportError as e:
            components[module] = f"error: {e}"
    
    # Test Bundle creation
    bundle_test = {}
    try:
        from fhir.resources.R4B.bundle import Bundle
        test_data = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": []
        }
        bundle = Bundle(**test_data)
        bundle_test["status"] = "success"
        bundle_test["type"] = bundle.type
    except Exception as e:
        bundle_test["status"] = "error"
        bundle_test["error"] = str(e)
    
    return {
        "python_version": sys.version,
        "python_executable": sys.executable,
        "fhir": {
            "available": fhir_available,
            "version": fhir_version,
            "location": fhir_location,
            "components": components,
            "bundle_test": bundle_test
        }
    }

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
        
        # Log start of processing for large files
        chunk_count_estimate = len(text_content) // 1000  # Rough estimate
        if chunk_count_estimate > 100:
            print(f"⏰ Processing large file '{file.filename}' (~{chunk_count_estimate} chunks estimated)")
            print(f"⏰ This may take 3-10 minutes due to rate limiting. Processing continues even if timeout occurs.")
        
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

# Store for processing status
processing_status = {}

@app.get("/therapy/status")
async def get_processing_status():
    """Get current therapy processing statistics"""
    try:
        # Check if services are working
        rag_healthy = rag_service is not None
        llm_healthy = therapy_llm_service is not None
        
        return {
            "status": "healthy" if rag_healthy and llm_healthy else "degraded",
            "services": {
                "rag_service": "healthy" if rag_healthy else "unavailable",
                "llm_service": "healthy" if llm_healthy else "unavailable"
            },
            "info": {
                "expected_processing_time": "60-180 seconds for complex therapy recommendations",
                "koyeb_timeout_info": "Cloud platform may show 503 after 60s, but processing continues",
                "recommendation": "Wait 2-3 minutes then retry if 503 error occurs"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/therapy/recommend-stream")
async def generate_therapy_recommendation_stream(request: dict):
    """Generate therapy recommendations with real-time progress updates via SSE"""
    
    async def generate_progress_stream():
        try:
            start_time = time.time()
            yield f"data: {json.dumps({'type': 'progress', 'message': '🏥 Starte Therapieempfehlung...', 'timestamp': time.time()})}\n\n"
            
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
                yield f"data: {json.dumps({'type': 'error', 'message': 'indication is required'})}\n\n"
                return
            if not severity:
                yield f"data: {json.dumps({'type': 'error', 'message': 'severity is required'})}\n\n"
                return
            
            yield f"data: {json.dumps({'type': 'progress', 'message': '📋 Parameter validiert', 'timestamp': time.time()})}\n\n"
            
            # Create ClinicalQuery object
            clinical_query = ClinicalQuery(
                indication=indication,
                severity=severity,
                infection_site=infection_site,
                risk_factors=risk_factors,
                suspected_pathogens=suspected_pathogens,
                free_text=free_text
            )
            
            # Step 1: Build context
            yield f"data: {json.dumps({'type': 'progress', 'message': '🔍 Suche relevante Leitlinien und Dosierungstabellen...', 'timestamp': time.time()})}\n\n"
            
            context_start = time.time()
            context_data = therapy_context_builder.build_therapy_context(
                clinical_query=clinical_query,
                patient_id=patient_id,
                max_rag_results=5,  
                max_dosing_tables=5  
            )
            context_time = time.time() - context_start
            
            # Create progress message safely
            rag_count = len(context_data.get("rag_results", []))
            dosing_count = len(context_data.get("dosing_tables", []))
            context_msg = f"✅ Kontext erstellt ({context_time:.1f}s) - {rag_count} Leitlinien, {dosing_count} Dosierungstabellen"
            yield f"data: {json.dumps({'type': 'progress', 'message': context_msg, 'timestamp': time.time()})}\n\n"
            
            # Check if we have sufficient context (only if RAG is enabled)
            rag_enabled = os.getenv("ENABLE_RAG", "true").lower() == "true"
            if rag_enabled and not context_data.get("rag_results") and not context_data.get("dosing_tables"):
                yield f"data: {json.dumps({'type': 'error', 'message': 'Keine relevanten Leitlinien oder Dosierungstabellen gefunden'})}\n\n"
                return
            
            # Step 2: Generate LLM recommendation with progress updates
            yield f"data: {json.dumps({'type': 'progress', 'message': '🤖 Generiere Therapieempfehlung mit KI...', 'timestamp': time.time()})}\n\n"
            
            # Start LLM generation in background
            llm_start = time.time()
            
            # Create a task for LLM generation
            async def generate_llm():
                return therapy_llm_service.generate_therapy_recommendation(
                    context_data=context_data,
                    max_options=max_therapy_options
                )
            
            # Start LLM task
            llm_task = asyncio.create_task(generate_llm())
            
            # Send keep-alive messages every 25 seconds while waiting for LLM
            while not llm_task.done():
                try:
                    # Wait for LLM or timeout after 25 seconds
                    therapy_recommendation = await asyncio.wait_for(llm_task, timeout=25.0)
                    break  # LLM finished
                except asyncio.TimeoutError:
                    # Send keep-alive message
                    elapsed = time.time() - llm_start
                    elapsed_msg = f"⏱️ KI arbeitet noch... ({elapsed:.0f}s vergangen)"
                    yield f"data: {json.dumps({'type': 'progress', 'message': elapsed_msg, 'timestamp': time.time()})}\n\n"
                    continue
            
            # Get the result
            therapy_recommendation = await llm_task
            llm_time = time.time() - llm_start
            
            llm_msg = f"✅ KI-Empfehlung generiert ({llm_time:.1f}s)"
            yield f"data: {json.dumps({'type': 'progress', 'message': llm_msg, 'timestamp': time.time()})}\n\n"
            
            # Step 3: Format response
            yield f"data: {json.dumps({'type': 'progress', 'message': '📦 Formatiere Antwort...', 'timestamp': time.time()})}\n\n"
            
            # Transform to match frontend expectations
            recommendations = []
            for i, option in enumerate(therapy_recommendation.therapy_options):
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
                    "clinical_guidance": option.clinical_guidance.dict() if option.clinical_guidance else None
                }
                
                recommendations.append({
                    "name": f"Therapie Option {i+1}",
                    "priority": i+1,
                    "medications": [medication_data],
                    "clinical_guidance": therapy_recommendation.clinical_guidance.dict() if therapy_recommendation.clinical_guidance else None,
                    "sources": [citation.dict() for citation in therapy_recommendation.source_citations]
                })
            
            # Create final response
            response_data = {
                "recommendations": recommendations,
                "therapy_options": [option.dict() for option in therapy_recommendation.therapy_options],
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
                "patient_data": context_data["patient_data"] if context_data["patient_data"] else None,
                "patient_summary": therapy_context_builder._format_patient_summary(context_data["patient_data"]) if context_data["patient_data"] else None,
                "llm_debug": {
                    "system_prompt": therapy_recommendation.system_prompt,
                    "user_prompt": therapy_recommendation.user_prompt,
                    "model": therapy_recommendation.llm_model
                }
            }
            
            total_time = time.time() - start_time
            
            # Send final result
            yield f"data: {json.dumps({'type': 'result', 'data': response_data, 'total_time': total_time})}\n\n"
            
            final_msg = f"🎉 Therapieempfehlung abgeschlossen ({total_time:.1f}s)"
            yield f"data: {json.dumps({'type': 'complete', 'message': final_msg})}\n\n"
            
        except Exception as e:
            print(f"❌ Stream error: {str(e)}")
            import traceback
            print(f"📋 Traceback: {traceback.format_exc()}")
            error_msg = f"Fehler bei der Therapieempfehlung: {str(e)}"
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
    
    return StreamingResponse(
        generate_progress_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

@app.post("/therapy/recommend")
async def generate_therapy_recommendation(request: dict):
    """Generate therapy recommendations based on clinical parameters"""
    try:
        print(f"🏥 Starting therapy recommendation generation...")
        start_time = time.time()
        
        # Monitor system resources at start
        try:
            import psutil
            memory_before = psutil.virtual_memory()
            print(f"💾 Memory before: {memory_before.percent:.1f}% used, {memory_before.available/(1024**3):.1f}GB available")
        except ImportError:
            print("💾 psutil not available for memory monitoring")
        
        # Extract parameters from request dict
        indication = request.get("indication")
        severity = request.get("severity")
        infection_site = request.get("infection_site")
        risk_factors = request.get("risk_factors", [])
        suspected_pathogens = request.get("suspected_pathogens", [])
        free_text = request.get("free_text")
        patient_id = request.get("patient_id")
        max_therapy_options = request.get("max_therapy_options", 5)
        
        print(f"📋 Request params: indication={indication}, severity={severity}, patient_id={patient_id}")
        
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
        print(f"🔍 Building therapy context...")
        context_start = time.time()
        
        try:
            context_data = therapy_context_builder.build_therapy_context(
                clinical_query=clinical_query,
                patient_id=patient_id,
                max_rag_results=5,  
                max_dosing_tables=5  
            )
            context_time = time.time() - context_start
            print(f"✅ Context built in {context_time:.2f}s")
        except Exception as context_error:
            print(f"❌ Context building failed: {str(context_error)}")
            import traceback
            print(f"📋 Context error traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Context building failed: {str(context_error)}")
        
        # Monitor memory after context building
        try:
            import psutil
            memory_after_context = psutil.virtual_memory()
            print(f"💾 Memory after context: {memory_after_context.percent:.1f}% used, {memory_after_context.available/(1024**3):.1f}GB available")
        except ImportError:
            pass
        
        # 2. Check if we have sufficient context (only if RAG is enabled)
        rag_enabled = os.getenv("ENABLE_RAG", "true").lower() == "true"
        if rag_enabled and not context_data.get("rag_results") and not context_data.get("dosing_tables"):
            raise HTTPException(
                status_code=404, 
                detail="Keine relevanten Leitlinien oder Dosierungstabellen gefunden"
            )
        
        # 3. Generate therapy recommendation using LLM
        print(f"🤖 Generating LLM recommendation...")
        llm_start = time.time()
        
        try:
            therapy_recommendation = therapy_llm_service.generate_therapy_recommendation(
                context_data=context_data,
                max_options=max_therapy_options
            )
            llm_time = time.time() - llm_start
            print(f"✅ LLM recommendation generated in {llm_time:.2f}s")
        except Exception as llm_error:
            print(f"❌ LLM generation failed: {str(llm_error)}")
            import traceback
            print(f"📋 LLM error traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"LLM generation failed: {str(llm_error)}")
        
        # Monitor memory after LLM
        try:
            import psutil
            memory_after_llm = psutil.virtual_memory()
            print(f"💾 Memory after LLM: {memory_after_llm.percent:.1f}% used, {memory_after_llm.available/(1024**3):.1f}GB available")
        except ImportError:
            pass
        
        # 4. Transform to match frontend expectations with new structure
        print(f"📦 Formatting response...")
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
        
        total_time = time.time() - start_time
        print(f"🎉 Therapy recommendation completed in {total_time:.2f}s (context: {context_time:.2f}s, LLM: {llm_time:.2f}s)")
        
        # Final memory check
        try:
            import psutil
            memory_final = psutil.virtual_memory()
            print(f"💾 Memory final: {memory_final.percent:.1f}% used, {memory_final.available/(1024**3):.1f}GB available")
        except ImportError:
            pass
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        total_time = time.time() - start_time if 'start_time' in locals() else 0
        print(f"❌ CRITICAL ERROR after {total_time:.2f}s: {str(e)}")
        import traceback
        print(f"📋 FULL TRACEBACK: {traceback.format_exc()}")
        
        # Try to get memory info for debugging
        try:
            import psutil
            memory_error = psutil.virtual_memory()
            print(f"💾 Memory at error: {memory_error.percent:.1f}% used, {memory_error.available/(1024**3):.1f}GB available")
        except ImportError:
            print("💾 Could not get memory info at error (psutil not available)")
        
        raise HTTPException(
            status_code=500, 
            detail=f"CRITICAL: Therapy recommendation failed: {str(e)}"
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


# Frontend routing for production deployment
@app.get("/{full_path:path}")
async def serve_frontend_app(full_path: str):
    """Serve frontend applications based on path"""
    
    # Skip API routes
    if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi"):
        raise HTTPException(status_code=404, detail="Not found")
    
    # Admin frontend
    if full_path.startswith("admin") or full_path == "admin":
        admin_index = Path(__file__).parent / "static" / "admin" / "index.html"
        if admin_index.exists():
            return FileResponse(str(admin_index))
        # Fallback to development
        dev_admin = Path(__file__).parent.parent / "frontend" / "build" / "index.html"
        if dev_admin.exists():
            return FileResponse(str(dev_admin))
    
    # Default: Enduser frontend (for root and all other paths)
    enduser_index = Path(__file__).parent / "static" / "enduser" / "index.html"
    if enduser_index.exists():
        return FileResponse(str(enduser_index))
    
    # Fallback to development build
    dev_frontend = Path(__file__).parent.parent / "frontend" / "build" / "index.html"
    if dev_frontend.exists():
        return FileResponse(str(dev_frontend))
    
    # No frontend available
    return {
        "message": "ABS-CDSS API Server", 
        "status": "Frontend not built",
        "admin": "/admin",
        "api_docs": "/docs"
    }


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