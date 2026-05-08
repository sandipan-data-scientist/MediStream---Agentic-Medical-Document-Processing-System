# File: app/graph.py

from langgraph.graph import StateGraph, END
from app.state import GraphState
from app.nodes.extraction import extraction_node
from app.nodes.coding import coding_node
from app.nodes.temporal import temporal_alignment_node
from app.nodes.serialization import serialization_node
from app.nodes.reviewer import reviewer_node


def reviewer_gate(state: GraphState) -> str:
    """
    Conditional edge function.
    If the reviewer passes the output, we end. If it fails, we could loop back.
    For simplicity here we always end but emit a warning in the state.
    In production this would trigger re-extraction or human review.
    """
    if state.reviewer_verdict == "fail":
        # In a real system: return "extraction_node" to restart
        # For now, end with the verdict logged in state
        return "end_with_warning"
    return "end"


def build_graph() -> StateGraph:
    """
    Assembles the MediStream LangGraph pipeline.
    Nodes execute in sequence. State is passed immutably between nodes.
    """

    graph = StateGraph(GraphState)

    # Register all nodes
    graph.add_node("extraction", extraction_node)
    graph.add_node("coding", coding_node)
    graph.add_node("temporal_alignment", temporal_alignment_node)
    graph.add_node("serialization", serialization_node)
    graph.add_node("reviewer", reviewer_node)

    # Define the linear execution path
    graph.set_entry_point("extraction")
    graph.add_edge("extraction", "coding")
    graph.add_edge("coding", "temporal_alignment")
    graph.add_edge("temporal_alignment", "serialization")
    graph.add_edge("serialization", "reviewer")

    # Conditional exit after review
    graph.add_conditional_edges(
        "reviewer",
        reviewer_gate,
        {
            "end": END,
            "end_with_warning": END
        }
    )

    return graph.compile()


# Convenience function to run the full pipeline
def run_pipeline(file_bytes: bytes, file_type: str = "text") -> GraphState:
    """
    Entry point for the full pipeline.
    Accepts raw file bytes and returns the fully populated GraphState.
    """
    compiled_graph = build_graph()
    initial_state = GraphState(source_bytes=file_bytes, file_type=file_type)
    result = compiled_graph.invoke(initial_state)
    return result