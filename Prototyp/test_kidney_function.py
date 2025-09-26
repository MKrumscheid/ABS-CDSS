"""
Test script for kidney function dosing adjustment functionality
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from backend.therapy_context_builder import TherapyContextBuilder

def test_kidney_dosing():
    """Test that kidney dosing table is included when GFR <= 60"""
    print("=== Testing Kidney Function Dosing Adjustment ===\n")
    
    # Create test patient data with reduced GFR
    patient_data = {
        "name": "Test Patient",
        "age": 75,
        "gender": "Männlich",
        "gfr": 45.0,  # Reduced kidney function
        "conditions": ["Pneumonia"],
        "allergies": [],
        "medications": [],
        "lab_values": {}
    }
    
    print(f"Test Patient - GFR: {patient_data['gfr']} ml/min/1.73m² (≤ 60 threshold)")
    print(f"Test Patient - Age: {patient_data['age']} years (> 70 threshold)")
    print()
    
    # Initialize context builder and test
    context_builder = TherapyContextBuilder()
    
    # Get additional context - should include both elderly info and kidney dosing
    additional_context = context_builder._get_additional_context(
        query="Pneumonia treatment",
        patient_data=patient_data,
        risk_factors=[]
    )
    
    print("Additional context sections included:")
    print("=" * 50)
    if additional_context:
        # Check for kidney dosing section
        if "DOSIERUNGSANPASSUNG BEI NIERENINSUFFIZIENZ" in additional_context:
            print("✅ Kidney dosing adjustment table INCLUDED (GFR ≤ 60)")
            print(f"   Patient GFR: {patient_data['gfr']} ml/min/1.73m²")
        else:
            print("❌ Kidney dosing adjustment table NOT included")
            
        # Check for elderly section
        if "ANTIBIOTIKATHERAPIE BEIM ALTEN MENSCHEN" in additional_context:
            print("✅ Elderly therapy information INCLUDED (Age > 70)")
            print(f"   Patient Age: {patient_data['age']} years")
        else:
            print("❌ Elderly therapy information NOT included")
            
        print("\n" + "="*50)
        print("PREVIEW OF ADDITIONAL CONTEXT:")
        print("="*50)
        print(additional_context[:1000] + "..." if len(additional_context) > 1000 else additional_context)
    else:
        print("❌ No additional context generated")

def test_normal_kidney_function():
    """Test that kidney dosing table is NOT included when GFR > 60"""
    print("\n=== Testing Normal Kidney Function (No Dosing Adjustment) ===\n")
    
    # Create test patient data with normal GFR
    patient_data = {
        "name": "Test Patient Normal",
        "age": 45,
        "gender": "Weiblich",
        "gfr": 85.0,  # Normal kidney function
        "conditions": ["UTI"],
        "allergies": [],
        "medications": [],
        "lab_values": {}
    }
    
    print(f"Test Patient - GFR: {patient_data['gfr']} ml/min/1.73m² (> 60 threshold)")
    print(f"Test Patient - Age: {patient_data['age']} years (< 70 threshold)")
    print()
    
    # Initialize context builder and test
    context_builder = TherapyContextBuilder()
    
    # Get additional context - should NOT include kidney dosing or elderly info
    additional_context = context_builder._get_additional_context(
        query="UTI treatment",
        patient_data=patient_data,
        risk_factors=[]
    )
    
    print("Additional context sections:")
    print("=" * 30)
    if additional_context:
        if "DOSIERUNGSANPASSUNG BEI NIERENINSUFFIZIENZ" in additional_context:
            print("❌ Kidney dosing adjustment table incorrectly INCLUDED")
        else:
            print("✅ Kidney dosing adjustment table correctly NOT included (GFR > 60)")
            
        if "ANTIBIOTIKATHERAPIE BEIM ALTEN MENSCHEN" in additional_context:
            print("❌ Elderly therapy information incorrectly INCLUDED")
        else:
            print("✅ Elderly therapy information correctly NOT included (Age < 70)")
    else:
        print("✅ No additional context (correct for normal patient)")

if __name__ == "__main__":
    test_kidney_dosing()
    test_normal_kidney_function()
    print("\n=== Test Complete ===")