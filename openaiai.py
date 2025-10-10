import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv('OPENAI')

print("Testing OpenAI connection...")
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Say hi"}],
    max_tokens=10
)
print(response.choices[0].message.content)
