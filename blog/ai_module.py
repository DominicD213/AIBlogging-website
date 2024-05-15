import openai
openai.api_key = ""
messages = []

# Append the message to the conversation history
def add_message(role, message):
    messages.append({"role": role, "content": message})

def converse_with_chatGPT():
    model_engine = "gpt-3.5-turbo"
    response = openai.ChatCompletion.create(
        model=model_engine,
        messages=messages,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5
    )
    message = response.choices[0].message.content
    return message.strip()

# Process user prompt
def process_user_query(prompt):
    user_prompt = f"{prompt}"
    add_message("user", user_prompt)
    result = converse_with_chatGPT()
    return result



