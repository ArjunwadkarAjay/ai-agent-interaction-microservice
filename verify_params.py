import requests
import json

url = "http://localhost:8000/api/v1/chat"

payload = {
    "message": "Write a short poem about code.",
    "model": "hf.co/liquidai/lfm2.5-1.2b-instruct-gguf:Q4_K_M",
    "temperature": 0.2, # Low temp for deterministic output
    "max_tokens": 50,    # Short output
    "top_p": 0.9,
    "presence_penalty": 0.1,
    "frequency_penalty": 0.1
}

print(f"Sending payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(url, json=payload)
    response.raise_for_status()
    print("Response received:")
    print(json.dumps(response.json(), indent=2))
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
    if response:
        print(response.text)
