import sys
import os

# Add the parent directory to Python path to enable imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import json
from app.agents.threat_analyst import run_threat_analyst, ThreatIntel
from app.state import GraphState

def test_run_threat_analyst_benign_ip(mocker):
    """
    Tests the threat analyst agent with a benign IP address.
    This test mocks the two internal chains (tool user and formatter)
    to isolate and verify the logic of the run_threat_analyst node itself.
    """
    # 1. Arrange: Set up mocks for the internal chains and the initial state
    
    # Mock the entire tool_user_executor object
    mock_tool_executor = mocker.patch('app.agents.threat_analyst.tool_user_executor')
    benign_report_str = json.dumps({
        "ip_address": "8.8.8.8",
        "reputation": 10,
        "analysis_stats": {"harmless": 10, "malicious": 0, "suspicious": 0, "undetected": 0},
        "is_malicious": False
    })
    # Configure the invoke method on the mock
    mock_tool_executor.invoke.return_value = {"output": benign_report_str}

    # CORRECTED MOCKING: Mock the entire formatter_chain object
    mock_formatter = mocker.patch('app.agents.threat_analyst.formatter_chain')
    # Configure the invoke method on this mock
    mock_formatter.invoke.return_value = ThreatIntel(
        summary="The IP 8.8.8.8 is a known Google DNS server and is considered benign.",
        is_malicious=False
    )

    # Define the initial state for the test
    initial_state = GraphState(
        alert={},
        indicator="8.8.8.8",
        intel={},
        investigation_trace=[]
    )

    # 2. Act: Run the function we are testing
    result_state = run_threat_analyst(initial_state)

    # 3. Assert: Verify that the outcome is correct
    
    # Check that the tool executor's invoke method was called correctly
    mock_tool_executor.invoke.assert_called_once_with({"input": "8.8.8.8"})
    
    # Check that the formatter chain's invoke method was called with the correct data
    mock_formatter.invoke.assert_called_once_with({"raw_data": benign_report_str})
    
    # Check that the final state was updated correctly
    assert result_state['intel'].is_malicious is False
    assert "benign" in result_state['intel'].summary
    assert "benign" in result_state['investigation_trace'][-1]