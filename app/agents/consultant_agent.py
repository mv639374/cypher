from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
load_dotenv()

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Get the root project directory (parent of scripts/)
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.state import GraphState

# --- 1. Set up the Retriever ---
# This is the component that searches the vector store
DB_PATH = os.path.join(root_dir, "vector_store")

# Load the same embedding model used during ingestion
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
)

# Load the vector store from disk
db = FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)

# Create the retriever
retriever = db.as_retriever()

# --- 2. Define the LLM and Prompt ---
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

consultant_prompt = ChatPromptTemplate.from_template(
"""You are an expert cybersecurity consultant. Your role is to provide specific, actionable steps from the official company playbooks.

A security incident has occurred. Based on the summary of the incident, find the most relevant procedure from the provided context.

If a relevant procedure is found, list the exact steps. If no specific procedure is found, state that "No specific playbook was found for this type of incident."

Context from Playbooks:
{context}

Incident Summary:
{incident_summary}
"""
)

# --- 3. Create the RAG Chain ---
rag_chain = (
    {"context": retriever, "incident_summary": RunnablePassthrough()}
    | consultant_prompt
    | llm
)

# --- 4. Define the Node for the Graph ---
def run_consultant_agent(state: GraphState) -> dict:
    """
    Runs the consultant agent to get advice from the knowledge base.
    """
    print("---CONSULTING THE KNOWLEDGE BASE---")
    
    # Create a rich summary from whatever details are available
    summary_points = []
    if state.get('intel'):
        summary_points.append(f"Threat Intel Summary: {state['intel'].summary}")
    if state.get('log_summary'):
        summary_points.append(f"Log Analysis Summary: {state['log_summary'].summary}")

    # Use the high-level trace as a fallback if no detailed summaries are present
    if not summary_points:
        summary_points.append("\n".join(state["investigation_trace"]))

    incident_summary = "\n".join(summary_points)
    
    response = rag_chain.invoke(incident_summary)
    
    return {
        "playbook_steps": [response.content]
    }