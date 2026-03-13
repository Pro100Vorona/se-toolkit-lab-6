import subprocess, json, sys

def test_agent():
    res = subprocess.run([sys.executable, "agent.py", "hi"], capture_output=True, text=True, timeout=10)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert "answer" in data and "tool_calls" in data
    print("Test passed")
