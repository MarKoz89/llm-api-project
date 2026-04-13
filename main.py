import json
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI


# načte .env ze stejné složky, kde je tento main.py
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError(f"Chybí OPENAI_API_KEY v .env souboru. Očekávaná cesta: {env_path}")

client = OpenAI(api_key=api_key)


def calculate(expression: str) -> str:
    allowed_chars = "0123456789+-*/(). "
    if not all(char in allowed_chars for char in expression):
        return "Neplatný výraz. Povolené jsou pouze čísla a operátory + - * / ( )"

    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Chyba při výpočtu: {e}"


tools = [
    {
        "type": "function",
        "name": "calculate",
        "description": "Vypočítá matematický výraz zadaný uživatelem.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Matematický výraz, například: (15 + 5) * 2"
                }
            },
            "required": ["expression"],
            "additionalProperties": False
        }
    }
]

user_prompt = "Kolik je (15 + 5) * 2? Použij k tomu nástroj."

response = client.responses.create(
    model="gpt-5",
    input=user_prompt,
    tools=tools
)

conversation_items = []

for item in response.output:
    conversation_items.append(item)

    if item.type == "function_call" and item.name == "calculate":
        arguments = json.loads(item.arguments)
        tool_result = calculate(arguments["expression"])

        conversation_items.append({
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": tool_result
        })

final_response = client.responses.create(
    model="gpt-5",
    input=conversation_items
)

print("Finální odpověď modelu:")
print(final_response.output_text)