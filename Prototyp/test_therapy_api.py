#!/usr/bin/env python3
"""
Test script for therapy recommendation API
"""
import requests
import json

# Test data
test_data = {
    "indication": "AMBULANT_ERWORBENE_PNEUMONIE",
    "severity": "MITTELSCHWER", 
    "infection_site": "LUNGE",
    "risk_factors": [],
    "suspected_pathogens": [],
    "free_text": "65-jähriger Patient mit typischen CAP-Symptomen",
    "patient_id": "cfsb1758022576326"
}

print("Testing therapy context generation...")
print(f"Request data: {json.dumps(test_data, indent=2)}")
print("-" * 80)

try:
    # Test context generation first
    response = requests.post("http://localhost:8000/therapy/context", json=test_data)
    print(f"Context Response Status: {response.status_code}")
    
    if response.status_code == 200:
        context_result = response.json()
        print("Context generation successful!")
        print(f"Context summary: {json.dumps(context_result, indent=2)}")
        
        print("\n" + "="*80)
        print("Testing therapy recommendation generation...")
        
        # Test therapy recommendation
        therapy_response = requests.post("http://localhost:8000/therapy/recommend", json=test_data)
        print(f"Therapy Response Status: {therapy_response.status_code}")
        
        if therapy_response.status_code == 200:
            therapy_result = therapy_response.json()
            print("Therapy recommendation successful!")
            print(f"Full LLM response: {json.dumps(therapy_result, indent=2, ensure_ascii=False)}")
            print(f"\nNumber of recommendations: {len(therapy_result.get('recommendations', []))}")
            
            # Print first recommendation details
            if therapy_result.get('recommendations'):
                first_rec = therapy_result['recommendations'][0]
                print(f"\nFirst recommendation: {first_rec.get('name')}")
                print(f"Priority: {first_rec.get('priority')}")
                print(f"Medications: {len(first_rec.get('medications', []))}")
            else:
                print("\n⚠️ No therapy recommendations found in response!")
                print("This might indicate an issue with LLM response parsing or structure.")
        else:
            print(f"Therapy recommendation failed: {therapy_response.text}")
            
    else:
        print(f"Context generation failed: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
except Exception as e:
    print(f"Error: {e}")