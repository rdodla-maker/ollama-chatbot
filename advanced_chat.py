import requests
import json
import os
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"

CHAT_FILE = "chat_history.json"

# ANSI Colors
USER_COLOR = "\033[94m"
AI_COLOR = "\033[92m"
SYSTEM_COLOR = "\033[93m"
RESET_COLOR = "\033[0m"

# AI Personality / System Prompt
SYSTEM_PROMPT = """
You are a helpful AI coding assistant.
You help with:
- Python
- React
- APIs
- Debugging
- FastAPI
- JavaScript

Give clean and beginner-friendly answers.
"""

# Load memory
if os.path.exists(CHAT_FILE):

    with open(CHAT_FILE, "r") as file:
        chat_history = json.load(file)

else:
    chat_history = []

print(f"{SYSTEM_COLOR}=== Advanced AI Assistant V3 ==={RESET_COLOR}")
print(f"{SYSTEM_COLOR}Commands:{RESET_COLOR}")
print("/exit  -> Quit")
print("/clear -> Clear memory")
print("/history -> View history\n")

while True:

    user_input = input(f"{USER_COLOR}You: {RESET_COLOR}")

    # EXIT
    if user_input.lower() == "/exit":
        print(f"\n{SYSTEM_COLOR}Goodbye!{RESET_COLOR}")
        break

    # CLEAR MEMORY
    if user_input.lower() == "/clear":

        chat_history = []

        with open(CHAT_FILE, "w") as file:
            json.dump(chat_history, file)

        print(f"{SYSTEM_COLOR}Memory cleared!{RESET_COLOR}\n")

        continue

    # SHOW HISTORY
    if user_input.lower() == "/history":

        print(f"\n{SYSTEM_COLOR}=== Chat History ==={RESET_COLOR}\n")

        for chat in chat_history:

            print(f"{USER_COLOR}You:{RESET_COLOR} {chat['user']}")
            print(f"{AI_COLOR}AI:{RESET_COLOR} {chat['assistant']}\n")

        continue

    # Build Prompt
    prompt = SYSTEM_PROMPT + "\n"

    for chat in chat_history:

        prompt += f"User: {chat['user']}\n"
        prompt += f"Assistant: {chat['assistant']}\n"

    prompt += f"User: {user_input}\nAssistant:"

    payload = {
        "model": "llama3",
        "prompt": prompt,
        "stream": True
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        stream=True
    )

    print(f"\n{AI_COLOR}AI: {RESET_COLOR}", end="")

    full_response = ""

    for line in response.iter_lines():

        if line:

            data = json.loads(line)

            token = data.get("response", "")

            full_response += token

            print(token, end="", flush=True)

    print("\n")

    # Save memory with timestamp
    chat_history.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user_input,
        "assistant": full_response
    })

    with open(CHAT_FILE, "w") as file:
        json.dump(chat_history, file, indent=4)