"""
FHIR Service for patient data retrieval from HAPI FHIR server
"""
import requests
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from fhir.resources.R4B.patient import Patient
from fhir.resources.R4B.bundle import Bundle
from fhir.resources.R4B.condition import Condition
from fhir.resources.R4B.observation import Observation
from fhir.resources.R4B.medicationstatement import MedicationStatement
from fhir.resources.R4B.allergyintolerance import AllergyIntolerance
from fhir.resources.R4B.medication import Medication
from pydantic import BaseModel


class PatientData(BaseModel):
    """Structured patient data for display"""
    patient_id: str
    name: str
    gender: str
    age: Optional[int] = None
    birth_date: Optional[str] = None
    height: Optional[float] = None  # in cm
    weight: Optional[float] = None  # in kg
    bmi: Optional[float] = None
    pregnancy_status: str = "Nicht Schwanger"  # Default for male or not specified
    conditions: List[str] = []  # Pre-existing conditions
    allergies: List[str] = []
    medications: List[str] = []
    lab_values: List[Dict[str, Any]] = []


class FHIRService:
    """Service for interacting with HAPI FHIR server"""
    
    def __init__(self, base_url: str = "https://hapi.fhir.org/baseR4"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/fhir+json',
            'Content-Type': 'application/fhir+json'
        })

    def search_patients_by_id(self, patient_id: str) -> List[Dict[str, Any]]:
        """Search for patients by ID"""
        try:
            url = f"{self.base_url}/Patient/{patient_id}"
            response = self.session.get(url)
            
            if response.status_code == 200:
                patient_data = response.json()
                # Return as list for consistency with name search
                return [patient_data]
            elif response.status_code == 404:
                return []
            else:
                print(f"Error searching patient by ID {patient_id}: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Exception searching patient by ID {patient_id}: {str(e)}")
            return []

    def search_patients_by_name_and_birthdate(self, given_name: str, family_name: str, birth_date: str) -> List[Dict[str, Any]]:
        """Search for patients by given name, family name, and birth date"""
        try:
            params = {
                'given': given_name,
                'family': family_name,
                'birthdate': birth_date
            }
            
            url = f"{self.base_url}/Patient"
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                bundle_data = response.json()
                if bundle_data.get('resourceType') == 'Bundle' and 'entry' in bundle_data:
                    return [entry['resource'] for entry in bundle_data['entry'] if entry.get('resource', {}).get('resourceType') == 'Patient']
                return []
            else:
                print(f"Error searching patients by name: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Exception searching patients by name: {str(e)}")
            return []

    def get_patient_bundle(self, patient_id: str) -> Optional[Bundle]:
        """Get complete patient bundle with all related resources"""
        try:
            # Search for all resources related to this patient
            resource_types = [
                'Condition', 'Observation', 'MedicationStatement', 
                'AllergyIntolerance', 'Medication'
            ]
            
            all_entries = []
            
            # Add the patient resource first
            patient_response = self.session.get(f"{self.base_url}/Patient/{patient_id}")
            if patient_response.status_code == 200:
                patient_data = patient_response.json()
                # Clean patient data to avoid validation issues
                patient_data = self._clean_resource_data(patient_data)
                all_entries.append({
                    "fullUrl": f"{self.base_url}/Patient/{patient_id}",
                    "resource": patient_data
                })
            
            # Get all related resources
            for resource_type in resource_types:
                try:
                    params = {'patient': patient_id, '_count': 50}  # Limit results
                    response = self.session.get(f"{self.base_url}/{resource_type}", params=params)
                    
                    if response.status_code == 200:
                        bundle_data = response.json()
                        if bundle_data.get('resourceType') == 'Bundle' and 'entry' in bundle_data:
                            for entry in bundle_data['entry']:
                                resource = entry.get('resource', {})
                                if resource.get('resourceType') == resource_type:
                                    # Clean resource data to avoid validation issues
                                    resource = self._clean_resource_data(resource)
                                    all_entries.append({
                                        "fullUrl": entry.get('fullUrl', f"{self.base_url}/{resource_type}/{resource.get('id')}"),
                                        "resource": resource
                                    })
                                    
                                    # For MedicationStatement, also fetch the referenced Medication
                                    if resource_type == 'MedicationStatement' and 'medicationReference' in resource:
                                        med_ref = resource['medicationReference'].get('reference', '')
                                        if med_ref.startswith('Medication/'):
                                            med_id = med_ref.split('/')[-1]
                                            med_response = self.session.get(f"{self.base_url}/Medication/{med_id}")
                                            if med_response.status_code == 200:
                                                med_data = med_response.json()
                                                med_data = self._clean_resource_data(med_data)
                                                all_entries.append({
                                                    "fullUrl": f"{self.base_url}/Medication/{med_id}",
                                                    "resource": med_data
                                                })
                                        
                except Exception as e:
                    print(f"Error fetching {resource_type} for patient {patient_id}: {str(e)}")
                    continue
            
            if all_entries:
                bundle_dict = {
                    "resourceType": "Bundle",
                    "type": "collection",
                    "entry": all_entries
                }
                return Bundle.model_validate(bundle_dict)
            
        except Exception as e:
            print(f"Exception getting patient bundle for {patient_id}: {str(e)}")
            
        return None

    def _clean_resource_data(self, resource_data: Dict) -> Dict:
        """Clean FHIR resource data to avoid validation issues"""
        if not isinstance(resource_data, dict):
            return resource_data
            
        # Create a deep copy to avoid modifying original
        import copy
        cleaned = copy.deepcopy(resource_data)
        
        # Remove or fix problematic fields that cause validation errors
        if 'text' in cleaned:
            text = cleaned['text']
            if isinstance(text, dict):
                # If div is None or empty, provide a minimal div
                if 'div' not in text or text.get('div') is None:
                    text['div'] = "<div xmlns=\"http://www.w3.org/1999/xhtml\">No narrative available</div>"
                # Ensure status is present
                if 'status' not in text:
                    text['status'] = 'generated'
        
        # Recursively clean nested resources if any
        for key, value in cleaned.items():
            if isinstance(value, dict):
                cleaned[key] = self._clean_resource_data(value)
            elif isinstance(value, list):
                cleaned[key] = [self._clean_resource_data(item) if isinstance(item, dict) else item for item in value]
                
        return cleaned

    def parse_patient_data(self, bundle: Bundle) -> PatientData:
        """Parse FHIR bundle into structured patient data"""
        patient_data = PatientData(
            patient_id="",
            name="Unbekannt",
            gender="unbekannt"
        )
        
        # Organize resources by type
        patient_resource = None
        conditions = []
        observations = []
        medication_statements = []
        allergies = []
        medications = {}  # id -> medication resource
        
        for entry in bundle.entry or []:
            resource = entry.resource
            if not resource:
                continue
                
            # Get resource type from class name
            resource_type = resource.__class__.__name__
            
            if resource_type == "Patient":
                patient_resource = resource
            elif resource_type == "Condition":
                conditions.append(resource)
            elif resource_type == "Observation":
                observations.append(resource)
            elif resource_type == "MedicationStatement":
                medication_statements.append(resource)
            elif resource_type == "AllergyIntolerance":
                allergies.append(resource)
            elif resource_type == "Medication":
                medications[resource.id] = resource

        # Parse patient basic info
        if patient_resource:
            patient_data.patient_id = patient_resource.id or ""
            patient_data.gender = self._parse_gender(patient_resource.gender)
            
            # Parse name
            patient_data.name = self._parse_patient_name(patient_resource.name)
            
            # Parse birth date and calculate age
            if hasattr(patient_resource, 'birthDate') and patient_resource.birthDate:
                patient_data.birth_date = str(patient_resource.birthDate)
                patient_data.age = self._calculate_age(patient_resource.birthDate)

        # Parse observations (height, weight, lab values, pregnancy status)
        height_cm, weight_kg = self._parse_observations(observations, patient_data)
        
        # Calculate BMI if both height and weight available
        if height_cm and weight_kg:
            patient_data.height = height_cm
            patient_data.weight = weight_kg
            patient_data.bmi = round(weight_kg / ((height_cm / 100) ** 2), 1)

        # Parse conditions
        patient_data.conditions = self._parse_conditions(conditions)
        
        # Parse allergies
        patient_data.allergies = self._parse_allergies(allergies)
        
        # Parse medications
        patient_data.medications = self._parse_medications(medication_statements, medications)
        
        return patient_data

    def parse_patient_data_raw(self, patient_id: str) -> Optional[PatientData]:
        """Fallback method to parse patient data directly from raw FHIR responses"""
        try:
            patient_data = PatientData(
                patient_id=patient_id,
                name="Unbekannt",
                gender="unbekannt"
            )
            
            # Get patient basic info
            patient_response = self.session.get(f"{self.base_url}/Patient/{patient_id}")
            if patient_response.status_code == 200:
                patient_raw = patient_response.json()
                
                # Parse basic patient info
                patient_data.patient_id = patient_raw.get('id', patient_id)
                patient_data.gender = self._parse_gender(patient_raw.get('gender'))
                
                # Parse name
                names = patient_raw.get('name', [])
                if names:
                    name = names[0]
                    given = name.get('given', [])
                    family = name.get('family', '')
                    if given and family:
                        patient_data.name = f"{' '.join(given)} {family}"
                    elif name.get('text'):
                        patient_data.name = name['text']
                    elif family:
                        patient_data.name = family
                
                # Parse birth date
                birth_date = patient_raw.get('birthDate')
                if birth_date:
                    patient_data.birth_date = birth_date
                    patient_data.age = self._calculate_age(birth_date)
            
            # Get observations
            obs_response = self.session.get(f"{self.base_url}/Observation", params={'patient': patient_id})
            if obs_response.status_code == 200:
                obs_bundle = obs_response.json()
                height_cm, weight_kg = None, None
                
                if obs_bundle.get('entry'):
                    for entry in obs_bundle['entry']:
                        obs = entry.get('resource', {})
                        if obs.get('code', {}).get('coding'):
                            for coding in obs['code']['coding']:
                                if coding.get('system') == 'http://loinc.org':
                                    code = coding.get('code')
                                    
                                    # Height
                                    if code == '8302-2' and obs.get('valueQuantity'):
                                        value = obs['valueQuantity'].get('value')
                                        unit = obs['valueQuantity'].get('unit', '')
                                        if value and unit in ['cm', 'centimeter']:
                                            height_cm = float(value)
                                    
                                    # Weight
                                    elif code == '29463-7' and obs.get('valueQuantity'):
                                        value = obs['valueQuantity'].get('value')
                                        unit = obs['valueQuantity'].get('unit', '')
                                        if value and unit in ['kg', 'kilogram']:
                                            weight_kg = float(value)
                                    
                                    # Pregnancy status
                                    elif code == '82810-3' and obs.get('valueCodeableConcept'):
                                        text = obs['valueCodeableConcept'].get('text')
                                        if text:
                                            patient_data.pregnancy_status = text
                                    
                                    # Lab values
                                    else:
                                        value_str = ""
                                        unit = ""
                                        display_name = coding.get('display', obs.get('code', {}).get('text', ''))
                                        
                                        if obs.get('valueQuantity'):
                                            value_str = str(obs['valueQuantity'].get('value', ''))
                                            unit = obs['valueQuantity'].get('unit', '')
                                        elif obs.get('valueString'):
                                            value_str = obs['valueString']
                                        
                                        if value_str and display_name:
                                            patient_data.lab_values.append({
                                                "name": display_name,
                                                "value": value_str,
                                                "unit": unit,
                                                "code": code
                                            })
                
                # Calculate BMI
                if height_cm and weight_kg:
                    patient_data.height = height_cm
                    patient_data.weight = weight_kg
                    patient_data.bmi = round(weight_kg / ((height_cm / 100) ** 2), 1)
            
            # Get conditions
            cond_response = self.session.get(f"{self.base_url}/Condition", params={'patient': patient_id})
            if cond_response.status_code == 200:
                cond_bundle = cond_response.json()
                if cond_bundle.get('entry'):
                    for entry in cond_bundle['entry']:
                        condition = entry.get('resource', {})
                        if condition.get('code', {}).get('text'):
                            patient_data.conditions.append(condition['code']['text'])
            
            # Get allergies
            allergy_response = self.session.get(f"{self.base_url}/AllergyIntolerance", params={'patient': patient_id})
            if allergy_response.status_code == 200:
                allergy_bundle = allergy_response.json()
                if allergy_bundle.get('entry'):
                    for entry in allergy_bundle['entry']:
                        allergy = entry.get('resource', {})
                        if allergy.get('code', {}).get('text'):
                            patient_data.allergies.append(allergy['code']['text'])
            
            # Get medications
            med_response = self.session.get(f"{self.base_url}/MedicationStatement", params={'patient': patient_id})
            if med_response.status_code == 200:
                med_bundle = med_response.json()
                if med_bundle.get('entry'):
                    for entry in med_bundle['entry']:
                        med_statement = entry.get('resource', {})
                        
                        # Try to get medication name from display
                        if med_statement.get('medicationReference', {}).get('display'):
                            patient_data.medications.append(med_statement['medicationReference']['display'])
                        elif med_statement.get('medicationCodeableConcept', {}).get('text'):
                            patient_data.medications.append(med_statement['medicationCodeableConcept']['text'])
            
            # Set default pregnancy status for males
            if patient_data.gender == "Männlich":
                patient_data.pregnancy_status = "Nicht Schwanger"
            
            return patient_data
            
        except Exception as e:
            print(f"Error in raw patient data parsing for {patient_id}: {str(e)}")
            return None

    def _parse_gender(self, gender: Optional[str]) -> str:
        """Parse FHIR gender to German display"""
        gender_map = {
            'male': 'Männlich',
            'female': 'Weiblich',
            'other': 'Divers',
            'unknown': 'Unbekannt'
        }
        return gender_map.get(gender, 'Unbekannt')

    def _parse_patient_name(self, names: Optional[List]) -> str:
        """Parse FHIR patient name"""
        if not names:
            return "Unbekannt"
            
        try:
            # Use first name entry
            name = names[0]
            
            # Try to get structured name
            given = name.given or []
            family = name.family or ""
            
            if given and family:
                return f"{' '.join(given)} {family}"
            elif name.text:
                return name.text
            elif family:
                return family
            elif given:
                return ' '.join(given)
            else:
                return "Unbekannt"
                
        except Exception as e:
            print(f"Error parsing patient name: {str(e)}")
            return "Unbekannt"

    def _calculate_age(self, birth_date) -> Optional[int]:
        """Calculate age from birth date"""
        try:
            if isinstance(birth_date, str):
                birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
            elif isinstance(birth_date, datetime):
                birth_date = birth_date.date()
            
            today = date.today()
            age = today.year - birth_date.year
            
            # Adjust if birthday hasn't occurred this year
            if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                age -= 1
                
            return age
        except Exception as e:
            print(f"Error calculating age: {str(e)}")
            return None

    def _parse_observations(self, observations: List, patient_data: PatientData) -> tuple[Optional[float], Optional[float]]:
        """Parse observations for height, weight, pregnancy status, and lab values"""
        height_cm = None
        weight_kg = None
        
        for obs in observations:
            try:
                if not hasattr(obs, 'code') or not obs.code or not hasattr(obs.code, 'coding') or not obs.code.coding:
                    continue
                    
                # Get the LOINC code
                loinc_code = None
                display_name = ""
                
                for coding in obs.code.coding:
                    if hasattr(coding, 'system') and coding.system == "http://loinc.org":
                        loinc_code = coding.code
                        display_name = coding.display or (obs.code.text if hasattr(obs.code, 'text') else "") or ""
                        break
                
                if not loinc_code:
                    continue
                
                # Height (Body height)
                if loinc_code == "8302-2":
                    if hasattr(obs, 'valueQuantity') and obs.valueQuantity and hasattr(obs.valueQuantity, 'value') and obs.valueQuantity.value:
                        if hasattr(obs.valueQuantity, 'unit') and obs.valueQuantity.unit in ["cm", "centimeter"]:
                            height_cm = float(obs.valueQuantity.value)
                        elif hasattr(obs.valueQuantity, 'unit') and obs.valueQuantity.unit in ["m", "meter"]:
                            height_cm = float(obs.valueQuantity.value) * 100
                
                # Weight (Body weight) 
                elif loinc_code == "29463-7":
                    if hasattr(obs, 'valueQuantity') and obs.valueQuantity and hasattr(obs.valueQuantity, 'value') and obs.valueQuantity.value:
                        if hasattr(obs.valueQuantity, 'unit') and obs.valueQuantity.unit in ["kg", "kilogram"]:
                            weight_kg = float(obs.valueQuantity.value)
                        elif hasattr(obs.valueQuantity, 'unit') and obs.valueQuantity.unit in ["g", "gram"]:
                            weight_kg = float(obs.valueQuantity.value) / 1000
                
                # Pregnancy status
                elif loinc_code == "82810-3":
                    if hasattr(obs, 'valueCodeableConcept') and obs.valueCodeableConcept and hasattr(obs.valueCodeableConcept, 'text') and obs.valueCodeableConcept.text:
                        patient_data.pregnancy_status = obs.valueCodeableConcept.text
                    elif patient_data.gender == "Männlich":
                        patient_data.pregnancy_status = "Nicht Schwanger"
                
                # Lab values - add all other observations as lab values
                else:
                    value_str = ""
                    unit = ""
                    
                    if hasattr(obs, 'valueQuantity') and obs.valueQuantity:
                        if hasattr(obs.valueQuantity, 'value'):
                            value_str = str(obs.valueQuantity.value)
                        if hasattr(obs.valueQuantity, 'unit'):
                            unit = obs.valueQuantity.unit or ""
                    elif hasattr(obs, 'valueString') and obs.valueString:
                        value_str = obs.valueString
                    elif hasattr(obs, 'valueCodeableConcept') and obs.valueCodeableConcept and hasattr(obs.valueCodeableConcept, 'text') and obs.valueCodeableConcept.text:
                        value_str = obs.valueCodeableConcept.text
                    
                    if value_str:
                        patient_data.lab_values.append({
                            "name": display_name,
                            "value": value_str,
                            "unit": unit,
                            "code": loinc_code
                        })
                        
            except Exception as e:
                print(f"Error parsing observation: {str(e)}")
                continue
        
        return height_cm, weight_kg

    def _parse_conditions(self, conditions: List) -> List[str]:
        """Parse FHIR conditions to list of condition names"""
        condition_names = []
        
        for condition in conditions:
            try:
                if hasattr(condition, 'code') and condition.code:
                    if hasattr(condition.code, 'text') and condition.code.text:
                        condition_names.append(condition.code.text)
                    elif hasattr(condition.code, 'coding') and condition.code.coding:
                        # Try to get display text from coding
                        for coding in condition.code.coding:
                            if hasattr(coding, 'display') and coding.display:
                                condition_names.append(coding.display)
                                break
                        else:
                            # If no display, use code
                            if condition.code.coding and len(condition.code.coding) > 0:
                                first_coding = condition.code.coding[0]
                                if hasattr(first_coding, 'code') and first_coding.code:
                                    condition_names.append(first_coding.code)
                            
            except Exception as e:
                print(f"Error parsing condition: {str(e)}")
                continue
                
        return condition_names

    def _parse_allergies(self, allergies: List) -> List[str]:
        """Parse FHIR allergies to list of allergy names"""
        allergy_names = []
        
        for allergy in allergies:
            try:
                if hasattr(allergy, 'code') and allergy.code:
                    if hasattr(allergy.code, 'text') and allergy.code.text:
                        allergy_names.append(allergy.code.text)
                    elif hasattr(allergy.code, 'coding') and allergy.code.coding:
                        # Try to get display text from coding
                        for coding in allergy.code.coding:
                            if hasattr(coding, 'display') and coding.display:
                                allergy_names.append(coding.display)
                                break
                        else:
                            # If no display, use code
                            if allergy.code.coding and len(allergy.code.coding) > 0:
                                first_coding = allergy.code.coding[0]
                                if hasattr(first_coding, 'code') and first_coding.code:
                                    allergy_names.append(first_coding.code)
                            
            except Exception as e:
                print(f"Error parsing allergy: {str(e)}")
                continue
                
        return allergy_names

    def _parse_medications(self, medication_statements: List, medications: Dict) -> List[str]:
        """Parse medication statements to get medication names"""
        medication_names = []
        
        for med_statement in medication_statements:
            try:
                # Try to get medication from reference
                if hasattr(med_statement, 'medicationReference') and med_statement.medicationReference:
                    ref_obj = med_statement.medicationReference
                    if hasattr(ref_obj, 'reference') and ref_obj.reference and ref_obj.reference.startswith('Medication/'):
                        med_id = ref_obj.reference.split('/')[-1]
                        
                        # First try to get medication name from display in statement
                        if hasattr(ref_obj, 'display') and ref_obj.display:
                            medication_names.append(ref_obj.display)
                        # Then look up the medication resource and get the name from code.text
                        elif med_id in medications:
                            medication = medications[med_id]
                            if hasattr(medication, 'code') and medication.code and hasattr(medication.code, 'text') and medication.code.text:
                                medication_names.append(medication.code.text)
                            else:
                                medication_names.append(f"Medikament ID: {med_id}")
                        else:
                            medication_names.append(f"Medikament ID: {med_id}")
                
                # Try to get from medication codeable concept if available
                elif hasattr(med_statement, 'medicationCodeableConcept') and med_statement.medicationCodeableConcept:
                    if hasattr(med_statement.medicationCodeableConcept, 'text') and med_statement.medicationCodeableConcept.text:
                        medication_names.append(med_statement.medicationCodeableConcept.text)
                    elif hasattr(med_statement.medicationCodeableConcept, 'coding') and med_statement.medicationCodeableConcept.coding:
                        for coding in med_statement.medicationCodeableConcept.coding:
                            if hasattr(coding, 'display') and coding.display:
                                medication_names.append(coding.display)
                                break
                        
            except Exception as e:
                print(f"Error parsing medication statement: {str(e)}")
                continue
                
        return medication_names