"""
Synonyms dictionary for medical indications/diagnoses
This file contains all medical indications with their synonyms for RAG search optimization.
"""

from typing import Dict, List

# Dictionary containing all medical indications and their synonyms
# Organized alphabetically by main diagnosis name
INDICATION_SYNONYMS: Dict[str, List[str]] = {
    # Existing diagnoses
    "AKUTE_EXAZERBATION_COPD": [
        "AECOPD",
        "Akute Exazerbation der COPD",
        "COPD Exazerbation", 
        "chronisch obstruktive Lungenerkrankung",
        "COPD"
    ],
    "AMBULANT_ERWORBENE_PNEUMONIE": [
        "CAP",
        "ambulant erworbene Pneumonie",
        "community-acquired pneumonia",
        "Pneumonie ambulant",
        "ambulante Pneumonie"
    ],
    "NOSOKOMIAL_ERWORBENE_PNEUMONIE": [
        "HAP",
        "nosokomial erworbene Pneumonie", 
        "hospital-acquired pneumonia",
        "nosokomiale Pneumonie",
        "Krankenhaus-Pneumonie"
    ],
    
    # New diagnoses - alphabetically organized
    "AKUTE_EPIDIDYMITIS": [
        "akute Epididymitis",
        "akute Nebenhodenentzündung",
        "Epididymitis acuta"
    ],
    "AKUTE_PROSTATITIS": [
        "akute Prostatitis",
        "akute bakterielle Prostatitis",
        "akute Prostataentzündung",
        "Prostatitis acuta"
    ],
    "AKUTE_UNKOMPLIZIERTE_PYELONEPHRITIS": [
        "akute unkomplizierte Pyelonephritis",
        "akute unkomplizierte Nierenbeckenentzündung",
        "unkomplizierte Pyelonephritis"
    ],
    "BAKTERIELLE_ARTHRITIS": [
        "bakterielle Arthritis",
        "septische Arthritis",
        "infektiöse Arthritis",
        "bakterielle Gelenkinfektion",
        "Arthritis septica"
    ],
    "BAKTERIELLE_ENDOKARDITIS": [
        "bakterielle Endokarditis",
        "infektiöse Endokarditis",
        "IE",
        "Endokarditis"
    ],
    "BAKTERIELLE_GASTROINTESTINALE_INFEKTIONEN": [
        "bakterielle gastrointestinale Infektionen",
        "bakterielle Gastroenteritis",
        "bakterielle Enteritis",
        "bakterielle Enterokolitis",
        "GI-Infektionen"
    ],
    "BAKTERIELLE_MENINGITIS": [
        "bakterielle Meningitis",
        "eitrige Meningitis",
        "bakterielle Hirnhautentzündung",
        "purulente Meningitis",
        "Meningitis purulenta"
    ],
    "BAKTERIELLE_SINUSITIDEN_UND_KOMPLIKATIONEN": [
        "bakterielle Sinusitiden und deren Komplikationen",
        "bakterielle Rhinosinusitis",
        "akute bakterielle Sinusitis",
        "purulente Sinusitis",
        "Sinusitis bakteriell"
    ],
    "ENDOMETRITIS": [
        "Endometritis",
        "Gebärmutterschleimhautentzündung",
        "Endometriumentzündung"
    ],
    "ENDOPROTHESEN_FREMDKOERPER_ASSOZIIERTE_INFEKTIONEN": [
        "Fremdkörper-assoziierte Infektionen",
        "Endoprothesen-/Fremdkörper-assoziierte Infektionen",
        "Implantat-assoziierte Infektion",
        "Protheseninfektion",
        "periprothetische Infektion",
        "Periprosthetic Joint Infection (PJI)",
        "PJI"
    ],
    "EPIDIDYMOORCHITIS": [
        "Epididymoorchitis",
        "Epididymo-Orchitis",
        "Nebenhoden-Hoden-Entzündung",
        "Epididymo-Orchitis"
    ],
    "EPIGLOTTITIS": [
        "Epiglottitis",
        "Supraglottitis",
        "Kehldeckelentzündung",
        "Epiglottitits acuta"
    ],
    "HAEMATOGENE_OSTEOMYELITIS": [
        "hämatogene Osteomyelitis",
        "akute hämatogene Osteomyelitis",
        "AHO",
        "hämatogene Knochenmarksentzündung",
        "Osteomyelitis haematogena"
    ],
    "INFIZIERTE_BISSWUNDEN": [
        "Bissverletzungen",
        "infizierte Bisswunden",
        "Bisswundinfektion",
        "Tierbissinfektion",
        "Menschenbissinfektion",
        "Bisswunde infiziert"
    ],
    "INVASIVE_INTRAABDOMINELLE_MYKOSEN": [
        "invasive intraabdominelle Mykosen",
        "intraabdominelle Pilzinfektion",
        "intraabdominelle Candidiasis",
        "Candidaperitonitis",
        "abdominelle Mykosen"
    ],
    "KOMPLIZIERTE_NOSOKOMIALE_HARNWEGSINFEKTION": [
        "komplizierte Harnwegsinfektion",
        "nosokomiale Harnwegsinfektion",
        "komplizierte HWI",
        "nosokomiale HWI",
        "komplizierte UTI",
        "cUTI"
    ],
    "MASTOIDITIS": [
        "Mastoiditis",
        "Warzenfortsatzentzündung",
        "Mastoidentzündung",
        "Mastoiditis acuta"
    ],
    "NASENFURUNKEL": [
        "Nasenfurunkel",
        "Furunkel des Nasenvorhofs",
        "Furunkel der Nase",
        "Furunculosis nasi"
    ],
    "NEKROTISIERENDE_PANKREATITIS_INFIZIERTE_NEKROSEN": [
        "nekrotisierende Pankreatitis mit infizierten Nekrosen",
        "infizierte nekrotisierende Pankreatitis",
        "infizierte Pankreasnekrose",
        "nekrotisierende Pankreatitis infiziert"
    ],
    "ODONTOGENE_INFEKTIONEN_AUSBREITUNGSTENDENZ": [
        "Dentogener Logenabszess",
        "odontogene Infektionen mit Ausbreitungstendenz, ggf. mit lokalen oder systemischen Komplikationen",
        "odontogene Infektionen",
        "dentogene Infektionen",
        "dentoalveoläre Infektionen",
        "odontogener Abszess"
    ],
    "OHRMUSCHELPERICHONDRITIS": [
        "Ohrmuschelperichondritis",
        "Perichondritis auriculae",
        "Perichondritis der Ohrmuschel",
        "Ohrknorpelentzündung"
    ],
    "OSTEOMYELITIS_KIEFER": [
        "Osteomyelitis der Kiefer",
        "Kieferosteomyelitis",
        "Osteomyelitis mandibulae",
        "Osteomyelitis maxillae"
    ],
    "OSTEOMYELITIS_SCHAEDELBASIS": [
        "Osteomyelitis der Schädelbasis",
        "Schädelbasisosteomyelitis",
        "Osteomyelitis der Basis cranii",
        "Skull-base osteomyelitis"
    ],
    "OTITIS_EXTERNA_MALIGNA": [
        "Otitis externa maligna",
        "nekrotisierende Otitis externa",
        "maligne Otitis externa",
        "Necrotizing external otitis"
    ],
    "PELVEOPERITONITIS": [
        "Pelveoperitonitis",
        "Beckenperitonitis",
        "pelvine Peritonitis"
    ],
    "PERITONITIS": [
        "Peritonitis",
        "Bauchfellentzündung",
        "Peritonealentzündung"
    ],
    "PERITONSILLITIS": [
        "Peritonsilitis",
        "Peritonsillarphlegmone",
    ],
    "PERITONSILLARABSZESS": [
        "Peritonsillarabszess",
        "Quinsy",
        "Abszess neben der Gaumenmandel"
    ],
    "POSTTRAUMATISCHE_POSTOPERATIVE_OSTEOMYELITIS": [
        "posttraumatische/postoperative Osteomyelitis",
        "posttraumatische Osteomyelitis",
        "postoperative Osteomyelitis",
        "chronische Osteomyelitis nach Trauma/OP"
    ],
    "PROSTATAABSZESS": [
        "Prostataabszess",
        "Abszess der Prostata",
        "Prostata-Abszess"
    ],
    "SALPINGITIS": [
        "Salpingitis",
        "Eileiterentzündung",
        "Adnexitis",
        "Salpingitis acuta"
    ],
    "SEPSIS": [
        "Sepsis",
        "Blutvergiftung",
        "Septikämie",
        "systemische Infektion"
    ],
    "SIALADENITIS": [
        "Sialadenitis",
        "Speicheldrüsenentzündung",
        "Parotitis",
        "Submandibulitis"
    ],
    "SPONDYLODISCITIS": [
        "Spondylodiscitis",
        "Spondylitis/Diskitis",
        "Wirbelkörper-/Bandscheibeninfektion",
        "infektiöse Spondylitis"
    ],
    "STERNUMOSTEOMYELITIS": [
        "Sternumosteomyelitis",
        "Sternalosteomyelitis",
        "Osteomyelitis des Sternums"
    ],
    "TUBOOVARIALABSZESS": [
        "Tuboovarialabszess",
        "tubo-ovarieller Abszess",
        "TOA"
    ],
    "UROSEPSIS": [
        "Urosepsis",
        "urogenitale Sepsis",
        "Sepsis aus dem Harntrakt"
    ],
    "ZERVIKOFAZIALE_AKTINOMYKOSE": [
        "zervikofaziale Aktinomykose",
        "cervicofaciale Aktinomykose",
        "Aktinomykose des Kopf-Hals-Bereichs",
        "Lumpy jaw"
    ]
}

def get_synonyms_for_indication(indication_key: str) -> List[str]:
    """
    Get synonyms for a specific indication
    
    Args:
        indication_key: The key of the indication (e.g., "CAP", "HAP")
    
    Returns:
        List of synonyms for the indication
    """
    return INDICATION_SYNONYMS.get(indication_key, [indication_key])

def get_all_indication_keys() -> List[str]:
    """
    Get all available indication keys
    
    Returns:
        List of all indication keys
    """
    return list(INDICATION_SYNONYMS.keys())

def get_negative_terms_for_indication(target_indication: str, category_filter: bool = True) -> List[str]:
    """
    Get negative terms (synonyms of other indications) for better search precision
    
    Args:
        target_indication: The indication we're searching for
        category_filter: If True, only return negative terms from related categories
        
    Returns:
        List of terms to negatively boost
    """
    # Category mapping for related indications (for smarter negative boosting)
    categories = {
        "respiratory": [
            "AMBULANT_ERWORBENE_PNEUMONIE",
            "NOSOKOMIAL_ERWORBENE_PNEUMONIE", 
            "AKUTE_EXAZERBATION_COPD",
            "EPIGLOTTITIS"
        ],
        "hno": [
            "OTITIS_EXTERNA_MALIGNA",
            "OSTEOMYELITIS_SCHAEDELBASIS",
            "MASTOIDITIS",
            "EPIGLOTTITIS",
            "OHRMUSCHELPERICHONDRITIS",
            "NASENFURUNKEL",
            "PERITONSILLITIS",
            "PERITONSILLARABSZESS",
            "BAKTERIELLE_SINUSITIDEN_UND_KOMPLIKATIONEN",
            "SIALADENITIS",
            "ZERVIKOFAZIALE_AKTINOMYKOSE"
        ],
        "dental": [
            "ODONTOGENE_INFEKTIONEN_AUSBREITUNGSTENDENZ",
            "OSTEOMYELITIS_KIEFER"
        ],
        "abdominal": [
            "PERITONITIS",
            "NEKROTISIERENDE_PANKREATITIS_INFIZIERTE_NEKROSEN",
            "INVASIVE_INTRAABDOMINELLE_MYKOSEN",
            "BAKTERIELLE_GASTROINTESTINALE_INFEKTIONEN"
        ],
        "urogenital": [
            "AKUTE_UNKOMPLIZIERTE_PYELONEPHRITIS",
            "KOMPLIZIERTE_NOSOKOMIALE_HARNWEGSINFEKTION",
            "UROSEPSIS",
            "AKUTE_PROSTATITIS",
            "PROSTATAABSZESS",
            "AKUTE_EPIDIDYMITIS",
            "EPIDIDYMOORCHITIS",
            "ENDOMETRITIS",
            "SALPINGITIS",
            "TUBOOVARIALABSZESS",
            "PELVEOPERITONITIS"
        ],
        "skin_soft_tissue": [
            "INFIZIERTE_BISSWUNDEN"
        ],
        "bone_joint": [
            "HAEMATOGENE_OSTEOMYELITIS",
            "SPONDYLODISCITIS",
            "POSTTRAUMATISCHE_POSTOPERATIVE_OSTEOMYELITIS",
            "STERNUMOSTEOMYELITIS",
            "BAKTERIELLE_ARTHRITIS",
            "ENDOPROTHESEN_FREMDKOERPER_ASSOZIIERTE_INFEKTIONEN"
        ],
        "systemic": [
            "SEPSIS",
            "BAKTERIELLE_ENDOKARDITIS",
            "BAKTERIELLE_MENINGITIS"
        ]
    }
    
    negative_terms = []
    
    if category_filter:
        # Find which category the target indication belongs to
        target_category = None
        for category, indications in categories.items():
            if target_indication in indications:
                target_category = category
                break
        
        # Only add negative terms from the same category
        if target_category:
            related_indications = categories[target_category]
            for indication in related_indications:
                if indication != target_indication:
                    negative_terms.extend(INDICATION_SYNONYMS.get(indication, []))
        else:
            # If not categorized, add a few most common indications as negative terms
            common_indications = [
                "AMBULANT_ERWORBENE_PNEUMONIE",
                "NOSOKOMIAL_ERWORBENE_PNEUMONIE",
                "AKUTE_EXAZERBATION_COPD"
            ]
            for indication in common_indications:
                if indication != target_indication:
                    negative_terms.extend(INDICATION_SYNONYMS.get(indication, []))
    else:
        # Add all other indications as negative terms (original behavior)
        for indication_key, synonyms in INDICATION_SYNONYMS.items():
            if indication_key != target_indication:
                negative_terms.extend(synonyms)
    
    return negative_terms