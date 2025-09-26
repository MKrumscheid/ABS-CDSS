#!/usr/bin/env python3
"""
Test script to verify that the backend now accepts all new indications for guideline upload
"""

import requests
import json

def test_indications_endpoint():
    """Test the /indications endpoint to see if it returns all new indications"""
    print("🧪 Testing /indications endpoint")
    
    try:
        response = requests.get("http://localhost:8000/indications")
        
        if response.status_code == 200:
            data = response.json()
            indications = data.get('indications', [])
            
            print(f"✅ /indications endpoint working")
            print(f"   Found {len(indications)} indications")
            
            # Show first 10 indications
            print("   First 10 indications:")
            for i, indication in enumerate(indications[:10]):
                print(f"     {i+1}. {indication['value']}: {indication['label']}")
            
            if len(indications) > 10:
                print(f"   ... and {len(indications) - 10} more")
                
            # Check if OTITIS_EXTERNA_MALIGNA is included
            otitis_found = any(ind['value'] == 'OTITIS_EXTERNA_MALIGNA' for ind in indications)
            if otitis_found:
                print("   ✅ OTITIS_EXTERNA_MALIGNA is included")
            else:
                print("   ❌ OTITIS_EXTERNA_MALIGNA is missing")
                
            return True
        else:
            print(f"   ❌ Request failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Connection error: {e}")
        return False

def test_upload_validation():
    """Test if the upload endpoint accepts new indications"""
    print("\n🧪 Testing upload validation")
    
    # Test data - we don't need to actually upload a file, just test the validation
    test_indications = [
        "CAP,HAP,AKUTE_EXAZERBATION_COPD",  # Old indications
        "OTITIS_EXTERNA_MALIGNA,MASTOIDITIS,EPIGLOTTITIS",  # New indications
        "SEPSIS,BAKTERIELLE_MENINGITIS,BAKTERIELLE_ENDOKARDITIS"  # More new indications
    ]
    
    for indications_str in test_indications:
        print(f"   Testing: {indications_str}")
        
        # Create a small test file
        files = {'file': ('test.txt', 'Test content', 'text/plain')}
        data = {
            'indications': indications_str,
            'guideline_id': 'test_guideline'
        }
        
        try:
            response = requests.post(
                "http://localhost:8000/upload/guideline",
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                print(f"     ✅ Upload accepted")
            elif response.status_code == 400:
                error_detail = response.json().get('detail', 'Unknown error')
                if 'Unknown indication' in error_detail:
                    print(f"     ❌ Still rejecting: {error_detail}")
                else:
                    print(f"     ⚠️  Other validation error: {error_detail}")
            else:
                print(f"     ❌ Unexpected status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"     ❌ Connection error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Backend Indication Support")
    print("=" * 50)
    
    # Test the indications endpoint
    indications_ok = test_indications_endpoint()
    
    # Test upload validation
    if indications_ok:
        test_upload_validation()
    else:
        print("⚠️  Skipping upload test due to /indications endpoint failure")
    
    print("\n" + "=" * 50)
    print("Make sure the backend server is running on localhost:8000")