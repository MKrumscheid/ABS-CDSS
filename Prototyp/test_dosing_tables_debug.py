#!/usr/bin/env python3
"""
Debug script to analyze dosing tables loading and search
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from rag_service_advanced import AdvancedRAGService
from models import ClinicalQuery, Indication, Severity

def test_dosing_tables():
    print("🧪 Testing Dosing Tables Debug")
    print("=" * 50)
    
    # Initialize RAG service
    rag_service = AdvancedRAGService(data_dir="backend/data")
    
    # Check loaded dosing tables
    print(f"📊 Total dosing tables loaded: {len(rag_service.dosing_tables)}")
    
    # Search for "Osteomyelitis der Schädelbasis"
    search_term = "osteomyelitis der schädelbasis"
    matching_tables = []
    
    print("\n🔍 Searching for tables containing 'osteomyelitis der schädelbasis':")
    for i, table in enumerate(rag_service.dosing_tables):
        table_name_lower = table.table_name.lower()
        if search_term in table_name_lower:
            matching_tables.append((i, table))
            print(f"  ✅ Found: {table.table_name}")
    
    if not matching_tables:
        print(f"  ❌ No exact matches found for '{search_term}'")
        
        # Check for partial matches
        print(f"\n🔍 Checking for partial matches:")
        for i, table in enumerate(rag_service.dosing_tables):
            table_name_lower = table.table_name.lower()
            if "osteomyelitis" in table_name_lower or "schädelbasis" in table_name_lower:
                print(f"  🔸 Partial match: {table.table_name}")
    
    # Show first 10 table names for context
    print(f"\n📋 First 10 loaded dosing tables:")
    for i, table in enumerate(rag_service.dosing_tables[:10]):
        print(f"  {i+1:2d}. {table.table_name}")
    
    # Test actual search functionality
    print(f"\n🔍 Testing RAG search for Osteomyelitis der Schädelbasis:")
    query = ClinicalQuery(
        indication=Indication.OSTEOMYELITIS_DER_SCHAEDELBASIS,
        severity=Severity.MODERATE,
        free_text="Osteomyelitis der Schädelbasis"
    )
    
    # Search dosing tables
    dosing_results = rag_service._search_dosing_tables(query, top_k=10)
    
    print(f"\n💊 Search Results ({len(dosing_results)} tables):")
    for table in dosing_results:
        print(f"  - {table.table_name} (score: {table.score:.3f})")

if __name__ == "__main__":
    test_dosing_tables()