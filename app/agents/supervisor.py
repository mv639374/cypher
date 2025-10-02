import sys
import os
# Add the parent directory to Python path to enable imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Literal

# --- 1. Define the LLM ---
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

class Route(BaseModel):
    next: Literal["Threat_Analyst", "Log_Analyst", "Consultant_Agent", "Policy_Agent", "end_investigation"]

# --- 2. Engineer the Supervisor's Prompt ---
supervisor_prompt = ChatPromptTemplate.from_template(
"""You are a senior cybersecurity SOC supervisor. Your role is to orchestrate a team of specialist agents to investigate and respond to a security alert.

Based on the current state of the investigation, you must decide the next step.

Your decision-making process:

1.  **Threat Intelligence:** If no threat intelligence has been gathered (`intel_available` is 'No'), you must call the `Threat_Analyst`.

2.  **Log Analysis:** If threat intelligence shows NO threat (`intel_available` is 'Yes' AND `threat_detected` is 'No') AND logs are unanalyzed (`log_summary_available` is 'No'), you must call the `Log_Analyst`.

3.  **Consult Playbook:** If a threat has been detected (`threat_detected` is 'Yes') BUT no playbook has been consulted yet (`playbook_consulted` is 'No'), you must immediately call the `Consultant_Agent` to get the company-specific procedure.

4.  **Policy Generation:** If a threat has been detected AND a playbook has been consulted (`playbook_consulted` is 'Yes'), you must call the `Policy_Agent`.

5.  **End Investigation:** If all analyses are complete and no threats were found, OR if a threat was found and a policy has been generated, you must choose `end_investigation`.

Here is the current state of the investigation:
- Intel available: {intel_available}
- Log Summary available: {log_summary_available}
- Threat Detected: {threat_detected}
- Playbook Consulted: {playbook_consulted}
- Policy Generated: {policy_generated}
- Trace: {investigation_trace}

What is the next step?"""
)

# --- 3. Create the Supervisor Chain ---
supervisor_chain = supervisor_prompt | llm.with_structured_output(Route)