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
    next: Literal["Threat_Analyst", "Log_Analyst", "Policy_Agent", "end_investigation"]

# --- 2. Engineer the Supervisor's Prompt ---
supervisor_prompt = ChatPromptTemplate.from_template(
"""You are a senior cybersecurity SOC supervisor. Your role is to orchestrate a team of specialist agents to investigate and respond to a security alert.

Based on the current state of the investigation, you must decide the next step.

Your decision-making process:

1. **Threat Intelligence:** If no threat intelligence has been gathered (`intel_available` is 'No'), you must call the `Threat_Analyst`.

2. **Log Analysis:** If threat intelligence shows NO threat (`intel_available` is 'Yes' AND `threat_detected` is 'No') AND logs are unanalyzed (`log_summary_available` is 'No'), you must call the `Log_Analyst`.

3. **Fast-Track Policy:** If the Threat_Analyst found a malicious indicator (`threat_detected` is 'Yes' from IP intelligence alone), SKIP log analysis and immediately call the `Policy_Agent`.

4. **Policy Generation:** If log analysis reveals an anomaly (`threat_detected` is 'Yes' from logs), you must call the `Policy_Agent`.

5. **End Investigation:** If all analyses are complete and no threats were found, OR if a threat was found and a policy has been generated, you must choose `end_investigation`.

Here is the current state of the investigation:
- Intel available: {intel_available}
- Log Summary available: {log_summary_available}
- Threat Detected: {threat_detected}
- Policy Generated: {policy_generated}
- Trace: {investigation_trace}

What is the next step?"""
)

# --- 3. Create the Supervisor Chain ---
supervisor_chain = supervisor_prompt | llm.with_structured_output(Route)