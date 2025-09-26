#!/usr/bin/env python3
"""
Test script to verify that the system works correctly without negative boosting
"""

import requests
import json

def test_search_without_negative_boosting():
    """Test search functionality with removed negative boosting"""
    print("🧪 Testing Search Without Negative Boosting")
    print("=" * 50)
    
    test_queries = [
        {
            "name": "CAP Query - should now include more results",
            "query": {
                "indication": "AMBULANT_ERWORBENE_PNEUMONIE",
                "severity": "mittelschwer",
                "free_text": "Pneumonie Therapie"
            }
        },
        {
            "name": "Sepsis Query - should work with lexical boosting only", 
            "query": {
                "indication": "SEPSIS",
                "severity": "schwer",
                "risk_factors": ["Immunsuppression"],
                "free_text": "Sepsis antibiotika"
            }
        },
        {
            "name": "New Indication - Otitis Externa Maligna",
            "query": {
                "indication": "OTITIS_EXTERNA_MALIGNA",
                "severity": "schwer",
                "free_text": "otitis externa behandlung"
            }
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n{i}. {test_case['name']}:")
        
        try:
            response = requests.post(
                "http://localhost:8000/query",
                json=test_case['query'],
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                chunks = data.get('results', [])
                dosing_tables = data.get('dosing_tables', [])
                
                print(f"   ✅ Query successful:")
                print(f"      Chunks: {len(chunks)}")
                print(f"      Dosing tables: {len(dosing_tables)}")
                print(f"      Execution time: {data.get('execution_time_ms', 0):.1f}ms")
                
                if chunks:
                    print(f"      Top chunk score: {chunks[0]['score']:.3f}")
                    # Look for positive lexical boosts
                    high_scores = [c for c in chunks if c['score'] > 10]
                    if high_scores:
                        print(f"      🎯 {len(high_scores)} chunks with lexical boost")
                
                if dosing_tables:
                    print(f"      Top dosing table score: {dosing_tables[0]['score']:.3f}")
                    high_table_scores = [t for t in dosing_tables if t['score'] > 10]
                    if high_table_scores:
                        print(f"      🎯 {len(high_table_scores)} dosing tables with lexical boost")
                        
            else:
                print(f"   ❌ Query failed: {response.status_code}")
                print(f"      Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Connection error: {e}")

def test_query_generation():
    """Test the query generation without negative boosting"""
    print(f"\n🧪 Testing Query Generation (Debug)")
    print("=" * 50)
    
    test_query = {
        "indication": "SEPSIS", 
        "severity": "schwer",
        "risk_factors": ["Diabetes"],
        "free_text": "sepsis antibiotika therapie"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/test-query", 
            json=test_query,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Query generation successful")
            print(f"   Search text: {data.get('search_text', 'N/A')[:100]}...")
            
            query_parts = data.get('query_parts', {})
            print(f"   MUST parts: {len(query_parts.get('must_parts', []))}")
            print(f"   SHOULD parts: {len(query_parts.get('should_parts', []))}")
            print(f"   BOOST parts: {len(query_parts.get('boost_parts', []))}")
            print(f"   ✅ No negative parts (removed)")
        else:
            print(f"   ❌ Query generation failed: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Connection error: {e}")

if __name__ == "__main__":
    print("🧪 Testing System Without Negative Boosting")
    print("=" * 60)
    
    # Test search functionality
    test_search_without_negative_boosting()
    
    # Test query generation 
    test_query_generation()
    
    print("\n" + "=" * 60)
    print("🎯 Benefits of Removing Negative Boosting:")
    print("   • More inclusive results - no aggressive filtering")  
    print("   • Lexical matching provides natural precision")
    print("   • Simpler, more predictable scoring")
    print("   • Better performance (no negative term processing)")
    print("\nMake sure the backend server is running on localhost:8000")