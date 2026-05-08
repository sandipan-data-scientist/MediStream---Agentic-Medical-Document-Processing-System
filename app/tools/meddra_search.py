# File: app/tools/meddra_search.py

from typing import Optional


def meddra_search(term: str) -> dict:
    """
    Performs a semantic search against MedDRA terminology to map a clinical
    description to its LLT, PT, and SOC hierarchy entries.

    In production this would call a licensed MedDRA API or a locally hosted
    vector index built from the MedDRA release files. For development we use
    a curated sample of common terms.
    """

    # Sample MedDRA mappings for development
    sample_mappings = {
        "high blood pressure": {
            "llt": "Blood pressure increased",
            "pt": "Hypertension",
            "soc": "Vascular disorders",
            "confidence": 0.95
        },
        "hypertension": {
            "llt": "Hypertension",
            "pt": "Hypertension",
            "soc": "Vascular disorders",
            "confidence": 0.99
        },
        "type 2 diabetes": {
            "llt": "Type 2 diabetes mellitus",
            "pt": "Type 2 diabetes mellitus",
            "soc": "Endocrine disorders",
            "confidence": 0.97
        },
        "diabetes": {
            "llt": "Diabetes mellitus",
            "pt": "Diabetes mellitus",
            "soc": "Endocrine disorders",
            "confidence": 0.90
        },
        "chest pain": {
            "llt": "Chest pain",
            "pt": "Chest discomfort",
            "soc": "General disorders and administration site conditions",
            "confidence": 0.85
        },
        "allergic reaction": {
            "llt": "Allergic reaction",
            "pt": "Hypersensitivity",
            "soc": "Immune system disorders",
            "confidence": 0.88
        },
        "kidney disease": {
            "llt": "Renal impairment",
            "pt": "Renal impairment",
            "soc": "Renal and urinary disorders",
            "confidence": 0.86
        },
    }

    normalized = term.lower().strip()

    # Direct match
    if normalized in sample_mappings:
        return sample_mappings[normalized]

    # Partial match by checking if any key is contained in the query
    for key, value in sample_mappings.items():
        if key in normalized or normalized in key:
            return {**value, "confidence": value["confidence"] * 0.85}

    # No match found
    return {
        "llt": "NOT_CODED",
        "pt": "NOT_CODED",
        "soc": "NOT_CODED",
        "confidence": 0.0
    }