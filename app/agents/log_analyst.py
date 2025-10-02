from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv()

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.state import GraphState

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

class LogAnalysis(BaseModel):
    """Structured Output for the Log Analysis agent."""
    summary: str = Field(description="A summary of the key events found in the logs and an analysis of their significance")
    contains_anomaly: bool = Field(description="The final verdict on whether the logs contain any anomalous or suspicious activity.")

log_analyst_prompt = ChatPromptTemplate.from_messages([
    ('system', 
    """You are a senior cybersecurity analyst specializing in log analysis. Your task is to meticulously review the provided logs and identify any suspicious or anomalous activity.

        Look for patterns such as:
        - Multiple failed login attempts followed by a success.
        - Access to sensitive files or directories.
        - Unusual commands being executed.
        - Connections from unexpected IP addresses or ports.

        Summarize the key events and provide a final verdict on whether an anomaly is present.
        You must respond in the format of the `LogAnalysis` tool."""),

        ('human', "Please analyze the following logs related to the alert:\n\n{logs}")
])

log_analyst_chain = log_analyst_prompt | llm.with_structured_output(LogAnalysis)

def run_log_analyst(state: GraphState) -> dict: # <-- Change return type to dict
    """Executes the log analysis agent."""
    print("---RUNNING LOG ANALYST---")
    logs = state.get("logs", "")
    if not logs:
        return {} # Return an empty dictionary if there's nothing to do
        
    response = log_analyst_chain.invoke({"logs": logs})

    trace_message = f"Log Analyst conclusion: Anomaly detected: {response.contains_anomaly}."

    # Return ONLY the fields that have been updated
    return {
        "log_summary": response,
        "investigation_trace": [trace_message]
    }