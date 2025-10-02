import sys
import os
# Add the parent directory to Python path to enable imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import START, StateGraph, END
from app.state import GraphState
from app.agents.threat_analyst import run_threat_analyst
from app.agents.log_analyst import run_log_analyst
from app.agents.policy_agent import run_policy_agent
from app.agents.supervisor import supervisor_chain

def run_supervisor(state: GraphState) -> dict: # <-- Change return type to dict
    """
    Runs the supervisor chain and saves its decision to the state.
    """
    print("---SUPERVISOR---")
    # ... (the logic for calling supervisor_chain is the same)
    threat_detected = (state.get('intel') and state['intel'].is_malicious) or \
                      (state.get('log_summary') and state['log_summary'].contains_anomaly)

    response = supervisor_chain.invoke({
        "intel_available": 'Yes' if state.get('intel') else 'No',
        "log_summary_available": 'Yes' if state.get('log_summary') else 'No',
        "policy_generated": 'Yes' if state.get('policy') else 'No',
        "threat_detected": 'Yes' if threat_detected else 'No',
        "investigation_trace": "\n".join(state.get('investigation_trace', []))
    })
    # Return ONLY the fields that have been updated
    return {"next_node": response.next}

def route(state: GraphState) -> str:
    """Routes to the next node."""
    print(f"---ROUTING TO: {state['next_node']}---")
    return state.get('next_node', 'end_investigation')


graph = (StateGraph(GraphState)
        .add_node("threat_analyst", run_threat_analyst)
        .add_node("log_analyst", run_log_analyst)
        .add_node("policy_agent", run_policy_agent)
        .add_node("supervisor", run_supervisor)
        .add_edge(START, "supervisor")
        .add_conditional_edges(
            "supervisor",
            route,
            {
                "Threat_Analyst":"threat_analyst",
                "Log_Analyst": "log_analyst",
                "Policy_Agent": "policy_agent",
                'end_investigation': END
            }
        )
        .add_edge("threat_analyst", "supervisor")
        .add_edge("log_analyst", "supervisor")
        .add_edge("policy_agent", "supervisor")).compile()

print("Graph Compiled Successfully!")


# ---This is for testing purpose---
# if __name__ == "__main__":
#     sample_logs = "[2023-10-27 10:00:04] CMD: User 'admin' executed 'cat /etc/passwd' from IP 198.51.100.10"
#     initial_state = {
#         "alert": {"source":"auth_log"},
#         "indicator": "198.51.100.10", # A clearly malicious indicator
#         "logs": sample_logs
#     }
#     for event in graph.stream(initial_state, {"recursion_limit": 10}):
#         print(event)
#         print("---")