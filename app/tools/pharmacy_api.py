# File: app/tools/pharmacy_api.py

import requests
import os
from typing import Optional


def pharmacy_lookup(brand_name: str) -> dict:
    """
    Queries an external pharmacy or drug database API to resolve a brand name
    to its generic name and active composition.

    In production this points to a real service such as the OpenFDA drug API
    or a licensed pharmaceutical database. For local development the function
    falls back to a small hardcoded dictionary so the pipeline can run without
    a live API key.
    """

    # Hardcoded fallback dictionary for development and testing
    known_drugs = {
        "paracetamol": {"generic_name": "acetaminophen", "composition": "acetaminophen 500mg"},
        "crocin": {"generic_name": "paracetamol", "composition": "paracetamol 650mg"},
        "augmentin": {"generic_name": "amoxicillin-clavulanate", "composition": "amoxicillin 875mg, clavulanate 125mg"},
        "metformin": {"generic_name": "metformin hydrochloride", "composition": "metformin HCl 500mg"},
        "aspirin": {"generic_name": "acetylsalicylic acid", "composition": "acetylsalicylic acid 75mg"},
        "lipitor": {"generic_name": "atorvastatin", "composition": "atorvastatin calcium 10mg"},
    }

    normalized = brand_name.lower().strip()

    if normalized in known_drugs:
        return known_drugs[normalized]

    # Attempt live lookup via OpenFDA if an API key is present
    api_key = os.getenv("OPENFDA_API_KEY", "")
    if api_key:
        try:
            url = f"https://api.fda.gov/drug/label.json?search=openfda.brand_name:{brand_name}&limit=1"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                results = response.json().get("results", [])
                if results:
                    generic = results[0].get("openfda", {}).get("generic_name", [brand_name])
                    substance = results[0].get("openfda", {}).get("substance_name", ["UNKNOWN"])
                    return {
                        "generic_name": generic[0].lower() if generic else brand_name,
                        "composition": substance[0] if substance else "UNKNOWN"
                    }
        except Exception:
            pass

    # If nothing works, return the brand name itself and mark as unresolved
    return {"generic_name": brand_name, "composition": "UNRESOLVED"}