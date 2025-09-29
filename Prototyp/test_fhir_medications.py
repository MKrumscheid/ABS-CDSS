#!/usr/bin/env python3
"""
Test script for FHIR medication parsing
Tests the medication parsing functionality with sample FHIR data
"""

import json
import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from fhir_service import FHIRService

# Sample FHIR Bundle data (your test case)
SAMPLE_FHIR_DATA = {
    "resourceType": "Bundle",
    "type": "collection",
    "entry": [
        {
            "fullUrl": "http://clinfhir.com/fhir/Patient/cfsb1759154394449",
            "resource": {
                "resourceType": "Patient",
                "id": "cfsb1759154394449",
                "generalPractitioner": [
                    {
                        "reference": "Practitioner/cfsb1759154415803"
                    }
                ],
                "birthDate": "1944-04-01",
                "gender": "male",
                "name": [
                    {
                        "text": "Diabetes",
                        "given": [
                            "Dieter"
                        ],
                        "family": "Diabetes"
                    }
                ]
            }
        },
        {
            "fullUrl": "http://clinfhir.com/fhir/Practitioner/cfsb1759154415803",
            "resource": {
                "resourceType": "Practitioner",
                "id": "cfsb1759154415803"
            }
        },
        {
            "fullUrl": "http://clinfhir.com/fhir/Condition/cfsb1759154440817",
            "resource": {
                "resourceType": "Condition",
                "id": "cfsb1759154440817",
                "subject": {
                    "reference": "Patient/cfsb1759154394449"
                },
                "recorder": {
                    "reference": "Practitioner/cfsb1759154415803"
                },
                "asserter": {
                    "reference": "Patient/cfsb1759154394449"
                },
                "code": {
                    "coding": [
                        {
                            "code": "K51.9",
                            "system": "http://hl7.org/fhir/sid/icd-10"
                        }
                    ],
                    "text": "Colitis ulcerosa, nicht näher bezeichnet"
                }
            }
        },
        {
            "fullUrl": "http://clinfhir.com/fhir/List/cfsb1759156207939",
            "resource": {
                "resourceType": "List",
                "id": "cfsb1759156207939",
                "subject": {
                    "reference": "Patient/cfsb1759154394449"
                },
                "status": "current",
                "mode": "working",
                "source": {
                    "reference": "Practitioner/cfsb1759154415803"
                }
            }
        },
        {
            "fullUrl": "http://clinfhir.com/fhir/MedicationStatement/cfsb1759156227700",
            "resource": {
                "resourceType": "MedicationStatement",
                "id": "cfsb1759156227700",
                "subject": {
                    "reference": "Patient/cfsb1759154394449"
                },
                "derivedFrom": [
                    {
                        "reference": "List/cfsb1759156207939"
                    }
                ],
                "reasonReference": [
                    {
                        "reference": "Condition/cfsb1759154440817"
                    }
                ],
                "status": "active",
                "medicationReference": {
                    "reference": "Medication/cfsb1759156300433"
                }
            }
        },
        {
            "fullUrl": "http://clinfhir.com/fhir/Medication/cfsb1759156300433",
            "resource": {
                "resourceType": "Medication",
                "id": "cfsb1759156300433",
                "status": "active",
                "code": {
                    "coding": [
                        {
                            "code": "07211125",
                            "system": "https://www.ifaffm.de/fhir/PZN"
                        }
                    ],
                    "text": "metex® 10mg 30 Tbl. N3"
                }
            }
        },
        {
            "fullUrl": "http://clinfhir.com/fhir/Observation/cfsb1759156489205",
            "resource": {
                "resourceType": "Observation",
                "id": "cfsb1759156489205",
                "subject": {
                    "reference": "Patient/cfsb1759154394449"
                },
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {
                                "code": "laboratory",
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category"
                            }
                        ],
                        "text": "Laborwert"
                    }
                ],
                "valueQuantity": {
                    "value": 55,
                    "unit": "mL/min/1.73 m²"
                },
                "code": {
                    "coding": [
                        {
                            "code": "98979-8",
                            "system": "http://loinc.org"
                        }
                    ],
                    "text": "GFR CKD-EPI"
                },
                "focus": [
                    {
                        "reference": "Patient/cfsb1759154394449"
                    }
                ]
            }
        },
        {
            "fullUrl": "http://clinfhir.com/fhir/MedicationStatement/cfsb1759156857571",
            "resource": {
                "resourceType": "MedicationStatement",
                "id": "cfsb1759156857571",
                "subject": {
                    "reference": "Patient/cfsb1759154394449"
                },
                "status": "active",
                "medicationReference": {
                    "reference": "Medication/cfsb1759156889848"
                },
                "derivedFrom": [
                    {
                        "reference": "List/cfsb1759156207939"
                    }
                ]
            }
        },
        {
            "fullUrl": "http://clinfhir.com/fhir/Medication/cfsb1759156889848",
            "resource": {
                "resourceType": "Medication",
                "id": "cfsb1759156889848",
                "code": {
                    "coding": [
                        {
                            "code": "04344044",
                            "system": "https://www.ifaffm.de/fhir/PZN"
                        }
                    ],
                    "text": "Valproat - 1 A Pharma® 500mg 200 Retardtabl. N3"
                }
            }
        },
        {
            "fullUrl": "http://clinfhir.com/fhir/Condition/cfsb1759156926047",
            "resource": {
                "resourceType": "Condition",
                "id": "cfsb1759156926047",
                "subject": {
                    "reference": "Patient/cfsb1759154394449"
                },
                "code": {
                    "coding": [
                        {
                            "code": "G40.3",
                            "system": "http://hl7.org/fhir/sid/icd-10"
                        }
                    ],
                    "text": "Generalisierte idiopathische Epilepsie und epileptische Syndrome"
                }
            }
        },
        {
            "fullUrl": "http://clinfhir.com/fhir/Observation/cfsb1759157139163",
            "resource": {
                "resourceType": "Observation",
                "id": "cfsb1759157139163",
                "subject": {
                    "reference": "Patient/cfsb1759154394449"
                },
                "status": "final",
                "code": {
                    "coding": [
                        {
                            "code": "29463-7",
                            "system": "http://loinc.org"
                        }
                    ],
                    "text": "Body weight"
                },
                "valueQuantity": {
                    "value": 66,
                    "unit": "kg"
                }
            }
        },
        {
            "fullUrl": "http://clinfhir.com/fhir/Observation/cfsb1759157227232",
            "resource": {
                "resourceType": "Observation",
                "id": "cfsb1759157227232",
                "subject": {
                    "reference": "Patient/cfsb1759154394449"
                },
                "code": {
                    "coding": [
                        {
                            "code": "8302-2",
                            "system": "http://loinc.org"
                        }
                    ],
                    "text": "Body height"
                },
                "valueQuantity": {
                    "value": 169,
                    "unit": "cm"
                },
                "status": "final"
            }
        }
    ]
}

def test_fhir_medication_parsing():
    """Test FHIR medication parsing with sample data"""
    print("=" * 80)
    print("🧪 FHIR Medication Parsing Test")
    print("=" * 80)
    
    # Initialize FHIR service
    fhir_service = FHIRService()
    
    print(f"📄 Testing with Bundle containing {len(SAMPLE_FHIR_DATA['entry'])} entries")
    
    try:
        # Import the FHIR Bundle class
        from fhir.resources.R4B.bundle import Bundle
        
        # Create Bundle object from our sample data
        print("\n🔍 Creating FHIR Bundle object...")
        bundle = Bundle(**SAMPLE_FHIR_DATA)
        
        print(f"   - Bundle type: {bundle.type}")
        print(f"   - Entry count: {len(bundle.entry) if bundle.entry else 0}")
        
        # Parse the bundle
        print("\n🔍 Parsing FHIR Bundle...")
        patient_data = fhir_service.parse_patient_data(bundle)
        
        print(f"\n✅ Parsing completed successfully!")
        print(f"📊 Results:")
        print(f"   - Patient ID: {patient_data.patient_id}")
        print(f"   - Name: {patient_data.name}")
        print(f"   - Age: {patient_data.age}")
        print(f"   - Gender: {patient_data.gender}")
        print(f"   - Weight: {patient_data.weight} kg")
        print(f"   - Height: {patient_data.height} cm")
        print(f"   - BMI: {patient_data.bmi}")
        print(f"   - GFR: {patient_data.gfr} mL/min/1.73m²")
        
        print(f"\n🏥 Conditions ({len(patient_data.conditions)}):")
        for i, condition in enumerate(patient_data.conditions, 1):
            print(f"   {i}. {condition}")
        
        print(f"\n💊 Medications ({len(patient_data.medications)}):")
        for i, medication in enumerate(patient_data.medications, 1):
            print(f"   {i}. {medication}")
        
        print(f"\n🔬 Lab Values ({len(patient_data.lab_values)}):")
        for i, lab_value in enumerate(patient_data.lab_values, 1):
            print(f"   {i}. {lab_value}")
        
        # Expected medications from the FHIR data
        expected_medications = [
            "metex® 10mg 30 Tbl. N3",
            "Valproat - 1 A Pharma® 500mg 200 Retardtabl. N3"
        ]
        
        print(f"\n🎯 Expected Medications:")
        for i, med in enumerate(expected_medications, 1):
            print(f"   {i}. {med}")
        
        # Check if medications match
        print(f"\n✅ Validation:")
        medications_found = len(patient_data.medications)
        medications_expected = len(expected_medications)
        
        if medications_found == medications_expected:
            print(f"   ✅ Medication count: {medications_found}/{medications_expected} ✓")
        else:
            print(f"   ❌ Medication count: {medications_found}/{medications_expected} ✗")
        
        # Check individual medications
        for expected_med in expected_medications:
            if expected_med in patient_data.medications:
                print(f"   ✅ Found: '{expected_med}' ✓")
            else:
                print(f"   ❌ Missing: '{expected_med}' ✗")
        
        return patient_data
        
    except Exception as e:
        print(f"\n❌ Error during parsing: {str(e)}")
        import traceback
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        return None

def test_raw_bundle_structure():
    """Test the raw structure of the FHIR bundle"""
    print("\n" + "=" * 80)
    print("🔍 Raw Bundle Structure Analysis")
    print("=" * 80)
    
    medication_statements = []
    medications = {}
    
    for entry in SAMPLE_FHIR_DATA['entry']:
        resource = entry['resource']
        resource_type = resource['resourceType']
        
        if resource_type == 'MedicationStatement':
            medication_statements.append(resource)
            print(f"📋 MedicationStatement {resource['id']}:")
            if 'medicationReference' in resource:
                print(f"   - medicationReference: {resource['medicationReference']}")
            if 'medicationCodeableConcept' in resource:
                print(f"   - medicationCodeableConcept: {resource['medicationCodeableConcept']}")
        
        elif resource_type == 'Medication':
            medications[resource['id']] = resource
            print(f"💊 Medication {resource['id']}:")
            if 'code' in resource:
                print(f"   - code: {resource['code']}")
    
    print(f"\n📊 Summary:")
    print(f"   - MedicationStatements found: {len(medication_statements)}")
    print(f"   - Medications found: {len(medications)}")
    
    return medication_statements, medications

if __name__ == "__main__":
    print("🚀 Starting FHIR Medication Parsing Tests\n")
    
    # Test 1: Raw structure analysis
    test_raw_bundle_structure()
    
    # Test 2: FHIR service parsing
    patient_data = test_fhir_medication_parsing()
    
    print("\n" + "=" * 80)
    print("🏁 Test Complete")
    print("=" * 80)
    
    if patient_data and len(patient_data.medications) >= 2:
        print("✅ Test PASSED: Medications parsed successfully!")
        sys.exit(0)
    else:
        print("❌ Test FAILED: Medications not parsed correctly!")
        sys.exit(1)