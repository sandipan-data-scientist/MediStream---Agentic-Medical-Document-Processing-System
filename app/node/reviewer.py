# File: app/nodes/reviewer.py
from dotenv import load_dotenv
load_dotenv()
import json
import uuid
import google.generativeai as genai
from app.state import GraphState, ValidationLog
from app.prompts import REVIEWER_SYSTEM_PROMPT
import os
try:
    from langsmith import traceable
except ImportError:
    def traceable(name=None):
        def decorator(fn):
            return fn
        return decorator

genai.configure(api_key=os.environ["GEMINI_API_KEY"])


@traceable(name="reviewer_node")
def reviewer_node(state: GraphState) -> GraphState:
    """
    Node 5: LLM-as-a-Judge Reviewer
    Compares the original document content against the generated XML output
    and flags discrepancies, hallucinations, or missed extractions.
    """

    if not state.output_xml_path:
        # Serialization did not run or failed, skip review
        return state

    with open(state.output_xml_path, "r", encoding="utf-8") as f:
        xml_content = f.read()

    # Reconstruct original document text from extracted raw_text fields
    original_text_parts = []
    for med in state.extracted_medications:
        original_text_parts.append(f"Medication raw text: {med.raw_text}")
    for event in state.extracted_history:
        original_text_parts.append(f"History raw text: {event.raw_text}")

    original_summary = "\n".join(original_text_parts)

    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        system_instruction=REVIEWER_SYSTEM_PROMPT
    )

    prompt = f"""
Original document content (raw extractions):
{original_summary}

Generated XML output:
{xml_content}

Please review and return your verdict as a JSON object.
"""

    response = model.generate_content(prompt)
    raw = response.text.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    verdict_data = json.loads(raw)

    log = ValidationLog(
        node_name="reviewer_node",
        trace_id=str(uuid.uuid4()),
        confidence_score=float(verdict_data.get("confidence", 0.5)),
        issues_found=verdict_data.get("issues", []),
        passed=(verdict_data.get("verdict", "fail") == "pass")
    )

    return state.model_copy(update={
        "reviewer_verdict": verdict_data.get("verdict", "fail"),
        "validation_logs": state.validation_logs + [log]
    })