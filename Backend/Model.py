import time
import cohere
from dotenv import dotenv_values
from rich import print

# ------------------ LOAD ENV ------------------
env_vars = dotenv_values(".env")
COHERE_API_KEY = env_vars.get("CohereAPIKey")

if not COHERE_API_KEY:
    raise RuntimeError("❌ Cohere API key missing. Check .env file")

# ------------------ INIT CLIENT ------------------
co = cohere.ClientV2(api_key=COHERE_API_KEY)

# ------------------ SUPPORTED TASKS ------------------
funcs = [
    "exit", "general", "realtime", "open", "close", "play",
    "generate image", "system", "content", "google search",
    "youtube search", "reminder"
]

# ------------------ SYSTEM PROMPT ------------------
preamble = """
You are a very accurate Decision-Making Model.
DO NOT answer the query.
ONLY classify it into one or more of the following formats:

general (query)
realtime (query)
open (app or site)
close (app or site)
play (song)
generate image (prompt)
system (task)
content (topic)
google search (topic)
youtube search (topic)
reminder (time date message)

Rules:
- Output must be comma-separated if multiple tasks
- Do not add explanations
- If user says goodbye → output: exit
- If unsure → output: general (query)
"""

# ------------------ FEW-SHOT MEMORY ------------------
ChatHistory = [
    {
        "role": "user",
        "content": [{"type": "text", "text": "how are you ?"}]
    },
    {
        "role": "assistant",
        "content": [{"type": "text", "text": "general how are you ?"}]
    },
    {
        "role": "user",
        "content": [{"type": "text", "text": "open chrome and tell me about mahatma gandhi"}]
    },
    {
        "role": "assistant",
        "content": [{"type": "text", "text": "open chrome, general tell me about mahatma gandhi"}]
    }
]

# ------------------ CORE DMM FUNCTION ------------------
def FirstLayerDMM(prompt: str):
    try:
        response = co.chat(
            model="command-r-08-2024",   # ✅ CORRECT TEXT MODEL
            temperature=0.3,
            max_tokens=50,
            messages=[
                {
                    "role": "system",
                    "content": [{"type": "text", "text": preamble}]
                },
                *ChatHistory,
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}]
                }
            ]
        )

        # Rate-limit protection
        time.sleep(1.5)

        # Extract response safely
        raw_text = response.message.content[0].text.strip().replace("\n", "")
        parts = [p.strip() for p in raw_text.split(",") if p.strip()]

        final_tasks = []
        for task in parts:
            for func in funcs:
                if task.lower().startswith(func):
                    final_tasks.append(task)

        return final_tasks if final_tasks else [f"general {prompt}"]

    except Exception as e:
        if "429" in str(e):
            print("[yellow]⚠ Rate limit hit. Waiting 10 seconds...[/yellow]")
            time.sleep(10)
        else:
            print(f"[red]❌ Cohere Error:[/red] {e}")

        return [f"general {prompt}"]

# ------------------ MANUAL TEST LOOP ------------------
if __name__ == "__main__":
    print("[green]🤖 Jarvis DMM Ready. Type 'exit' to quit.[/green]\n")

    while True:
        user_input = input(">>> ").strip()

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit", "bye"]:
            print("[cyan]👋 Goodbye![/cyan]")
            break

        tasks = FirstLayerDMM(user_input)
        print(tasks)
