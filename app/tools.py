import os
import requests
import json
from langchain_core.tools import tool

@tool
def virustotal_ip_lookup(ip_address: str) -> str:
    """
    Performs a lookup for a given IP address using the VirusTotal API.
    Returns a JSON string with a summary of the findings, including analysis stats and reputation.
    """
    api_key = os.getenv("VT_API_KEY")
    if not api_key:
        return "Error: VirusTotal API key not found in environment variables."
    
    url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip_address}"
    headers = {"x-apikey": api_key}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx, 5xx)
        data = response.json()

        # We are not returning the raw data. Instead, we are summarizing it.
        # This is a curcial step in making the tool useful for the LLM.
        attributes = data.get('data', {}).get('attributes', {})
        analysis_stats = attributes.get("last_analysis_stats", {})
        reputation = attributes.get("reputation")

        summary = {
            "ip_address": ip_address,
            "reputation": reputation,
            "analysis_stats": {
                "harmless": analysis_stats.get("harmless", 0),
                "malicious": analysis_stats.get("malicious", 0),
                "suspicious": analysis_stats.get("suspicious", 0),
                "undetected": analysis_stats.get("undetected", 0),
            },
            "is_malicious": analysis_stats.get("malicious", 0) > 0 or analysis_stats.get("suspicious", 0) > 0
        }

        return json.dumps(summary)

    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

        