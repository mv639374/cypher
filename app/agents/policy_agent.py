from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Literal

from dotenv import load_dotenv
load_dotenv()

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.state import GraphState

# --- 1. Define the LLM and the Output Structure ---
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

class FirewallRule(BaseModel):
    """Represents a single firewall rule to be generated."""
    name: str = Field(description="A descriptive name for the rule, e.g., 'Block-Malicious-IP-123.45.67.89'.")
    action: Literal["BLOCK", "ALLOW", "LOG"] = Field(description="The action to be taken.")
    source_ip: str = Field(description="The source IP address this rule applies to.")
    protocol: Literal["TCP", "UDP", "ANY"] = Field(description="The protocol (TCP, UDP, or ANY).")
    
# --- 2. Engineer the Agent's Prompt ---
policy_agent_prompt = ChatPromptTemplate.from_template(
"""You are a senior network security engineer. Your task is to generate a specific, machine-readable firewall rule based on a security investigation summary.

The investigation has confirmed that the following indicator is malicious:
Indicator: {indicator}

Summary of findings:
{investigation_trace}

Based on this, generate a BLOCK rule for the malicious IP address. The rule should apply to any protocol.
You must respond in the format of the `FirewallRule` tool."""
)

# --- 3. Create the Policy Agent Chain ---
policy_agent_chain = policy_agent_prompt | llm.with_structured_output(FirewallRule)

# --- 4. Define the Node for the Graph ---
def run_policy_agent(state: GraphState) -> dict: # <-- Change return type to dict
    """Executes the policy agent to generate a firewall rule."""
    print("---GENERATING SECURITY POLICY---")
    
    response = policy_agent_chain.invoke({
        "indicator": state["indicator"],
        "investigation_trace": "\n".join(state["investigation_trace"])
    })
    
    trace_message = f"Policy Agent generated rule: {response.name}"
    
    # Return ONLY the fields that have been updated
    return {
        "policy": response,
        "investigation_trace": [trace_message]
    }