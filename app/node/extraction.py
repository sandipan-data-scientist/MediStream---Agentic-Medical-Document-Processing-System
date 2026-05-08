# File: app/nodes/extraction.py
from dotenv import load_dotenv
load_dotenv()
import base64
import json
import datetime
import google.generativeai as genai
from app.state import GraphState, MedicationEntity, MedicalHistoryEntity
from app.prompts import EXTRACTION_SYSTEM_PROMPT
import os
try:
    from langsmith import traceable
except ImportError:
    def traceable(name=None):
        def decorator(fn):
            return fn
        return decorator

genai.configure(api_key=os.environ["GEMINI_API_KEY"])


def resolve_relative_date(raw_date_str: str, reference_date: datetime.date) -> datetime.date:
    """
    Converts fuzzy date expressions to concrete datetime.date objects.
    This handles the most common patterns seen in clinical documents.
    """
    raw = raw_date_str.lower().strip()

    if not raw or raw in ("unknown", "not stated", "n/a"):
        return None

    # Try direct ISO parse first
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%B %Y", "%b %Y"):
        try:
            return datetime.datetime.strptime(raw_date_str.strip(), fmt).date()
        except ValueError:
            continue

    # Handle relative expressions
    import re
    months_ago = re.search(r"(\d+)\s*month", raw)
    years_ago = re.search(r"(\d+)\s*year", raw)
    weeks_ago = re.search(r"(\d+)\s*week", raw)

    if months_ago:
        m = int(months_ago.group(1))
        return (reference_date.replace(day=1) - datetime.timedelta(days=30 * m))
    if years_ago:
        y = int(years_ago.group(1))
        return reference_date.replace(year=reference_date.year - y)
    if weeks_ago:
        w = int(weeks_ago.group(1))
        return reference_date - datetime.timedelta(weeks=w)

    # Seasonal references
    if "early" in raw:
        year_match = re.search(r"(\d{4})", raw)
        year = int(year_match.group(1)) if year_match else reference_date.year
        return datetime.date(year, 1, 1)
    if "mid" in raw:
        year_match = re.search(r"(\d{4})", raw)
        year = int(year_match.group(1)) if year_match else reference_date.year
        return datetime.date(year, 6, 1)
    if "late" in raw:
        year_match = re.search(r"(\d{4})", raw)
        year = int(year_match.group(1)) if year_match else reference_date.year
        return datetime.date(year, 10, 1)

    return None


@traceable(name="multimodal_extraction_node")
def extraction_node(state: GraphState) -> GraphState:
    """
    Node 1: Multimodal Extraction
    Sends the raw document to Gemini 1.5 Pro and parses the structured response.
    Supports PDF bytes (converted to base64 inline data), image bytes, and plain text.
    """

    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        system_instruction=EXTRACTION_SYSTEM_PROMPT
    )

    reference_date = datetime.date.today()

    # Build the content parts based on file type
    if state.file_type in ("pdf", "image"):
        # Encode bytes as base64 for Gemini multimodal input
        encoded = base64.b64encode(state.source_bytes).decode("utf-8")
        mime = "application/pdf" if state.file_type == "pdf" else "image/jpeg"
        parts = [
            {"inline_data": {"mime_type": mime, "data": encoded}},
            {"text": "Please extract all medications and medical history from this document as described in your instructions."}
        ]
    else:
        # Plain text input
        document_text = state.source_bytes.decode("utf-8")
        parts = [{"text": document_text}]

    response = model.generate_content(parts)
    raw_json = response.text.strip()

    # Strip markdown code fences if Gemini wraps the response
    if raw_json.startswith("```"):
        raw_json = raw_json.split("```")[1]
        if raw_json.startswith("json"):
            raw_json = raw_json[4:]

    parsed = json.loads(raw_json)

    # Parse medications
    medications = []
    for item in parsed.get("medications", []):
        med = MedicationEntity(
            raw_text=item.get("raw_text", ""),
            brand_name=item.get("brand_name"),
            generic_name=item.get("generic_name"),
            dose=item.get("dose"),
            route=item.get("route"),
            frequency=item.get("frequency"),
            is_concomitant=item.get("is_concomitant", False)
        )
        # Resolve dates
        if item.get("start_date"):
            med.start_date = resolve_relative_date(item["start_date"], reference_date)
        if item.get("end_date"):
            med.end_date = resolve_relative_date(item["end_date"], reference_date)
        medications.append(med)

    # Parse medical history
    history = []
    for item in parsed.get("medical_history", []):
        event = MedicalHistoryEntity(
            raw_text=item.get("raw_text", ""),
            event_description=item.get("event_description", ""),
            is_ongoing=item.get("is_ongoing", False)
        )
        if item.get("onset_date"):
            event.onset_date = resolve_relative_date(item["onset_date"], reference_date)
        if item.get("resolution_date"):
            event.resolution_date = resolve_relative_date(item["resolution_date"], reference_date)
        history.append(event)

    # Return updated state
    return state.model_copy(update={
        "extracted_medications": medications,
        "extracted_history": history
    })