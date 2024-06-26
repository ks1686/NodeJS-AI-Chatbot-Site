import os

from awan_llm_api import AwanLLMClient, Role
from awan_llm_api.completions import ChatCompletions
from pysondb import db
from dotenv import load_dotenv

from speech import speech_to_text, text_to_speech

# Load the environment variables
load_dotenv()

# API key and model name
AWANLLM_API_KEY = os.getenv("AWANLLM_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

# check if the API key and model name are provided
if not AWANLLM_API_KEY or not MODEL_NAME:
    raise ValueError("Please provide the API key, model name")

# Initialize the client
client = AwanLLMClient(AWANLLM_API_KEY)

# Initialize chat completions instance
chat = ChatCompletions(MODEL_NAME)

# Initialize the food menu
food_menu = db.getDb("menu.json")

# Get all items from the food menu
items = food_menu.getAll()

# Add all items to the chat in a readable format
menu_text = "\n".join(
    [f"{item['item']}: ${item['price']})" for item in items if item["in_stock"]]
)


def payment():
    print("Payment API called")
    # extract the database items and quantity from the chat. items are formatted as below:
    # * 2 Burgers: $8.99 x 2 = $17.98
    # * 1 French Fries: $2.99
    # we want: 2 Burgers, 1 French Fries


# key phrase to confirm the order and end the conversation
key_phrase = "Confirm my order"

# Add a system message to the chat
chat.add_message(
    Role.SYSTEM,
    "Here is the food menu, use it whenever someone asks"
    "what's on the menu or if they want to place an order:\n{menu_text}."
    "Users should format orders as follows: Burgers: 2, French Fries: 3. The number represents the "
    "quantity the person is ordering. When you're ready to confirm the order, say 'Confirm my order'.",
)

# Initialize the content variable
content = ""

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

    # print to console
    print(f"pAI: {content}")

    # Speak the response
    text_to_speech(content)
