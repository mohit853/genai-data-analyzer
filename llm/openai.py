import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_fixed

import os

load_dotenv()


if "OPENAI_API_KEY" not in os.environ:
    print("Error: Please set the OPENAI_API_KEY environment variable.")
    sys.exit(1)

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def call_llm_api(content="who is the president of the united states?"):
    """Function to call OpenAI GPT-4o API with retry logic."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }
    data = {"model": "gpt-4o", "messages": [{"role": "user", "content": content}]}

    #  ## ^ request package to call open api
    response = requests.post(OPENAI_API_URL, headers=headers, json=data)
    if response.status_code == 200:

        return response.json()["choices"][0]["message"]["content"]
    else:
        print(f"Error calling API: {response.status_code}\n{response.text}")
        sys.exit(1)
