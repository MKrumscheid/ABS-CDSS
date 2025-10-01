#!/usr/bin/env python3
"""
FHIR Environment Diagnosis Script
Checks FHIR-related dependencies and environment in production
"""

import sys
import os

def check_fhir_environment():
    print("=" * 60)
    print("🔍 FHIR Environment Diagnosis")
    print("=" * 60)
    
    # Python version
    print(f"🐍 Python Version: {sys.version}")
    print(f"📁 Python Path: {sys.executable}")
    
    # Check FHIR library
    try:
        import fhir
        print(f"✅ FHIR library imported successfully")
        print(f"📦 FHIR location: {fhir.__file__}")
        
        # Try to get version
        try:
            print(f"🏷️ FHIR version: {fhir.__version__}")
        except:
            print("⚠️ FHIR version not available")
            
    except ImportError as e:
        print(f"❌ FHIR library import failed: {e}")
        return False
    
    # Check specific FHIR components
    components = [
        ('fhir.resources', 'FHIR Resources'),
        ('fhir.resources.R4B', 'FHIR R4B'),
        ('fhir.resources.R4B.bundle', 'Bundle'),
        ('fhir.resources.R4B.patient', 'Patient'),
        ('fhir.resources.R4B.medicationstatement', 'MedicationStatement'),
        ('fhir.resources.R4B.medication', 'Medication'),
    ]
    
    print(f"\n📦 FHIR Components:")
    for module, name in components:
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError as e:
            print(f"   ❌ {name}: {e}")
    
    # Test Bundle creation
    print(f"\n🧪 Testing Bundle Creation:")
    try:
        from fhir.resources.R4B.bundle import Bundle
        
        # Simple test bundle
        test_data = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": []
        }
        
        bundle = Bundle(**test_data)
        print(f"   ✅ Bundle creation successful")
        print(f"   📊 Bundle type: {bundle.type}")
        
    except Exception as e:
        print(f"   ❌ Bundle creation failed: {e}")
        import traceback
        print(f"   📋 Traceback: {traceback.format_exc()}")
    
    # Test MedicationStatement creation
    print(f"\n💊 Testing MedicationStatement Creation:")
    try:
        from fhir.resources.R4B.medicationstatement import MedicationStatement
        from fhir.resources.R4B.fhirtypes import Reference
        
        test_med_statement = {
            "resourceType": "MedicationStatement",
            "id": "test123",
            "status": "active",
            "medicationReference": {
                "reference": "Medication/test456"
            }
        }
        
        med_statement = MedicationStatement(**test_med_statement)
        print(f"   ✅ MedicationStatement creation successful")
        print(f"   📊 ID: {med_statement.id}")
        print(f"   📊 Status: {med_statement.status}")
        
        if hasattr(med_statement, 'medicationReference'):
            print(f"   📊 Has medicationReference: True")
            ref = med_statement.medicationReference
            if hasattr(ref, 'reference'):
                print(f"   📊 Reference: {ref.reference}")
            else:
                print(f"   ⚠️ medicationReference has no 'reference' attribute")
        else:
            print(f"   ⚠️ No medicationReference attribute")
        
    except Exception as e:
        print(f"   ❌ MedicationStatement creation failed: {e}")
        import traceback
        print(f"   📋 Traceback: {traceback.format_exc()}")
    
    print(f"\n" + "=" * 60)
    print("🏁 Diagnosis Complete")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    check_fhir_environment()