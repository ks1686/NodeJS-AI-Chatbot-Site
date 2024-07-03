import os
import qrcode

import dotenv
import flask
import web3

app = flask.Flask(__name__)

# Load environment variables
dotenv.load_dotenv()

# Initialize the Web3 provider
w3 = web3.Web3(web3.Web3.HTTPProvider(os.getenv("SEPOLIA_ETH_ENDPOINT")))
if not w3.is_connected():
    raise ConnectionError("Could not connect to the Ethereum network")

# Wallet address to monitor, else throw an error
wallet_address = os.getenv("SEPOLIA_WALLET_ADDRESS")
if not wallet_address:
    raise ValueError("SEPOLIA_WALLET_ADDRESS environment variable is required")


@app.route("/")
def index():
    img = qrcode.make(f"ethereum:{wallet_address}")
    type(img)
    qr_img_path = "static/qrcode.png"
    img.save(qr_img_path)

    return flask.render_template("crypto_index.html", qr_img_path=qr_img_path)


@app.route("/check_transaction", methods=["POST"])
def check_transaction():
    data = flask.request.get_json()
    tx_hash = data.get("tx_hash")
    tx = w3.eth.get_transaction(tx_hash)
    tx_value = tx.get("value") if tx else None
    tx_to = tx.get("to") if tx else None

    if (
        tx
        and tx_to is not None
        and wallet_address is not None
        and tx_to.lower() == wallet_address.lower()
        and tx_value is not None
        and tx_value == web3.Web3.to_wei(data.get("amount"), "ether")
    ):
        return flask.jsonify({"status": "success", "message": "Payment received!"})
    else:
        return flask.jsonify(
            {
                "status": "failure",
                "message": "Transaction not found or incorrect amount.",
            }
        )


@app.route("/webhook", methods=["POST"])
def webhook():
    data = flask.request.get_json()
    if "event" in data and data["event"] == "mined_transaction":
        tx_hash = data["hash"]
        tx = w3.eth.get_transaction(tx_hash)
        tx_value = tx.get("value") if tx else None

        if tx and tx.get("to") == wallet_address and tx_value is not None:
            amount_received = web3.Web3.from_wei(tx_value, "ether")
            # Here you can add logic to verify the amount and update your application state
            return flask.jsonify(
                {"status": "success", "message": "Transaction received!"}
            )
    return flask.jsonify({"status": "failure", "message": "Invalid data."}), 400


if __name__ == "__main__":
    app.run(debug=True)
