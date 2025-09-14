#!/usr/bin/env python3
"""
Mock test script to verify dosing tables search functionality without embedding model
"""

import os
import sys
from pathlib import Path
from typing import List, Dict

# Add parent directory to path to import models
sys.path.append(str(Path(__file__).parent))

from models import ClinicalQuery, Indication, Severity, InfectionSite, DosingTable

# Mock class that simulates the essential parts of AdvancedRAGService for dosing tables
class MockDosingTableService:
    def __init__(self):
        self.dosing_tables = []
        self.dosing_index = None
        self._load_dosing_tables()
    
    def _load_dosing_tables(self):
        """Load dosing tables from bundled markdown file"""
        from test_dosing_tables import parse_dosing_tables, extract_clinical_context_from_name, optimize_table_for_llm
        
        dosing_file_path = Path("data/dose_info/dosis_tabellen.md")
        
        if not dosing_file_path.exists():
            print(f"⚠️ Dosing tables file not found: {dosing_file_path}")
            return
        
        try:
            with open(dosing_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse tables
            tables_data = parse_dosing_tables(content)
            
            # Create DosingTable objects
            for table_data in tables_data:
                dosing_table = DosingTable(
                    table_id=table_data['table_id'],
                    table_name=table_data['table_name'],
                    table_html=table_data['table_html'],
                    score=0.0,
                    clinical_context=table_data['clinical_context']
                )
                self.dosing_tables.append(dosing_table)
            
            print(f"✅ Loaded {len(self.dosing_tables)} dosing tables")
            
        except Exception as e:
            print(f"❌ Error loading dosing tables: {e}")
    
    def search_dosing_tables_mock(self, query: ClinicalQuery, top_k: int = 3) -> List[DosingTable]:
        """Mock search for relevant dosing tables based on clinical query"""
        if not self.dosing_tables:
            return []
        
        results = []
        
        # Score each table based on clinical context matching
        for table in self.dosing_tables:
            score = self._calculate_clinical_context_match(query, table.clinical_context)
            
            if score > 0:  # Only include tables with some match
                result_table = DosingTable(
                    table_id=table.table_id,
                    table_name=table.table_name,
                    table_html=table.table_html,
                    score=score,
                    clinical_context=table.clinical_context
                )
                results.append(result_table)
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x.score, reverse=True)
        final_results = results[:top_k]
        
        print(f"💊 Found {len(final_results)} relevant dosing tables:")
        for table in final_results:
            print(f"  - {table.table_name[:60]}... (score: {table.score:.3f})")
        
        return final_results
    
    def _calculate_clinical_context_match(self, query: ClinicalQuery, table_context: Dict) -> float:
        """Calculate how well the table's clinical context matches the query"""
        if not table_context:
            return 0.0
        
        score = 0.0
        max_score = 0.0
        
        # Match indication (highest weight)
        max_score += 0.4
        if table_context.get('indication'):
            query_indication = str(query.indication.value if hasattr(query.indication, 'value') else query.indication)
            if table_context['indication'] == query_indication:
                score += 0.4
            elif any(term in table_context['indication'].lower() for term in query_indication.lower().split()):
                score += 0.2
        
        # Match severity (medium weight)
        max_score += 0.3
        if table_context.get('severity') and query.severity:
            if table_context['severity'] == query.severity:
                score += 0.3
            elif any(term in table_context['severity'].lower() for term in query.severity.lower().split()):
                score += 0.15
        
        # Match infection site (medium weight)
        max_score += 0.3
        if table_context.get('infection_site') and query.infection_site:
            query_site = str(query.infection_site.value if hasattr(query.infection_site, 'value') else query.infection_site)
            if table_context['infection_site'] == query_site:
                score += 0.3
            elif any(term in table_context['infection_site'].lower() for term in query_site.lower().split()):
                score += 0.15
        
        # Normalize score
        return score / max_score if max_score > 0 else 0.0

def main():
    """Test dosing tables search functionality"""
    print("🧪 Testing Dosing Tables Search...")
    
    # Initialize mock service
    service = MockDosingTableService()
    
    if not service.dosing_tables:
        print("❌ No dosing tables loaded, cannot test search")
        return
    
    # Test queries
    test_queries = [
        {
            "name": "CAP + MITTELSCHWER + LUNGE",
            "query": ClinicalQuery(
                indication=Indication.CAP,
                severity=Severity.MODERATE,
                infection_site=InfectionSite.LUNG,
                free_text="Pneumonie Dosierung"
            )
        },
        {
            "name": "HAP + SCHWER",
            "query": ClinicalQuery(
                indication=Indication.HAP,
                severity=Severity.SEVERE,
                free_text="nosokomial Antibiotika"
            )
        },
        {
            "name": "CAP only",
            "query": ClinicalQuery(
                indication=Indication.CAP,
                severity=Severity.LIGHT,
                free_text="ambulant erworbene Pneumonie"
            )
        }
    ]
    
    # Test each query
    for test in test_queries:
        print(f"\n🔍 Testing Query: {test['name']}")
        print(f"   Indication: {test['query'].indication}")
        print(f"   Severity: {test['query'].severity}")
        print(f"   Infection Site: {test['query'].infection_site}")
        print(f"   Free Text: {test['query'].free_text}")
        
        results = service.search_dosing_tables_mock(test['query'])
        
        if results:
            print(f"   ✅ Found {len(results)} relevant tables")
            for i, table in enumerate(results):
                print(f"     {i+1}. {table.table_name[:50]}... (context: {table.clinical_context})")
        else:
            print(f"   ⚠️ No relevant tables found")
    
    print(f"\n✅ Dosing tables search test completed!")

if __name__ == "__main__":
    main()