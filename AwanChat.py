from operator import is_
from awan_llm_api import AwanLLMClient, Role
from awan_llm_api.completions import Completions, ChatCompletions
from pysondb import db
import os
import subprocess
import pvorca
from pydub import AudioSegment
from pydub.playback import play

# API key and model name
AWANLLM_API_KEY = "29d1a42a-37ad-49f2-bdc5-6309fdd89b4a"
MODEL_NAME = "Meta-Llama-3-8B-Instruct"
ORCA_ACCESS_KEY = "3Jbal8cmmrqZUcuOTmFcocMybuh9VfZKnNST7jZZSjYKt31zw1Wzkg=="

# Initialize the client
client = AwanLLMClient(AWANLLM_API_KEY)

# Initialize chat completions instance
chat = ChatCompletions(MODEL_NAME)

# Initialize the Orca client
orca = pvorca.create(access_key=ORCA_ACCESS_KEY)

# Initialize the food menu
food_menu = db.getDb("menu.json")

# Get all items from the food menu
items = food_menu.getAll()

# Add all items to the chat in a readable format
menu_text = "\n".join(
    [f"{item['item']}: ${item['price']})" for item in items if item["in_stock"]]
)


def speak(text):
    # Remove any invalid characters (e.g., *)
    text = text.replace("*", "").replace("$", "USD: ")

    # Synthesize speech using Orca and save to output.wav
    alignments = orca.synthesize_to_file(text, "output.wav")

    # Play the audio file using ffplay
    with open(os.devnull, "w") as devnull:
        subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", "output.wav"],
            stdout=devnull,
            stderr=subprocess.STDOUT,
        )

    # Remove the temporary audio file
    os.remove("output.wav")


chat.add_message(Role.SYSTEM, f"Here is the food menu:\n{menu_text}")

# Loop to take user input and generate responses
while True:
    # Take user input
    user_input = input("User: ")

    # Add a user message to the chat
    chat.add_message(Role.USER, user_input)

    # Request a completion from the model
    chat_response = client.chat_completion(chat)

    # Extract the content portion from the response
    content = chat_response["choices"][0]["message"]["content"]

    # print to console
    print(f"pAI: {content}")

    # Speak the response
    speak(content)
