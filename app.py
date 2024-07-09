import json
import os
import secrets

import awan_llm_api
import awan_llm_api.completions
import dotenv
import ffmpeg
import flask
import gtts


from backend_scripts import speech_to_text

app = flask.Flask(__name__)
app.secret_key = secrets.token_urlsafe()
app.static_folder = "static"
app.config["UPLOAD_FOLDER"] = "static/audio"

if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

# Load environment variables
dotenv.load_dotenv()

# Initialize recording process
recording_process = None

# Chat API key and model name
AWANLLM_API_KEY = os.getenv("AWANLLM_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")
if not AWANLLM_API_KEY or not MODEL_NAME:
    raise ValueError("Please provide the API key and model name")

# Initialize the client
client = awan_llm_api.AwanLLMClient(AWANLLM_API_KEY)
chat = awan_llm_api.completions.ChatCompletions(MODEL_NAME)

# Load menu data from JSON
with open("menu.json", "r") as f:
    menu_data = json.load(f)["data"]
menu_text = "\n".join(
    [f"{item['item']}: ${item['price']}" for item in menu_data if item["in_stock"]]
)

# Add a system message to the chat with the menu
chat.add_message(awan_llm_api.Role.SYSTEM, f"Here is the menu:\n{menu_text}")


# Template filter to format price when displayed as currency
@app.template_filter("format_currency")
def format_currency(value):
    return f"{value:.2f}"


# Route for the main page with category buttons
@app.route("/")
def index():
    return flask.render_template("index.html")


# Route to handle category requests
@app.route("/category/<category_name>")
def category_items(category_name):
    items_in_category = [
        item
        for item in menu_data
        if item["category"] == category_name and item["in_stock"]
    ]
    return flask.render_template(
        "category_items.html", category_name=category_name, items=items_in_category
    )


# Route to add item to the cart
@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    item_name = flask.request.form.get("item_name")
    item_price = flask.request.form.get("item_price")
    quantity_str = flask.request.form.get("quantity")

    if quantity_str and quantity_str.isdigit():
        quantity = int(quantity_str)
    else:
        return "Invalid quantity", 400

    # If the cart is not in the session, create it
    if "cart" not in flask.session:
        flask.session["cart"] = []

    # Check if the item is already in the cart
    item_found = False
    for item in flask.session["cart"]:
        if item["name"] == item_name:
            item["quantity"] += quantity
            item_found = True
            break

    # If the item is not in the cart, add it
    if not item_found:
        flask.session["cart"].append(
            {"name": item_name, "price": item_price, "quantity": quantity}
        )

    flask.session.modified = True
    return flask.redirect(flask.url_for("view_cart"))


# Route to remove item from the cart
@app.route("/remove_from_cart", methods=["POST"])
def remove_from_cart():
    item_name = flask.request.form.get("item_name")

    if "cart" in flask.session:
        flask.session["cart"] = [
            item for item in flask.session["cart"] if item["name"] != item_name
        ]
        flask.session.modified = True

    return flask.redirect(flask.url_for("view_cart"))


# Route to update item quantity in the cart
@app.route("/update_cart", methods=["POST"])
def update_cart():
    item_name = flask.request.form.get("item_name")
    new_quantity = flask.request.form.get("quantity")

    if new_quantity and new_quantity.isdigit():
        new_quantity = int(new_quantity)
    else:
        return "Invalid quantity", 400

    if "cart" in flask.session:
        for item in flask.session["cart"]:
            if item["name"] == item_name:
                item["quantity"] = new_quantity
                break

        flask.session.modified = True

    return flask.redirect(flask.url_for("view_cart"))


# Route to view the cart
@app.route("/cart")
def view_cart():
    cart = flask.session.get("cart", [])
    total = sum(float(item["price"]) * item["quantity"] for item in cart)
    return flask.render_template(
        "cart.html", cart=cart, total=total, hide_cart_button=True
    )


# Route to handle chat requests
@app.route("/chat", methods=["POST"])
def chat_api():
    if flask.request.is_json:
        data = flask.request.get_json()

        # Add user message to chat
        user_message = data["message"]

        chat.add_message(awan_llm_api.Role.USER, user_message)
        chat_response = client.chat_completion(chat)

        # Extract the content portion from the response
        content = chat_response["choices"][0]["message"]["content"]
        return flask.jsonify({"chat_response": content})
    else:  # Return error for non-JSON requests
        return "Invalid request", 400


@app.route("/record", methods=["POST"])
def record_audio():
    if "audio" not in flask.request.files:
        return flask.jsonify({"error": "No audio file received"}), 400

    audio_file = flask.request.files["audio"]

    try:
        audio_path_mp3 = os.path.join(app.config["UPLOAD_FOLDER"], "output.mp3")
        audio_path_wav = os.path.join(app.config["UPLOAD_FOLDER"], "output.wav")

        # Save the mp3 file
        audio_file.save(audio_path_mp3)

        # Convert the mp3 to wav
        ffmpeg.input(audio_path_mp3).output(audio_path_wav).run()

        # Process the audio file (convert to text)
        text = speech_to_text(audio_path_wav)

        # Clear out the old mp3 audio file
        if os.path.exists(audio_path_mp3):
            os.remove(audio_path_mp3)

        return flask.jsonify({"text": text}), 200

    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500


@app.route("/tts", methods=["POST"])
def stream_tts():
    data = flask.request.get_json()
    text = data["text"]

    # Generate speech
    tts = gtts.gTTS(text)
    audio_path = os.path.join(app.config["UPLOAD_FOLDER"], "output.mp3")
    tts.save(audio_path)

    return (
        flask.jsonify(
            {"audio_url": flask.url_for("serve_audio", filename="output.mp3")}
        ),
        200,
    )


# Serve static files
@app.route("/static/audio/<path:filename>")
def serve_audio(filename):
    return flask.send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/delete_audio", methods=["DELETE"])
def delete_audio():
    try:
        audio_path = os.path.join(app.config["UPLOAD_FOLDER"], "output.mp3")
        if os.path.exists(audio_path):
            os.remove(audio_path)
            return flask.jsonify({"message": "Audio file deleted"}), 200
        else:
            return flask.jsonify({"error": "Audio file not found"}), 404
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=8000, debug=True)
