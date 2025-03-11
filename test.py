from openai import OpenAI

client = OpenAI(api_key="sk-32acbf091669470088082a985df2e0e3", base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "你是谁"},
    ],
    stream=False
)

print(response.choices[0].message.content)
