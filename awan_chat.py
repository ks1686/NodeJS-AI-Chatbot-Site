import os
import json
from dotenv import load_dotenv
from awan_llm_api import AwanLLMClient, Role
from awan_llm_api.completions import ChatCompletions
from speech import speech_to_text, text_to_speech

# Load environment variables
load_dotenv()

# API key and model name
AWANLLM_API_KEY = os.getenv("AWANLLM_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

# Check if the API key and model name are provided
if not AWANLLM_API_KEY or not MODEL_NAME:
    raise ValueError("Please provide the API key and model name")

# Initialize the client
client = AwanLLMClient(AWANLLM_API_KEY)

# Initialize chat completions instance
chat = ChatCompletions(MODEL_NAME)

# Load menu data from JSON
with open("menu.json", "r") as f:
    menu_data = json.load(f)["data"]

# Generate menu text
menu_text = "\n".join(
    [f"{item['item']}: ${item['price']}" for item in menu_data if item["in_stock"]]
)


def payment():
    print("Payment API called")
    # extract the database items and quantity from the chat. items are formatted as below:
    # * 2 Burgers: $8.99 x 2 = $17.98
    # * 1 French Fries: $2.99
    # we want: 2 Burgers, 1 French Fries


# key phrase to confirm the order and end the conversation
key_phrase = "Confirm my order"

# Add a system message to the chat with the menu
chat.add_message(Role.SYSTEM, f"Here is the menu:\n{menu_text}")

# Loop to take user input and generate responses
while True:
    # Take user input
    user_input = input("User: ")

    # if the user input is empty or exit, break the loop
    if not user_input or user_input.lower() == "exit":
        break

    # if user input is "voice message", convert the voice to text
    if user_input.lower() == "voice message":
        user_input = speech_to_text()
        if user_input:
            print(f"User (voice): {user_input}")
        else:
            break

    # if the user input is the key phrase, end the conversation
    if key_phrase in user_input:
        payment()
        break

    # Add a user message to the chat
    chat.add_message(Role.USER, user_input)

    # Request a completion from the model
    chat_response = client.chat_completion(chat)

    # Extract the content portion from the response
    content = chat_response["choices"][0]["message"]["content"]

    # Print to console
    print(f"pAI: {content}")

    # Speak the response
    text_to_speech(content)
