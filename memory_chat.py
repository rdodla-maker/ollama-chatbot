import requests
import json
import os

OLLAMA_URL = "http://localhost:11434/api/generate"

CHAT_FILE = "chat_history.json"

# Load previous chats
if os.path.exists(CHAT_FILE):

    with open(CHAT_FILE, "r") as file:
        chat_history = json.load(file)

else:
    chat_history = []

print("=== AI Chatbot With Memory ===")
print("Type 'exit' to quit\n")

while True:

    user_input = input("You: ")

    if user_input.lower() == "exit":
        break

    # Build prompt from history
    prompt = ""

    for chat in chat_history:
        prompt += f"User: {chat['user']}\n"
        prompt += f"Assistant: {chat['assistant']}\n"

    prompt += f"User: {user_input}\nAssistant:"

    payload = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload
    )

    result = response.json()["response"]

    print("\nAI:", result)
    print()

    # Save conversation
    chat_history.append({
        "user": user_input,
        "assistant": result
    })

    with open(CHAT_FILE, "w") as file:
        json.dump(chat_history, file, indent=4)