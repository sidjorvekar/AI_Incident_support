import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def analyze_logs(logs):

    prompt = f"""
    You are a Kubernetes SRE expert.

    Analyze these logs.

    Return:
    1. Root cause
    2. Severity
    3. Suggested fix

    Logs:
    {logs}
    """

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    return response.json()['response']
