import os
import qrcode

import dotenv
import flask
import web3
import base64

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

app = flask.Flask(__name__)

# Load environment variables
dotenv.load_dotenv()

# Load the depay public key from the depay_key.pem file
DEPAY_PUBLIC_KEY = open("depay_public_key.pem").read()
depay_key = serialization.load_pem_public_key(DEPAY_PUBLIC_KEY.encode("utf-8"))

# Load  private key from the private_key.pem file
PRIVATE_KEY = open("private_key.pem").read()
private_key_bytes = PRIVATE_KEY.encode("utf-8")
private_key = serialization.load_pem_private_key(private_key_bytes, password=None)

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

    return flask.render_template(
        "crypto_index.html",
        qr_img_path=qr_img_path,
        wallet_address=wallet_address,
    )


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


# Callback endpoint for the Depay payment gateway
@app.route("/depay_callback", methods=["POST"])
def depay_callback():
    # Respond with 200 OK status code as the callback is received
    response = flask.jsonify({"status": "success"})
    response.status_code = 200
    return response


if __name__ == "__main__":
    app.run(port=8000, debug=True)
