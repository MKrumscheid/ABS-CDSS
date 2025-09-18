#!/usr/bin/env python3
"""
Test script to debug patient loading issues
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from fhir_service import FHIRService
import json

def test_patient(patient_id):
    print(f"=== Testing Patient {patient_id} ===")
    
    # Initialize FHIR service
    fhir = FHIRService()
    
    # Test 1: Search by ID
    print("1. Searching patient by ID...")
    try:
        patients = fhir.search_patients_by_id(patient_id)
        print(f"Found {len(patients)} patients")
        
        if patients:
            patient = patients[0]
            print(f"Patient ID: {patient.get('id')}")
            print(f"Patient Name: {patient.get('name')}")
            print()
        else:
            print("No patient found!")
            return
            
    except Exception as e:
        print(f"Error searching patient: {e}")
        return
    
    # Test 2: Get patient bundle
    print("2. Getting patient bundle...")
    try:
        bundle = fhir.get_patient_bundle(patient_id)
        if bundle:
            print(f"Bundle created successfully with {len(bundle.entry)} entries")
            
            # Show resource types in bundle
            resource_types = {}
            for i, entry in enumerate(bundle.entry):
                if entry.resource:
                    # Debug: print the resource object attributes
                    resource = entry.resource
                    print(f"Entry {i}: Resource type: {type(resource)}")
                    print(f"  Has resource_type: {hasattr(resource, 'resource_type')}")
                    print(f"  Has resourceType: {hasattr(resource, 'resourceType')}")
                    print(f"  Class name: {resource.__class__.__name__}")
                    if hasattr(resource, '__dict__'):
                        print(f"  Attributes: {list(resource.__dict__.keys())[:5]}")  # First 5 attributes
                    print()
                    
                    # Try to get resource type
                    res_type = None
                    if hasattr(resource, 'resource_type'):
                        res_type = resource.resource_type
                    elif hasattr(resource, 'resourceType'):
                        res_type = resource.resourceType
                    else:
                        res_type = resource.__class__.__name__
                        
                    resource_types[res_type] = resource_types.get(res_type, 0) + 1
            
            print("Resources in bundle:")
            for res_type, count in resource_types.items():
                print(f"  - {res_type}: {count}")
            print()
            
            # Test 3: Parse patient data from bundle
            print("3. Parsing patient data from bundle...")
            patient_data = fhir.parse_patient_data(bundle)
            print(f"Name: {patient_data.name}")
            print(f"Gender: {patient_data.gender}")
            print(f"Age: {patient_data.age}")
            print(f"Height: {patient_data.height} cm")
            print(f"Weight: {patient_data.weight} kg") 
            print(f"BMI: {patient_data.bmi}")
            print(f"Pregnancy Status: {patient_data.pregnancy_status}")
            print(f"Conditions: {patient_data.conditions}")
            print(f"Allergies: {patient_data.allergies}")
            print(f"Medications: {patient_data.medications}")
            print(f"Lab values: {len(patient_data.lab_values)} entries")
            
            if patient_data.lab_values:
                print("Lab values details:")
                for lab in patient_data.lab_values:
                    print(f"  - {lab.get('name')}: {lab.get('value')} {lab.get('unit')}")
                    
        else:
            print("Bundle creation failed!")
            
    except Exception as e:
        print(f"Error with bundle: {e}")
        
        # Test 4: Raw parsing fallback
        print("\n4. Using raw parsing fallback...")
        try:
            patient_data = fhir.parse_patient_data_raw(patient_id)
            if patient_data:
                print(f"Raw parsed data successful!")
                print(f"Name: {patient_data.name}")
                print(f"Gender: {patient_data.gender}")
                print(f"Age: {patient_data.age}")
                print(f"Height: {patient_data.height} cm")
                print(f"Weight: {patient_data.weight} kg")
                print(f"BMI: {patient_data.bmi}")
                print(f"Conditions: {patient_data.conditions}")
                print(f"Allergies: {patient_data.allergies}")
                print(f"Medications: {patient_data.medications}")
                print(f"Lab values: {len(patient_data.lab_values)} entries")
            else:
                print("Raw parsing also failed")
        except Exception as e2:
            print(f"Raw parsing error: {e2}")

if __name__ == "__main__":
    test_patient("cfsb1758022576326")