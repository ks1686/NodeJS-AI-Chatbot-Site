import json
import os
import subprocess
from secrets import token_urlsafe as generate_secret_key

import speech_recognition as sr
from awan_llm_api import AwanLLMClient, Role
from awan_llm_api.completions import ChatCompletions
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from gtts import gTTS

app = Flask(__name__)
app.secret_key = generate_secret_key()
app.static_folder = "static"

# Load environment variables
load_dotenv()

# Initialize recording process
recording_process = None

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


# Template filter to format price when displayed as currency
@app.template_filter("format_currency")
def format_currency(value):
    return f"{value:.2f}"


# Route for the main page with category buttons
@app.route("/")
def index():
    return render_template("index.html")


# Route to handle category requests
@app.route("/category/<category_name>")
def category_items(category_name):
    items_in_category = [
        item
        for item in menu_data
        if item["category"] == category_name and item["in_stock"]
    ]
    return render_template(
        "category_items.html", category_name=category_name, items=items_in_category
    )


# Route to add item to the cart
@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    item_name = request.form.get("item_name")
    item_price = request.form.get("item_price")
    quantity_str = request.form.get("quantity")

    if quantity_str and quantity_str.isdigit():
        quantity = int(quantity_str)
    else:
        return "Invalid quantity", 400

    # If the cart is not in the session, create it
    if "cart" not in session:
        session["cart"] = []

    # Check if the item is already in the cart
    item_found = False
    for item in session["cart"]:
        if item["name"] == item_name:
            item["quantity"] += quantity
            item_found = True
            break

    # If the item is not in the cart, add it
    if not item_found:
        session["cart"].append(
            {"name": item_name, "price": item_price, "quantity": quantity}
        )

    session.modified = True
    return redirect(url_for("view_cart"))


# Route to remove item from the cart
@app.route("/remove_from_cart", methods=["POST"])
def remove_from_cart():
    item_name = request.form.get("item_name")

    if "cart" in session:
        session["cart"] = [
            item for item in session["cart"] if item["name"] != item_name
        ]
        session.modified = True

    return redirect(url_for("view_cart"))


# Route to update item quantity in the cart
@app.route("/update_cart", methods=["POST"])
def update_cart():
    item_name = request.form.get("item_name")
    new_quantity = request.form.get("quantity")

    if new_quantity and new_quantity.isdigit():
        new_quantity = int(new_quantity)
    else:
        return "Invalid quantity", 400

    if "cart" in session:
        for item in session["cart"]:
            if item["name"] == item_name:
                item["quantity"] = new_quantity
                break

        session.modified = True

    return redirect(url_for("view_cart"))


# Route to view the cart
@app.route("/cart")
def view_cart():
    cart = session.get("cart", [])
    total = sum(float(item["price"]) * item["quantity"] for item in cart)
    return render_template("cart.html", cart=cart, total=total, hide_cart_button=True)


# Route to handle chat requests
@app.route("/chat", methods=["POST"])
def chat_api():
    if request.is_json:
        data = request.get_json()

        # Add user message to chat
        user_message = data["message"]

        chat.add_message(Role.USER, user_message)
        chat_response = client.chat_completion(chat)

        # Extract the content portion from the response
        content = chat_response["choices"][0]["message"]["content"]
        return jsonify({"chat_response": content})
    else:  # Return error for non-JSON requests
        return "Invalid request", 400


# Route to handle audio recording requests
@app.route("/record", methods=["POST"])
def record():
    action = request.form.get("action")

    print(f"Action: {action}")

    if action == "start":
        start_recording()
        return jsonify({"status": "Recording started"})
    elif action == "stop":
        stop_recording()
        text = speech_to_text()
        return jsonify({"status": "Recording stopped", "text": text})
    return jsonify({"status": "Invalid action"})


# Function to start recording audio using ffmpeg
def start_recording(output_file="output.wav"):
    global recording_process
    command = [
        "ffmpeg",
        "-f",
        "avfoundation",
        "-i",
        ":0",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "2",
        output_file,
    ]
    recording_process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )


# Function to stop recording audio
def stop_recording():
    global recording_process
    if recording_process:
        recording_process.terminate()
        recording_process = None


# Function to convert the recorded audio to text
def speech_to_text():
    audio_file = "output.wav"
    r = sr.Recognizer()

    with sr.AudioFile(audio_file) as source:
        audio_data = r.record(source)

    try:
        print("Converting audio to text...")
        return r.recognize_sphinx(audio_data)
    except sr.UnknownValueError:
        return "Could not understand the audio"
    except sr.RequestError as e:
        return f"Error: {e}"
    finally:
        os.remove(audio_file)


# Function to convert text to speech and play the audio
def text_to_speech(text):
    # Synthesize speech using gTTS and save to output.mp3
    tts = gTTS(text=text, lang="en")
    tts.save("output.mp3")

    # Play the audio file using ffplay
    with open(os.devnull, "w") as devnull:
        subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", "output.mp3"],
            stdout=devnull,
            stderr=subprocess.STDOUT,
        )

    # Remove the temporary audio file
    os.remove("output.mp3")


if __name__ == "__main__":
    app.run(debug=True)
