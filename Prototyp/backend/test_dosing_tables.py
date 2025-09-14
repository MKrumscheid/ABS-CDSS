#!/usr/bin/env python3
"""
Test script to verify dosing tables loading and parsing functionality
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict

# Add parent directory to path to import models
sys.path.append(str(Path(__file__).parent))

def parse_dosing_tables(content: str) -> List[Dict]:
    """Parse dosing tables from markdown content"""
    tables = []
    
    # Split content by table headers - improved pattern
    # Look for lines starting with # followed by "Tabelle" and capture everything until next # or end
    pattern = r'^# (Tabelle[^\n]+)\n'
    table_headers = re.finditer(pattern, content, re.MULTILINE)
    
    header_positions = []
    for match in table_headers:
        header_positions.append({
            'start': match.start(),
            'end': match.end(),
            'name': match.group(1).strip()
        })
    
    # Extract content for each table
    for i, header in enumerate(header_positions):
        table_name = header['name']
        
        # Get content from end of header to start of next header (or end of file)
        content_start = header['end']
        content_end = header_positions[i + 1]['start'] if i + 1 < len(header_positions) else len(content)
        
        table_content = content[content_start:content_end].strip()
        
        # Extract HTML table from this section
        table_match = re.search(r'<table[^>]*>.*?</table>', table_content, re.DOTALL)
        if table_match:
            table_html = table_match.group(0)
            
            # Clean up HTML for LLM consumption
            llm_optimized_html = optimize_table_for_llm(table_html)
            
            # Extract clinical context from table name
            clinical_context = extract_clinical_context_from_name(table_name)
            
            table_data = {
                'table_id': f"dosing_table_{len(tables) + 1:02d}",
                'table_name': table_name,
                'table_html': llm_optimized_html,
                'clinical_context': clinical_context
            }
            tables.append(table_data)
    
    return tables

def optimize_table_for_llm(html_table: str) -> str:
    """Optimize HTML table for LLM consumption with better formatting"""
    # Clean up HTML for better LLM readability
    cleaned = html_table
    
    # Convert to more readable format while preserving structure
    cleaned = re.sub(r'<tbody>', '', cleaned)
    cleaned = re.sub(r'</tbody>', '', cleaned)
    cleaned = re.sub(r'<tr>', '\n| ', cleaned)
    cleaned = re.sub(r'</tr>', ' |', cleaned)
    cleaned = re.sub(r'<td[^>]*>', '', cleaned)
    cleaned = re.sub(r'</td>', ' | ', cleaned)
    cleaned = re.sub(r'<th[^>]*>', '**', cleaned)
    cleaned = re.sub(r'</th>', '** | ', cleaned)
    
    # Clean up multiple spaces and pipes
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'\|\s*\|', '|', cleaned)
    cleaned = cleaned.strip()
    
    # Add table markers for LLM
    formatted_table = f"""
DOSING TABLE (LLM Format):
{cleaned}
END OF DOSING TABLE
"""
    return formatted_table.strip()

def extract_clinical_context_from_name(table_name: str) -> Dict:
    """Extract clinical context (indication, severity, infection_site) from table name"""
    context = {
        'indication': None,
        'severity': None,
        'infection_site': None,
        'keywords': []
    }
    
    name_lower = table_name.lower()
    
    # Extract indication
    if any(term in name_lower for term in ['cap', 'ambulant', 'community-acquired']):
        context['indication'] = 'CAP'
    elif any(term in name_lower for term in ['hap', 'nosokomial', 'hospital-acquired']):
        context['indication'] = 'HAP'
    elif any(term in name_lower for term in ['aecopd', 'copd']):
        context['indication'] = 'AECOPD'
    
    # Extract severity
    if any(term in name_lower for term in ['leicht', 'mild']):
        context['severity'] = 'LEICHT'
    elif any(term in name_lower for term in ['mittelschwer', 'moderat']):
        context['severity'] = 'MITTELSCHWER'
    elif any(term in name_lower for term in ['schwer', 'severe']):
        context['severity'] = 'SCHWER'
    elif any(term in name_lower for term in ['septisch', 'septic', 'schock']):
        context['severity'] = 'SEPTISCH'
    
    # Extract infection site
    if any(term in name_lower for term in ['pneumonie', 'lunge', 'respiratorisch']):
        context['infection_site'] = 'LUNGE'
    elif any(term in name_lower for term in ['harnweg', 'uti', 'urogenital']):
        context['infection_site'] = 'HARNTRAKT'
    elif any(term in name_lower for term in ['bakteriämie', 'sepsis', 'blut']):
        context['infection_site'] = 'BLUT'
    
    # Extract additional keywords for matching
    keywords = []
    keyword_patterns = [
        'initialtherapie', 'antibiotika', 'therapie', 'behandlung',
        'hospitalisiert', 'intensiv', 'beatmung', 'risiko'
    ]
    
    for keyword in keyword_patterns:
        if keyword in name_lower:
            keywords.append(keyword)
    
    context['keywords'] = keywords
    
    return context

def main():
    """Test dosing tables parsing"""
    print("🧪 Testing Dosing Tables Loading...")
    
    # Path to dosing tables file
    dosing_file_path = Path("data/dose_info/dosis_tabellen.md")
    
    if not dosing_file_path.exists():
        print(f"❌ Dosing tables file not found: {dosing_file_path}")
        print(f"Expected path: {dosing_file_path.absolute()}")
        return
    
    try:
        # Read the dosing tables file
        print(f"📖 Reading dosing tables from: {dosing_file_path}")
        with open(dosing_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📄 File size: {len(content)} characters")
        
        # Parse tables from the markdown content
        print("🔍 Parsing tables...")
        tables = parse_dosing_tables(content)
        
        print(f"✅ Successfully parsed {len(tables)} dosing tables")
        
        # Show details of first few tables
        for i, table in enumerate(tables[:5]):
            print(f"\n📋 Table {i+1}: {table['table_id']}")
            print(f"   Name: {table['table_name'][:80]}...")
            print(f"   Clinical Context: {table['clinical_context']}")
            print(f"   HTML Length: {len(table['table_html'])} chars")
        
        # Show statistics
        indications = {}
        severities = {}
        infection_sites = {}
        
        for table in tables:
            ctx = table['clinical_context']
            if ctx['indication']:
                indications[ctx['indication']] = indications.get(ctx['indication'], 0) + 1
            if ctx['severity']:
                severities[ctx['severity']] = severities.get(ctx['severity'], 0) + 1
            if ctx['infection_site']:
                infection_sites[ctx['infection_site']] = infection_sites.get(ctx['infection_site'], 0) + 1
        
        print(f"\n📊 Statistics:")
        print(f"   Indications: {indications}")
        print(f"   Severities: {severities}")
        print(f"   Infection Sites: {infection_sites}")
        
        print(f"\n✅ Dosing tables parsing test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing dosing tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()