from model import generate_response
import sys

# Windows utf-8 stdout fix
sys.stdout.reconfigure(encoding='utf-8')

def test_llm():
    prompt = "List 3 famous real museums, 3 famous real restaurants, and 3 famous real local desserts in Italy. Just give the names in bullet points, without introductory text."
    system_prompt = "You are a helpful travel data assistant. Give concise bullet points."
    try:
        response = generate_response(prompt, system_prompt)
        print("Response:\n" + response)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_llm()
