# File: app/nodes/coding.py
from dotenv import load_dotenv
load_dotenv()
import json
import google.generativeai as genai
from app.state import (GraphState, EnrichedMedication, EnrichedHistoryEvent, ValidationLog)
from app.tools.pharmacy_api import pharmacy_lookup
from app.tools.meddra_search import meddra_search
from app.prompts import CODING_SYSTEM_PROMPT
import os
import uuid
try:
    from langsmith import traceable
except ImportError:
    def traceable(name=None):
        def decorator(fn):
            return fn
        return decorator

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Define tools in Gemini function calling format
PHARMACY_TOOL = genai.protos.Tool(
    function_declarations=[
        genai.protos.FunctionDeclaration(
            name="pharmacy_lookup",
            description="Resolve a drug brand name to its WHO INN generic name and active chemical composition.",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={
                    "brand_name": genai.protos.Schema(
                        type=genai.protos.Type.STRING,
                        description="The brand name or trade name of the drug"
                    )
                },
                required=["brand_name"]
            )
        )
    ]
)

MEDDRA_TOOL = genai.protos.Tool(
    function_declarations=[
        genai.protos.FunctionDeclaration(
            name="meddra_search",
            description="Search MedDRA terminology to map a medical event description to LLT, PT, and SOC codes.",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={
                    "term": genai.protos.Schema(
                        type=genai.protos.Type.STRING,
                        description="The clinical term or event description to search"
                    )
                },
                required=["term"]
            )
        )
    ]
)


def run_coding_with_tools(prompt_text: str) -> dict:
    """
    Runs the Gemini model in an agentic loop.
    The model will call tools as needed and the loop continues until
    the model produces a final text response (no more tool calls).
    """

    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        system_instruction=CODING_SYSTEM_PROMPT,
        tools=[PHARMACY_TOOL, MEDDRA_TOOL]
    )

    messages = [{"role": "user", "parts": [{"text": prompt_text}]}]

    # Agentic loop with a safety limit to prevent infinite loops
    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        response = model.generate_content(messages)

        # Check if model called a tool
        tool_calls = [
            part for candidate in response.candidates
            for part in candidate.content.parts
            if hasattr(part, "function_call") and part.function_call.name
        ]

        if not tool_calls:
            # Model produced a final text response
            return response.text

        # Execute each tool call and feed results back
        tool_results = []
        for part in tool_calls:
            fn_name = part.function_call.name
            fn_args = dict(part.function_call.args)

            if fn_name == "pharmacy_lookup":
                result = pharmacy_lookup(**fn_args)
            elif fn_name == "meddra_search":
                result = meddra_search(**fn_args)
            else:
                result = {"error": f"Unknown tool: {fn_name}"}

            tool_results.append(
                genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=fn_name,
                        response={"result": result}
                    )
                )
            )

        # Append model response and tool results to the conversation
        messages.append({"role": "model", "parts": [p for p in response.candidates[0].content.parts]})
        messages.append({"role": "user", "parts": tool_results})

    raise RuntimeError("Coding agent exceeded maximum iteration limit without producing a final response.")


@traceable(name="clinical_coding_node")
def coding_node(state: GraphState) -> GraphState:
    """
    Node 2: Clinical Coding
    Enriches extracted entities with standardized terminology using
    Gemini function calling for autonomous tool use.
    """

    # Build a plain text summary of what needs to be coded
    meds_summary = json.dumps(
        [m.model_dump(mode="json") for m in state.extracted_medications],
        indent=2, default=str
    )
    history_summary = json.dumps(
        [h.model_dump(mode="json") for h in state.extracted_history],
        indent=2, default=str
    )

    prompt = f"""
Please code the following extracted entities.

Medications to resolve:
{meds_summary}

Medical history events to map:
{history_summary}
"""

    raw_response = run_coding_with_tools(prompt)

    # Strip markdown fences if present
    clean = raw_response.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:]

    coded = json.loads(clean)

    # Build enriched medication objects
    enriched_meds = []
    for i, item in enumerate(coded.get("enriched_medications", [])):
        original = state.extracted_medications[i] if i < len(state.extracted_medications) else state.extracted_medications[0]
        enriched_meds.append(EnrichedMedication(
            original=original,
            generic_name=item.get("generic_name", original.brand_name or "UNKNOWN"),
            active_composition=item.get("active_composition", "UNKNOWN"),
            atc_code=item.get("atc_code")
        ))

    # Build enriched history objects
    enriched_history = []
    issues_found = []
    for i, item in enumerate(coded.get("enriched_history", [])):
        original = state.extracted_history[i] if i < len(state.extracted_history) else state.extracted_history[0]
        confidence = float(item.get("confidence_score", 0.5))

        if confidence < 0.7:
            issues_found.append(f"Low confidence ({confidence}) for term: {original.event_description}")

        enriched_history.append(EnrichedHistoryEvent(
            original=original,
            meddra_llt=item.get("meddra_llt", "NOT_CODED"),
            meddra_pt=item.get("meddra_pt", "NOT_CODED"),
            meddra_soc=item.get("meddra_soc"),
            confidence_score=confidence
        ))

    log = ValidationLog(
        node_name="clinical_coding_node",
        trace_id=str(uuid.uuid4()),
        confidence_score=sum(e.confidence_score for e in enriched_history) / max(len(enriched_history), 1),
        issues_found=issues_found,
        passed=len(issues_found) == 0
    )

    return state.model_copy(update={
        "enriched_medications": enriched_meds,
        "enriched_history": enriched_history,
        "validation_logs": state.validation_logs + [log]
    })