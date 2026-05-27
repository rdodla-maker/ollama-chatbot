import httpx
import json

OLLAMA_URL = "http://localhost:11434/api/generate"

print("=== Streaming AI Chatbot ===")
print("Type 'exit' to quit\n")

while True:

    user_input = input("You: ")

    if user_input.lower() == "exit":
        break

    payload = {
        "model": "llama3",
        "prompt": user_input,
        "stream": True
    }

    with httpx.stream("POST", OLLAMA_URL, json=payload, timeout=None) as resp:
        print("\nAI: ", end="")
        for line in resp.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                except Exception:
                    continue
                print(data.get("response", ""), end="", flush=True)

    print("\n")