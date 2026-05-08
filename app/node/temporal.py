# File: app/nodes/temporal.py
from dotenv import load_dotenv
load_dotenv()
import datetime
from app.state import GraphState, TimelineEvent
try:
    from langsmith import traceable
except ImportError:
    def traceable(name=None):
        def decorator(fn):
            return fn
        return decorator


def safe_iso(d: datetime.date) -> str:
    """Converts a date to ISO 8601 string. Returns a placeholder if date is None."""
    if d is None:
        return "1900-01-01"  # sentinel for unknown dates, sorts to beginning
    return d.isoformat()


@traceable(name="temporal_alignment_node")
def temporal_alignment_node(state: GraphState) -> GraphState:
    """
    Node 3: Temporal Alignment
    Builds a linear chronological timeline from all enriched entities.
    Medications that span a date range appear twice (start event and end event).
    Ongoing items are assigned the current date as their end anchor.
    Overlapping events are preserved as-is with their own timestamps,
    allowing downstream consumers to identify co-occurrence periods.
    """

    events = []
    today_iso = datetime.date.today().isoformat()

    # Process each enriched medication
    for i, med in enumerate(state.enriched_medications):
        orig = med.original

        # Start of medication event
        events.append(TimelineEvent(
            event_type="medication_start",
            description=f"Started {med.generic_name} ({orig.dose or 'dose unknown'}, {orig.route or 'route unknown'}, {orig.frequency or 'frequency unknown'})",
            iso_timestamp=safe_iso(orig.start_date),
            source_entity_id=f"med_{i}"
        ))

        # End of medication event (only if there is an explicit end date)
        if orig.end_date:
            events.append(TimelineEvent(
                event_type="medication_end",
                description=f"Stopped {med.generic_name}",
                iso_timestamp=safe_iso(orig.end_date),
                source_entity_id=f"med_{i}"
            ))

    # Process each enriched history event
    for i, event in enumerate(state.enriched_history):
        orig = event.original

        events.append(TimelineEvent(
            event_type="medical_history_onset",
            description=f"Onset: {orig.event_description} (MedDRA PT: {event.meddra_pt})",
            iso_timestamp=safe_iso(orig.onset_date),
            source_entity_id=f"hist_{i}"
        ))

        if orig.resolution_date:
            events.append(TimelineEvent(
                event_type="medical_history_resolution",
                description=f"Resolved: {orig.event_description}",
                iso_timestamp=safe_iso(orig.resolution_date),
                source_entity_id=f"hist_{i}"
            ))
        elif orig.is_ongoing:
            events.append(TimelineEvent(
                event_type="medical_history_ongoing",
                description=f"Still ongoing as of today: {orig.event_description}",
                iso_timestamp=today_iso,
                source_entity_id=f"hist_{i}"
            ))

    # Sort by ISO timestamp string (ISO 8601 sorts correctly as plain strings)
    events.sort(key=lambda e: e.iso_timestamp)

    return state.model_copy(update={"chronological_timeline": events})