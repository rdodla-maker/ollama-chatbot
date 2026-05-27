import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"

print("=== Basic AI Chatbot ===")
print("Type 'exit' to quit\n")

while True:

    user_input = input("You: ")

    if user_input.lower() == "exit":
        break

    payload = {
        "model": "llama3",
        "prompt": user_input,
        "stream": False
    }

    response = httpx.post(OLLAMA_URL, json=payload, timeout=30.0)
    result = response.json().get("response", "")

    print("\nAI:", result)
    print()