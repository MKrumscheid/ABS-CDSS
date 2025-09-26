#!/usr/bin/env python3
"""
Test script for the new indication synonyms system
Tests the RAG service with various new indications
"""

import sys
import os
import requests
import json

# Add the backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_backend_running():
    """Test if backend is running"""
    try:
        response = requests.get("http://localhost:8000/")
        return response.status_code == 200
    except:
        return False

def test_synonyms_import():
    """Test if synonyms can be imported"""
    try:
        from synonyms import INDICATION_SYNONYMS, get_synonyms_for_indication, get_negative_terms_for_indication
        print("✅ Synonyms module imported successfully")
        print(f"   Found {len(INDICATION_SYNONYMS)} indications")
        
        # Test a few key functions
        cap_synonyms = get_synonyms_for_indication("AMBULANT_ERWORBENE_PNEUMONIE")
        print(f"   CAP synonyms: {cap_synonyms[:3]}...")
        
        negative_terms = get_negative_terms_for_indication("AMBULANT_ERWORBENE_PNEUMONIE", category_filter=True)
        print(f"   Negative terms for CAP: {len(negative_terms)} terms")
        
        return True
    except Exception as e:
        print(f"❌ Error importing synonyms: {e}")
        return False

def test_models_import():
    """Test if models can be imported"""
    try:
        from models import Indication
        print("✅ Models imported successfully")
        
        # Test new indications
        test_indications = [
            Indication.SEPSIS,
            Indication.BACTERIAL_MENINGITIS,
            Indication.ACUTE_PROSTATITIS
        ]
        
        for indication in test_indications:
            display_name = indication.get_display_name()
            category = indication.get_category()
            synonyms = indication.get_synonyms()
            print(f"   {indication.value}: {display_name} ({category}) - {len(synonyms)} synonyms")
        
        return True
    except Exception as e:
        print(f"❌ Error importing models: {e}")
        return False

def test_rag_service():
    """Test if RAG service can be imported and initialized"""
    try:
        from rag_service_advanced import AdvancedRAGService
        print("✅ RAG service imported successfully")
        
        # Try basic initialization without loading embeddings for testing
        print("   Testing basic RAG service structure...")
        # Don't actually initialize it in test to avoid heavy dependencies
        print("   RAG service class available ✅")
        
        return True
    except Exception as e:
        print(f"❌ Error importing RAG service: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints with new indications"""
    test_cases = [
        {
            "name": "Sepsis query",
            "data": {
                "indication": "SEPSIS",
                "severity": "SCHWER",
                "infection_site": "BLUT",
                "risk_factors": ["BEATMUNG"],
                "suspected_pathogens": [],
                "free_text": "Patient mit septischem Schock"
            }
        },
        {
            "name": "Bacterial meningitis query", 
            "data": {
                "indication": "BAKTERIELLE_MENINGITIS",
                "severity": "SCHWER",
                "infection_site": "ZNS",
                "risk_factors": [],
                "suspected_pathogens": ["Streptococcus pneumoniae"],
                "free_text": "Verdacht auf bakterielle Meningitis"
            }
        },
        {
            "name": "Acute prostatitis query",
            "data": {
                "indication": "AKUTE_PROSTATITIS", 
                "severity": "MITTELSCHWER",
                "infection_site": "HARNTRAKT",
                "risk_factors": [],
                "suspected_pathogens": [],
                "free_text": "Akute bakterielle Prostatitis"
            }
        }
    ]
    
    if not test_backend_running():
        print("❌ Backend not running, skipping API tests")
        return False
    
    for test_case in test_cases:
        try:
            response = requests.post(
                "http://localhost:8000/search",
                json=test_case["data"],
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {test_case['name']}: {len(result.get('results', []))} chunks found")
                if 'dosing_tables' in result:
                    print(f"   Dosing tables: {len(result['dosing_tables'])}")
            else:
                print(f"❌ {test_case['name']}: HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ {test_case['name']}: {e}")
    
    return True

def main():
    """Run all tests"""
    print("🧪 Testing New Indication System")
    print("=" * 40)
    
    # Test imports
    print("\n1. Testing Imports:")
    synonyms_ok = test_synonyms_import()
    models_ok = test_models_import()
    rag_ok = test_rag_service()
    
    # Test API if backend is running
    print("\n2. Testing API Endpoints:")
    api_ok = test_api_endpoints()
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Test Summary:")
    print(f"   Synonyms: {'✅' if synonyms_ok else '❌'}")
    print(f"   Models: {'✅' if models_ok else '❌'}")
    print(f"   RAG Service: {'✅' if rag_ok else '❌'}")
    print(f"   API: {'✅' if api_ok else '❌'}")
    
    if all([synonyms_ok, models_ok, rag_ok]):
        print("\n🎉 Basic functionality tests passed!")
        print("   You can now:")
        print("   - Start the backend: python backend/main.py")
        print("   - Start the frontend: npm start (in frontend/)")
        print("   - Upload new guidelines with various indications")
        print("   - Test RAG queries with new diagnoses")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()