from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain.agents import AgentExecutor, create_tool_calling_agent

from dotenv import load_dotenv
load_dotenv()

import sys
import os
# Add the parent directory to Python path to enable imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.tools import virustotal_ip_lookup
from app.state import GraphState
import json

# --- 1. Define the LLM and the Output Structure ---
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

class ThreatIntel(BaseModel):
    """Structured output for the Threat Intelligence Analyst agent."""
    summary: str = Field(description="A concise summary of the threat intelligence findings, including reputation and analysis stats.")
    is_malicious: bool = Field(description="The final verdict on whether the indicator is malicious, based on the analysis.")

# --- 2. Create the "Tool User" Agent ---
# This agent's only job is to call the VirusTotal tool.
tool_user_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are an assistant that uses tools to gather information. You must use the virustotal_ip_lookup tool for the given IP address."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)
tool_user_agent = create_tool_calling_agent(llm, [virustotal_ip_lookup], tool_user_prompt)
tool_user_executor = AgentExecutor(agent=tool_user_agent, tools=[virustotal_ip_lookup], verbose=True)


# --- 3. Create the "Formatter" Chain ---
# This chain's only job is to format the raw tool output into our desired structure.
formatter_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", 
         """You are a Threat Intelligence Analyst specializing in analyzing indicators of compromise.

            Your task: Analyze the provided indicator using VirusTotal data and determine if it's malicious.

            **Critical Detection Criteria:**
            - If ANY scanner flags the indicator as malicious, consider it malicious
            - If the indicator has a reputation score of 0 or negative, flag as suspicious
            - If context suggests this IP is associated with attacks, prioritize that over scanner counts

            Indicator: {indicator}"""),
            
        ("human", "Here is the raw data from the threat intelligence tool:\n\n{raw_data}")
    ]
)
# We cleanly apply structured output here, with no tools to cause conflicts.
formatter_chain = formatter_prompt | llm.with_structured_output(ThreatIntel)


# --- 4. Define the Node that Orchestrates the Two Steps ---
def run_threat_analyst(state: GraphState) -> dict: # <-- Change return type to dict
    """Executes the threat intelligence analysis."""
    print("---RUNNING THREAT ANALYST---")
    indicator = state["indicator"]
    
    tool_response = tool_user_executor.invoke({"input": indicator})
    raw_data_str = tool_response["output"]
    structured_output = formatter_chain.invoke({"indicator":indicator, "raw_data": raw_data_str})
    
    trace_message = f"Threat Analyst conclusion: The indicator '{indicator}' is {'malicious' if structured_output.is_malicious else 'benign'}."
    
    # Return ONLY the fields that have been updated
    return {
        "intel": structured_output,
        "investigation_trace": [trace_message] # Return the new trace message as a list
    }