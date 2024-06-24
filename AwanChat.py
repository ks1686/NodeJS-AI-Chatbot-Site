from awan_llm_api import AwanLLMClient, Role
from awan_llm_api.completions import Completions, ChatCompletions
from pysondb import db

AWANLLM_API_KEY = "29d1a42a-37ad-49f2-bdc5-6309fdd89b4a"
MODEL_NAME = "Meta-Llama-3-8B-Instruct"

client = AwanLLMClient(AWANLLM_API_KEY)

# initialize chat completions instance
chat = ChatCompletions(MODEL_NAME)

# loop to take user input and generate responses
while True:
    # take user input
    user_input = input("User: ")

    # add a user message to the chat
    chat.add_message(Role.USER, user_input)

    # request a completion from the model
    chat_response = client.chat_completion(chat)

    # extract the content portion from the response
    content = chat_response["choices"][0]["message"]["content"]
    print("pAI: ", content)
