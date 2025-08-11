from openai import OpenAI

# pip install openai 
# if you saved the key under a different environment variable name, you can do something like:
client = OpenAI(
  api_key="<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>",
)
completion = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "system", "content": "You are a virtual assistant name robin skilled in general tasks like Alexa and Google Cloud"},
    {"role": "user", "content": "what is maths"}
  ]
)

print(completion.choices[0].message.content)