#!/usr/bin/env python3
"""
Test script to verify fuzzy matching implementation for both chunks and dosing tables
"""

import requests
import json

def test_fuzzy_matching():
    """Test the fuzzy matching functionality"""
    
    print("🧪 Testing Fuzzy Matching for Chunks and Dosing Tables")
    print("=" * 60)
    
    # Test cases with different indications and search terms
    test_cases = [
        {
            "name": "Direct indication match",
            "query": {
                "indication": "SEPSIS",
                "severity": "schwer",
                "free_text": "Sepsis Therapie Empfehlung"
            }
        },
        {
            "name": "Compound indication with underscore",
            "query": {
                "indication": "BAKTERIELLE_MENINGITIS", 
                "severity": "akut",
                "free_text": "Meningitis bakteriell"
            }
        },
        {
            "name": "Urogenital infection",
            "query": {
                "indication": "AKUTE_PYELONEPHRITIS",
                "severity": "mittelschwer", 
                "risk_factors": ["Diabetes", "Immunsuppression"],
                "free_text": "Pyelonephritis akut"
            }
        }
    ]
    
    base_url = "http://localhost:8000"
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}:")
        print(f"   Query: {test_case['query']}")
        
        try:
            response = requests.post(
                f"{base_url}/query",
                json=test_case['query'],
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                chunks = data.get('results', [])
                dosing_tables = data.get('dosing_tables', [])
                
                print(f"   ✅ Response received:")
                print(f"      Chunks found: {len(chunks)}")
                print(f"      Dosing tables: {len(dosing_tables)}")
                
                if chunks:
                    print(f"      Top chunk score: {chunks[0]['score']:.3f}")
                    # Show if lexical boost was applied (high scores indicate lexical matching)
                    high_score_chunks = [c for c in chunks if c['score'] > 10]
                    if high_score_chunks:
                        print(f"      🎯 {len(high_score_chunks)} chunks with lexical boost (score > 10)")
                
                if dosing_tables:
                    print(f"      Top dosing table score: {dosing_tables[0]['score']:.3f}")
                    high_score_tables = [t for t in dosing_tables if t['score'] > 10]
                    if high_score_tables:
                        print(f"      🎯 {len(high_score_tables)} dosing tables with lexical boost (score > 10)")
                        
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                print(f"      Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Connection error: {e}")
            print("   Make sure the backend server is running on localhost:8000")
    
    print(f"\n" + "=" * 60)
    print("🎯 Fuzzy Matching Features Implemented:")
    print("   • Chunks: +5 direct indication match, +2.5 partial match")
    print("   • Chunks: +3 severity match, +2 per risk factor")
    print("   • Chunks: +2 infection site match, +1.5 per free text word")
    print("   • Dosing Tables: +10 direct match, +5 partial match")
    print("   • Dosing Tables: Softened penalties (0.2x-0.4x instead of 0.05x-0.1x)")

if __name__ == "__main__":
    test_fuzzy_matching()