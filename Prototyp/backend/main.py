from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import aiofiles
from pathlib import Path

from models import ClinicalQuery, RAGResponse, Indication
from rag_service_advanced import RAGService

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

# Initialize RAG service
rag_service = RAGService()

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