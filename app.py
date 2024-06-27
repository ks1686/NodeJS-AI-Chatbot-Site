import json
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed to use sessions; replace "your_secret_key" with a unique, secret value

# Load menu data from JSON
with open("menu.json", "r") as f:
    menu_data = json.load(f)


# Route for the main page with category buttons
@app.route("/")
def index():
    return render_template("index.html")


# Route to handle category requests
@app.route("/category/<category_name>")
def category_items(category_name):
    items_in_category = [
        item
        for item in menu_data["data"]
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
    quantity = int(request.form.get("quantity"))

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
        session["cart"].append({"name": item_name, "price": item_price, "quantity": quantity})

    session.modified = True
    return redirect(url_for("view_cart"))


# Route to remove item from the cart
@app.route("/remove_from_cart", methods=["POST"])
def remove_from_cart():
    item_name = request.form.get("item_name")

    if "cart" in session:
        session["cart"] = [item for item in session["cart"] if item["name"] != item_name]
        session.modified = True

    return redirect(url_for("view_cart"))


# Route to update item quantity in the cart
@app.route("/update_cart", methods=["POST"])
def update_cart():
    item_name = request.form.get("item_name")
    new_quantity = int(request.form.get("quantity"))

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
    quantity = sum(item["quantity"] for item in cart)
    return render_template("cart.html", cart=cart, total=total, hide_cart_button=True)


if __name__ == "__main__":
    app.run(debug=True)
