# File: app/state.py

from pydantic import BaseModel, Field
from typing import Optional
import datetime


# A single medication entry extracted from the source document
class MedicationEntity(BaseModel):
    raw_text: str  # exact text as it appeared in the document
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None
    dose: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None
    is_concomitant: bool = False


# A single medical history event extracted from the source document
class MedicalHistoryEntity(BaseModel):
    raw_text: str
    event_description: str
    onset_date: Optional[datetime.date] = None
    resolution_date: Optional[datetime.date] = None
    is_ongoing: bool = False


# After coding, a medication gets enriched with standardized identifiers
class EnrichedMedication(BaseModel):
    original: MedicationEntity
    generic_name: str
    active_composition: str
    atc_code: Optional[str] = None  # WHO ATC classification


# After coding, a history event gets mapped to MedDRA terminology
class EnrichedHistoryEvent(BaseModel):
    original: MedicalHistoryEntity
    meddra_llt: str  # Lowest Level Term
    meddra_pt: str   # Preferred Term
    meddra_soc: Optional[str] = None  # System Organ Class
    confidence_score: float = Field(ge=0.0, le=1.0)


# A single entry in the final chronological timeline
class TimelineEvent(BaseModel):
    event_type: str  # "medication" or "medical_history"
    description: str
    iso_timestamp: str  # ISO 8601 format
    source_entity_id: Optional[str] = None


# Validation record for LangSmith tracing
class ValidationLog(BaseModel):
    node_name: str
    trace_id: str
    confidence_score: float
    issues_found: list[str] = []
    passed: bool = True


# The master state object that flows through every node in the graph
class GraphState(BaseModel):
    source_bytes: Optional[bytes] = None
    file_type: str = "pdf"  # pdf, image, text
    extracted_medications: list[MedicationEntity] = []
    extracted_history: list[MedicalHistoryEntity] = []
    enriched_medications: list[EnrichedMedication] = []
    enriched_history: list[EnrichedHistoryEvent] = []
    chronological_timeline: list[TimelineEvent] = []
    validation_logs: list[ValidationLog] = []
    output_xml_path: Optional[str] = None
    output_xlsx_path: Optional[str] = None
    reviewer_verdict: Optional[str] = None  # pass or fail with reasoning