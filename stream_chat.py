import requests
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

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        stream=True
    )

    print("\nAI: ", end="")

    for line in response.iter_lines():

        if line:

            data = json.loads(line)

            print(
                data.get("response", ""),
                end="",
                flush=True
            )

    print("\n")